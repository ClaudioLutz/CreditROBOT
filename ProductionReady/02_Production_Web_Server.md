# Technical Guide: Using a Production-Grade Web Server (Gunicorn)

The Flask development server (`app.run()`) is not suitable for production environments due to its single-threaded nature and lack of robustness. A production-grade WSGI (Web Server Gateway Interface) server like Gunicorn is essential for handling concurrent requests, managing worker processes, and providing better performance and stability.

This guide details how to integrate and configure Gunicorn for the CreditRobot application.

## 1. Add Gunicorn to `requirements.txt`

First, ensure Gunicorn is listed as a project dependency. If it's not already there, add `gunicorn` to your `requirements.txt` file. You can specify a version if needed, e.g., `gunicorn>=20.0`.

Example `requirements.txt` addition:
```
Flask>=2.0
Flask-SQLAlchemy>=2.5
Flask-Migrate>=3.0
# ... other dependencies ...
gunicorn>=21.2.0
```
After adding it, if you're working locally, you'd update your virtual environment: `pip install -r requirements.txt`. When building the Docker image, this will be handled by the `pip install -r requirements.txt` command in the `Dockerfile`.

## 2. Create Gunicorn Configuration File (`gunicorn.conf.py`)

Gunicorn can be configured via command-line arguments or a configuration file. A configuration file is generally cleaner and more manageable for multiple settings. The `Dockerfile` we created in Guide `01_Dockerfile.md` already specifies using a config file: `CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]`.

Create a file named `gunicorn.conf.py` in the root of your project. Here's a sample configuration tailored for a typical Flask application:

```python
# gunicorn.conf.py

import multiprocessing
import os

# Host and Port
# Bind to 0.0.0.0 to be accessible from outside the Docker container.
# The port should match the EXPOSE instruction in your Dockerfile.
bind = "0.0.0.0:5000"

# Worker Processes
# Gunicorn recommends (2 * number of CPU cores) + 1 as a starting point.
# Docker containers might have CPU limits, so adjust accordingly.
# For a system with os.cpu_count() available:
try:
    workers = (multiprocessing.cpu_count() * 2) + 1
except NotImplementedError:
    workers = 3 # Default if cpu_count is not available

# For environments where os.environ provides CPU_LIMIT (e.g. some PaaS):
# workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))


# Worker Class
# 'sync' is the default. For I/O bound applications, 'gevent' or 'eventlet'
# can provide better concurrency with async workers. This requires installing
# gevent or eventlet separately (add to requirements.txt).
# For simplicity, we'll start with 'sync'.
worker_class = "sync"
# To use gevent:
# worker_class = "gevent"
# threads = 2 # Number of threads per worker when using gevent

# Worker Connections
# The maximum number of simultaneous clients. Only affects async workers.
# worker_connections = 1000

# Timeout
# Workers silent for more than this many seconds are killed and restarted.
# Value is a positive number greater than zero. The default is 30.
timeout = 120

# Keep Alive
# The number of seconds to wait for requests on a Keep-Alive connection.
# Generally set in the 1-5 seconds range. Default is 2.
keepalive = 5

# Logging
# Access log format.
# For more detailed logging options, refer to Gunicorn documentation.
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info") # Default to 'info', configurable via env var
# Example of a more detailed access log format:
# access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process Naming (useful for process monitoring)
# proc_name = 'creditrobot-gunicorn'

# Server Mechanics
# Daemonize the Gunicorn process (not recommended when running in Docker, let Docker manage the process)
# daemon = False

# Preload Application
# Load application code before the worker processes are forked.
# This can save some RAM resources as well as speed up server boot times.
# However, it can have some drawbacks if your application has specific needs
# around per-worker initialization or resource handling.
preload_app = True

# SSL (Typically handled by a reverse proxy like Nginx in production)
# keyfile = None
# certfile = None
# ssl_version = ...

# Ensure this file is copied into your Docker image if it's not in the root
# or adjust paths in the Dockerfile CMD accordingly.
# If gunicorn.conf.py is in the root, `COPY . .` in Dockerfile handles it.
```

