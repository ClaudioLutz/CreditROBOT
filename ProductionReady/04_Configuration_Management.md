# Technical Guide: Configuration Management

Hardcoding configuration values (like secret keys, database URIs, API keys) directly into application code is insecure and inflexible. For production, application configuration should be externalized from the Docker image. Environment variables are a widely adopted method for this, aligning with Twelve-Factor App principles.

This guide details how to manage configuration for the CreditRobot application using environment variables.

## 1. Identify Configuration to Externalize

Review `app.py` and other relevant files to identify configuration values that should be managed externally. Common candidates include:

*   **`SECRET_KEY`**: Flask's secret key for session management and other security features.
*   **`SQLALCHEMY_DATABASE_URI`**: The database connection string (especially if moving away from a hardcoded SQLite path or to an external database).
*   **`DEBUG` mode**: Flask's debug mode should be off in production.
*   **`FLASK_ENV`**: Set to `production`.
*   **Gunicorn settings**: Log level, worker count (though some might be in `gunicorn.conf.py`, sensitive parts or overrides can be env vars).
*   Any external API keys or service credentials.

For this project, the primary ones are `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, and `FLASK_ENV`.

## 2. Modify `app.py` to Use Environment Variables

Update `app.py` to read these configuration values from environment variables using `os.environ.get()`. Provide sensible defaults for development if an environment variable isn't set.

```python
# app.py
import os
from flask import Flask
# ... other imports for SQLAlchemy, Migrate etc. ...

# Determine the absolute path for the instance folder
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

app = Flask(__name__, instance_path=instance_path) # Or instance_relative_config=True

# --- Configuration ---
# Secret Key
# Generate a strong random key for production (e.g., using `openssl rand -hex 32`)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-secure-default-secret-key-for-dev-only')

# Database URI
# Default to local SQLite for development if DATABASE_URL is not set
default_db_uri = f"sqlite:///{os.path.join(instance_path, 'creditrobot.db')}"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_db_uri)

# Other SQLAlchemy settings (can also be from env vars if needed)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask Environment (controls debug mode etc.)
# FLASK_ENV is typically set outside the app, but FLASK_DEBUG can be derived.
# app.config['DEBUG'] = os.environ.get('FLASK_ENV') == 'development'
# Note: Gunicorn and Docker CMD will typically set FLASK_ENV=production

# Initialize extensions (db, migrate, etc.)
# from models import db # Assuming models.py defines db
# from flask_migrate import Migrate
# db.init_app(app)
# migrate = Migrate(app, db)
# Ensure your db and migrate objects are initialized after app.config is set.
# If db is defined in models.py, ensure app is passed to it or models.py imports the configured app.

# --- Example: Initializing DB (ensure this is compatible with your models.py structure) ---
# This is a common pattern if 'db' is defined in models.py
# from models import db, Conversation # Import db and any models
# db.init_app(app)

# with app.app_context():
#     db.create_all() # This might be handled by migrations in a real setup

# --- Blueprints and Routes ---
# ... your routes and blueprints ...

# Example route:
@app.route('/')
def hello():
    return "Hello, CreditRobot!"

# Remove or guard the app.run() call for production
# if __name__ == '__main__':
#    # This is for development only. Gunicorn is used in production.
#    app.run(host='0.0.0.0', port=5000, debug=(os.environ.get('FLASK_ENV') == 'development'))

```

**Important Considerations for `app.py`:**
*   **`SECRET_KEY`**: For production, generate a strong, unique secret key. Do **not** use the default provided in the code.
*   **`DATABASE_URL`**: If you use the default SQLite, it still works. If you switch to PostgreSQL/MySQL (as per Guide `03`), you'll set `DATABASE_URL` to something like `postgresql://user:password@host:port/dbname`.
*   **Initialization Order**: Ensure that `app.config` is fully populated *before* initializing Flask extensions like SQLAlchemy, as they might read from the configuration upon initialization. If your `db` object is defined in `models.py`, you might need to adjust how `db.init_app(app)` is called or ensure `models.py` imports the fully configured `app` instance.
*   **`FLASK_ENV` and `DEBUG`**: `FLASK_ENV=production` (set when running the container) typically disables debug mode. Gunicorn also has its own debug flags which are separate.

