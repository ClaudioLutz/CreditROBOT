# Technical Guide: Logging in Production

Effective logging is crucial for monitoring application health, diagnosing issues, and understanding application behavior in a production environment. When running applications in Docker, the standard practice is to configure applications to log to `stdout` (standard output) and `stderr` (standard error). Docker's logging drivers can then collect these streams and forward them to various destinations.

This guide covers configuring logging for the Flask application and Gunicorn server.

## 1. Logging Principles for Dockerized Applications

*   **Log to `stdout`/`stderr`**: Your application should not write logs to files inside the container. Instead, direct all log output to standard output or standard error.
*   **Let Docker Handle Log Files**: Docker captures these streams and can manage log rotation and drivers.
*   **Structured Logging**: Consider using structured log formats (like JSON) for easier parsing, searching, and analysis by log management systems.
*   **Configurable Log Levels**: Allow log verbosity to be controlled at runtime (e.g., via environment variables).

## 2. Configuring Gunicorn Logging

Gunicorn controls the logging for the web server itself, including access logs and its own error logs.

### 2.1. Gunicorn Configuration (`gunicorn.conf.py`)

In Guide `02_Production_Web_Server.md`, we set up `gunicorn.conf.py`. Ensure these logging-related settings are present:

```python
# gunicorn.conf.py
import os

# ... other settings ...

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
# Default to 'info', configurable via GUNICORN_LOG_LEVEL env var in docker-compose.yml or docker run
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")

# Example of a more detailed access log format (optional)
# access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
# For JSON structured access logs with Gunicorn (requires custom formatter or additional tools):
# You might need to implement a custom logger class for Gunicorn or use a library
# that can intercept and format Gunicorn's access logs if you need them in JSON directly from Gunicorn.
# Alternatively, process plain text logs downstream.
```

*   **`accesslog = "-"`**: Sends access logs to `stdout`.
*   **`errorlog = "-"`**: Sends Gunicorn's error logs (e.g., worker timeouts, boot errors) to `stderr`.
*   **`loglevel`**: Controls the verbosity of Gunicorn's error log. Setting this via `os.environ.get("GUNICORN_LOG_LEVEL", "info")` allows you to change it at runtime without modifying the config file.

### 2.2. Access Log Format
Gunicorn's default access log format is quite informative. If you need custom fields, you can use `access_log_format`. For JSON access logs from Gunicorn, it's more complex and might involve custom log formatters or processing downstream.

## 3. Configuring Flask Application Logging

Flask uses Python's standard `logging` module. By default, Flask logs to `stderr`.

### 3.1. Basic Flask Logging Configuration

You can configure Flask's logger in `app.py`.

```python
# app.py
import logging
import os
from flask import Flask

# ... (other imports and Flask app setup) ...
app = Flask(__name__)

# --- Logging Configuration ---
if __name__ != '__main__': # Only configure this when run by a WSGI server like Gunicorn
    # Get Gunicorn's logger instance
    gunicorn_logger = logging.getLogger('gunicorn.error')

    # Use Gunicorn's handlers and log level for the Flask app logger
    # This integrates Flask app logs with Gunicorn's error log stream
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    # You can also set a specific level for Flask if needed, e.g.:
    # app.logger.setLevel(os.environ.get("FLASK_LOG_LEVEL", "INFO").upper())

# Example: Adding a custom log message
app.logger.info("CreditRobot application has started.")

# Example route with logging
@app.route('/')
def index():
    app.logger.info('Index page accessed.')
    return "Welcome to CreditRobot!"

@app.route('/error_example')
def error_example():
    try:
        1 / 0
    except ZeroDivisionError:
        app.logger.error("A ZeroDivisionError occurred!", exc_info=True)
        # exc_info=True includes the stack trace in the log
    return "An error was logged.", 500

# ... (rest of your app.py) ...
```

**Explanation:**

*   **`if __name__ != '__main__':`**: This condition ensures that this logging setup is applied when Gunicorn (or another WSGI server) runs the app. When you run `python app.py` directly for local development, Flask's default development server logging is used.
*   **`gunicorn_logger = logging.getLogger('gunicorn.error')`**: Gets the logger instance that Gunicorn uses for its error stream.
*   **`app.logger.handlers = gunicorn_logger.handlers`**: Makes the Flask application logger use the same handlers (output destinations) as Gunicorn's error logger. This means Flask logs will go to `stderr` along with Gunicorn's logs.
*   **`app.logger.setLevel(gunicorn_logger.level)`**: Sets the Flask app's log level to match Gunicorn's. This way, `GUNICORN_LOG_LEVEL` controls both.
*   **`app.logger.info(...)`, `app.logger.error(...)`**: Examples of how to use the Flask logger.

### 3.2. Structured Logging with `python-json-logger` (Recommended)

Structured logs (e.g., in JSON format) are much easier for log management systems to parse and query. The `python-json-logger` library is a popular choice.

1.  **Add to `requirements.txt`**:
    ```
    python-json-logger>=2.0
    ```
    Then `pip install -r requirements.txt` or let Docker rebuild.