**Key Configuration Options Explained:**

*   **`bind`**: The address and port Gunicorn listens on. `0.0.0.0` makes it listen on all available network interfaces within the container, which is necessary for Docker port mapping to work. `5000` matches the `EXPOSE` in the `Dockerfile`.
*   **`workers`**: The number of worker processes. The formula `(2 * CPU cores) + 1` is a common starting point. `multiprocessing.cpu_count()` attempts to determine this. In a containerized environment, CPU limits might apply, so this might need adjustment or be set via an environment variable.
*   **`worker_class`**: The type of worker. `sync` workers are simple and handle one request at a time. For applications with many I/O-bound operations (like waiting for database queries or external API calls), asynchronous workers like `gevent` or `eventlet` (which require installing their respective libraries) can offer much better throughput.
*   **`timeout`**: If a worker is silent for this many seconds, it's killed and restarted. This helps deal with stuck workers.
*   **`keepalive`**: How long to wait for requests on a keep-alive connection.
*   **`accesslog`, `errorlog`**: Set to `"-"` to send logs to `stdout` and `stderr`, respectively. This is standard practice for Dockerized applications, allowing Docker's logging drivers to pick them up.
*   **`loglevel`**: The granularity of logs. Can be set from an environment variable `GUNICORN_LOG_LEVEL`.
*   **`preload_app = True`**: Loads the application code once in the master process before forking worker processes. This can save memory but might have implications if your app performs initialization that needs to be per-worker (e.g., database connections if not managed carefully).

## 3. Update `Dockerfile` (If Necessary)

The `Dockerfile` created in Guide `01_Dockerfile.md` already includes the `CMD` to use `gunicorn.conf.py`:
```dockerfile
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```
Ensure that:
1.  `gunicorn.conf.py` is in the root directory of your project so that `COPY . .` in the `Dockerfile` copies it to `/app/gunicorn.conf.py`.
2.  `gunicorn` is added to `requirements.txt`.

## 4. Remove Flask Development Server Calls (Important for Production)

Your `app.py` might contain a block like this for development:
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```
While this block doesn't hurt if Gunicorn is used to start the app (as Gunicorn imports the `app` object directly and doesn't execute `app.py` as the main script), it's good practice to ensure that the development server is not accidentally run in a production-like setting. Gunicorn will be the entry point in production.

You can leave it for local development convenience, but be sure your production startup script/command (like the `CMD` in Dockerfile) *only* uses Gunicorn.

## 5. Building and Running with Gunicorn

1.  **Rebuild the Docker image** (if you changed `requirements.txt` or `gunicorn.conf.py`):
    ```bash
    docker build -t creditrobot-app .
    ```
2.  **Run the container**:
    ```bash
    docker run -p 5000:5000            -e GUNICORN_LOG_LEVEL="debug" \ # Example: override log level
           creditrobot-app
    ```
    You should see Gunicorn startup logs in your terminal.

## 6. Considerations for Asynchronous Workers (e.g., `gevent`)

If your application is I/O-bound and you want to use `gevent` for better concurrency:
1.  Add `gevent` to `requirements.txt`.
2.  Change `worker_class = "sync"` to `worker_class = "gevent"` in `gunicorn.conf.py`.
3.  You might also want to set `threads` in `gunicorn.conf.py` (e.g., `threads = 2` or `threads = 4`). The optimal number of threads per gevent worker depends on the nature of your application's I/O.

Using `gevent` requires that your application and its dependencies are gevent-friendly (i.e., they use non-blocking I/O or are properly patched by gevent). Standard libraries like Flask and SQLAlchemy generally work well with gevent.

By following this guide, you've replaced the Flask development server with Gunicorn, a robust WSGI server ready for production workloads, configured to run efficiently within your Docker container.