## 3. Setting Environment Variables in Docker

There are several ways to provide environment variables to your Docker container:

### 3.1. Using `docker run -e` or `--env`

When running the container directly:
```bash
docker run -d -p 5000:5000        -e SECRET_KEY='your_super_secret_production_key'        -e DATABASE_URL='sqlite:////app/instance/creditrobot.db' \ # Path inside container
       -e FLASK_ENV='production'        -e GUNICORN_LOG_LEVEL='info'        --name creditrobot_app        -v creditrobot_db_data:/app/instance \ # From Guide 03
       creditrobot-app
```
*   **`FLASK_ENV='production'`**: This tells Flask to run in production mode (e.g., disables the interactive debugger).
*   **`GUNICORN_LOG_LEVEL`**: As seen in `gunicorn.conf.py` to control Gunicorn's log verbosity.

### 3.2. Using an Environment File (`--env-file`)

You can list your environment variables in a file (e.g., `production.env`) and pass it to Docker:

`production.env`:
```
SECRET_KEY='your_super_secret_production_key'
DATABASE_URL='sqlite:////app/instance/creditrobot.db'
FLASK_ENV='production'
GUNICORN_LOG_LEVEL='info'
# Add other variables as needed
```
**Important:** Add `*.env` to your `.gitignore` file to prevent committing secret files to version control.

Run the container:
```bash
docker run -d -p 5000:5000        --env-file ./production.env        --name creditrobot_app        -v creditrobot_db_data:/app/instance        creditrobot-app
```

### 3.3. Using Docker Compose

Docker Compose provides a clean way to manage environment variables:

`docker-compose.yml`:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      # Option 1: Define directly
      SECRET_KEY: 'your_super_secret_production_key_here_or_use_env_file'
      DATABASE_URL: 'sqlite:////app/instance/creditrobot.db' # Path inside container
      FLASK_ENV: 'production'
      GUNICORN_LOG_LEVEL: 'info'
      # Option 2: Reference an .env file (recommended for secrets)
      # env_file:
      #   - ./production.env # Docker Compose will look for this file
    volumes:
      - creditrobot_db_data:/app/instance

volumes:
  creditrobot_db_data:
```
If `env_file` is used, Docker Compose automatically reads variables from it. You can also leverage variable substitution in Docker Compose to pull values from the shell environment where `docker-compose` is run, which is useful for CI/CD systems.

## 4. `.env` Files for Local Development

For local development convenience (outside Docker, or even with Docker Compose overrides), developers often use `.env` files in the project root to store development-specific environment variables. Libraries like `python-dotenv` can load these automatically when the Flask app starts in a local (non-Docker) dev environment.

1.  Add to `requirements.txt` (for local dev, not strictly needed in Docker if env vars are passed directly): `python-dotenv`
2.  Create a `.env` file (and add it to `.gitignore`!):
    ```
    # .env (for local development)
    FLASK_APP=app.py
    FLASK_ENV=development
    SECRET_KEY='a_dev_secret_key_not_for_production'
    DATABASE_URL='sqlite:///instance/creditrobot.db' # Local path
    ```
3.  Load it at the top of your `app.py` (or more commonly, in a wrapper script that runs the dev server):
    ```python
    # app.py (at the very top, or in your local run script)
    from dotenv import load_dotenv
    load_dotenv() # Loads variables from .env into os.environ

    import os
    # ... rest of your app.py
    ```
    When using Docker, the environment variables are injected directly by Docker (as configured in `docker run` or `docker-compose.yml`), so `python-dotenv` is less critical within the container itself, but it doesn't hurt.

## 5. Verifying Configuration

After setting up environment variables and running your container:
*   Check application logs for any errors related to configuration.
*   You can `docker exec -it <container_name> env` to see the environment variables set inside the running container.
*   Test application functionality that depends on these configurations (e.g., can it connect to the database? are sessions working?).

By externalizing configuration, you make your CreditRobot application more secure, flexible, and easier to manage across different environments (development, staging, production) without changing code.