2.  **Configure JSON logging in `app.py`**:

    ```python
    # app.py
    import logging
    import os
    from flask import Flask
    from pythonjsonlogger import jsonlogger

    app = Flask(__name__)

    # --- Structured Logging Configuration ---
    # Only configure this when run by a WSGI server like Gunicorn
    if __name__ != '__main__':
        logger = logging.getLogger() # Get root logger, or app.logger
        logHandler = logging.StreamHandler() # Default to stderr

        # Custom formatter for JSON logs
        class CustomJsonFormatter(jsonlogger.JsonFormatter):
            def add_fields(self, log_record, record, message_dict):
                super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
                if not log_record.get('timestamp'):
                    # Add timestamp in ISO format
                    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    log_record['timestamp'] = now
                if log_record.get('level'):
                    log_record['level'] = log_record['level'].upper()
                else:
                    log_record['level'] = record.levelname

                # Add logger name if not present
                if not log_record.get('logger'):
                    log_record['logger'] = record.name


        formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(logger)s %(module)s %(funcName)s %(lineno)d %(message)s')

        logHandler.setFormatter(formatter)

        # Configure app.logger (Flask's default logger)
        app.logger.handlers.clear() # Clear existing handlers
        app.logger.addHandler(logHandler)
        app.logger.setLevel(os.environ.get("FLASK_LOG_LEVEL", "INFO").upper())
        app.logger.propagate = False # Prevent duplication if root logger is also configured

        # Optionally, configure the root logger if other libraries also log
        # logging.basicConfig(handlers=[logHandler], level=os.environ.get("FLASK_LOG_LEVEL", "INFO").upper())

        # Integrate with Gunicorn's error logger stream (optional, but good for consistency)
        # gunicorn_error_logger = logging.getLogger('gunicorn.error')
        # gunicorn_error_logger.handlers.clear()
        # gunicorn_error_logger.addHandler(logHandler)
        # gunicorn_error_logger.setLevel(os.environ.get("GUNICORN_LOG_LEVEL", "INFO").upper())

        app.logger.info("CreditRobot application (JSON logging) has started.")


    # Example route with logging
    @app.route('/')
    def index():
        app.logger.info('Index page accessed.', extra={'props': {'path': '/'}})
        return "Welcome to CreditRobot!"

    @app.route('/error_example')
    def error_example():
        try:
            1 / 0
        except ZeroDivisionError:
            app.logger.error("A ZeroDivisionError occurred!", exc_info=True, extra={'props': {'error_type': 'ZeroDivision'}})
        return "An error was logged (JSON).", 500

    # Need datetime for the custom formatter
    from datetime import datetime

    # ... (rest of your app.py) ...
    ```

**Explanation of JSON logging setup:**
*   `CustomJsonFormatter`: Allows adding custom fields or modifying existing ones. Here, we ensure a consistent `timestamp` and `level`.
*   The formatter is applied to a `StreamHandler`.
*   `app.logger.handlers.clear()`: Clears any default handlers Flask might have set up.
*   `app.logger.addHandler(logHandler)`: Adds the JSON log handler.
*   `app.logger.propagate = False`: Prevents log messages from being passed up to the root logger if you also configure it, avoiding duplicate log entries.
*   Logging with `extra`: `app.logger.info('Message', extra={'props': {'custom_field': 'value'}})` allows adding arbitrary key-value pairs to your JSON logs.

## 4. Viewing Logs with Docker

Once your application and Gunicorn are logging to `stdout`/`stderr`, you can view logs using:

*   **`docker logs <container_name_or_id>`**: Shows logs for a specific container.
    ```bash
    docker logs creditrobot_app_web_1 # If using docker-compose, name might be like this
    docker logs <container_id_from_docker_ps>
    ```
*   **`docker-compose logs <service_name>`**: Shows logs for a service defined in `docker-compose.yml`.
    ```bash
    docker-compose logs web # Shows logs from the 'web' service
    docker-compose logs -f web # Follow log output
    ```

## 5. Log Management in Production

For a production system, you'll typically forward Docker logs to a centralized log management system like:
*   ELK Stack (Elasticsearch, Logstash, Kibana)
*   Grafana Loki
*   Splunk
*   Datadog
*   AWS CloudWatch Logs
*   Google Cloud Logging

Docker supports various [logging drivers](https://docs.docker.com/config/containers/logging/configure/) that can send logs to these systems. You configure the logging driver in the Docker daemon configuration or sometimes per container/service in `docker-compose.yml`.

Example (conceptual) in `docker-compose.yml` for AWS CloudWatch:
```yaml
services:
  web:
    # ...
    logging:
      driver: "awslogs"
      options:
        awslogs-group: "/docker/creditrobot-app"
        awslogs-region: "your-aws-region"
        awslogs-stream-prefix: "web"
```

## Conclusion

By configuring Gunicorn and Flask to log to `stdout`/`stderr`, optionally using a structured JSON format, you enable Docker to effectively manage your application's logs. This setup is crucial for monitoring, debugging, and integrating with centralized logging systems in production. Remember to set appropriate log levels for different environments to balance visibility with log volume.
