# Technical Guide: Database Management for Production (MS SQL Server)

This guide details how to integrate Microsoft SQL Server (MS SQL Server) as the database backend for the CreditRobot application in a Dockerized production environment. It covers running MS SQL Server in Docker, configuring the Flask application, using Docker Compose, ensuring data persistence, and handling database migrations with Alembic.

While Guide `03_Database_Management.md` covered SQLite and general concepts for PostgreSQL/MySQL, this guide specifically focuses on MS SQL Server.

## 1. Running MS SQL Server in Docker

Microsoft provides official Docker images for SQL Server on Linux. These images allow you to run a SQL Server instance within a Docker container.

### 1.1. Choosing an Image
The official images are available on Docker Hub (e.g., `mcr.microsoft.com/mssql/server`). You can choose a specific version tag (e.g., `2022-latest`, `2019-latest`).

### 1.2. Key Environment Variables for SQL Server Container
When running the SQL Server container, you **must** set these environment variables:
*   `ACCEPT_EULA=Y`: Required to accept the End-User Licensing Agreement.
*   `MSSQL_SA_PASSWORD` (or `SA_PASSWORD` for older images): Sets the password for the System Administrator (`sa`) login. Choose a strong password.
*   `MSSQL_PID`: (Optional) Specifies the edition of SQL Server (e.g., `Developer`, `Express`, `Standard`, `Enterprise`). `Developer` edition is free for development and testing. `Express` is free for production with limitations.

## 2. Flask Application Configuration for MS SQL Server

### 2.1. Install Python Driver: `pyodbc`
The most common Python driver for connecting to MS SQL Server is `pyodbc`. You'll also need Microsoft's ODBC drivers for SQL Server installed in your application's Docker image.

1.  **Add to `requirements.txt`**:
    ```
    pyodbc>=4.0.30
    ```

2.  **Install ODBC Drivers in `Dockerfile`**:
    The `python:3.12-slim-bookworm` base image (Debian) requires installing Microsoft's ODBC drivers. This adds complexity to the `Dockerfile`.

    Modify your application's `Dockerfile`:
    ```dockerfile
    # Stage 1: Base Image Setup
    FROM python:3.12-slim-bookworm AS base
    # ... (ENV vars, WORKDIR) ...

    # Install Microsoft ODBC Driver for SQL Server
    # Instructions from https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server
    # This sequence is for Debian. Adjust if using a different base Linux distribution.
    RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        apt-transport-https && \
        curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
        curl https://packages.microsoft.com/config/debian/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
        apt-get update && \
        ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18 unixodbc-dev && \
        # Optional: remove tools to save space if only driver is needed for app image
        # apt-get remove -y mssql-tools18 && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*
    # ... (rest of your Dockerfile: non-root user setup, etc.) ...

    # Stage 2: Build Stage (for Python dependencies)
    FROM base AS builder
    COPY requirements.txt .
    RUN pip install --no-cache-dir --upgrade pip && \
        pip install --no-cache-dir -r requirements.txt
    # ... (rest of builder stage) ...

    # Stage 3: Application Stage
    # ... (as before, ensuring non-root user is used) ...
    ```
    **Note:** Installing ODBC drivers significantly increases the image size and build time. Ensure these steps are correct for your chosen base image and ODBC driver version. The `msodbcsql18` package is common for newer SQL Server versions.

### 2.2. SQLAlchemy Connection String
SQLAlchemy uses a connection string (DSN) to connect to the database. For MS SQL Server with `pyodbc`, it looks like:
`mssql+pyodbc://<username>:<password>@<host>:<port>/<database_name>?driver=<driver_name>`

*   `<username>`: e.g., `sa`
*   `<password>`: The password you set for the `sa` user (or other user).
*   `<host>`: The hostname of the SQL Server container (e.g., `db` in Docker Compose).
*   `<port>`: The port SQL Server is listening on (default is `1433`).
*   `<database_name>`: The name of your database.
*   `<driver_name>`: The name of the ODBC driver. It's often something like `ODBC Driver 18 for SQL Server`. This needs to match the installed driver.

### 2.3. Update `app.py` for Configuration
Modify `app.py` to use environment variables for the database connection:

```python
# app.py
import os
# ...

# Default to local SQLite for dev if DATABASE_URL is not set
default_db_uri = f"sqlite:///{os.path.join(app.instance_path, 'creditrobot.db')}"

# For MS SQL Server, DATABASE_URL would be set in the environment:
# Example: MSSQL_DRIVER='ODBC Driver 18 for SQL Server' (can also be part of DATABASE_URL)
#          MSSQL_SERVER='db,1433' # Host and port
#          MSSQL_DATABASE='CreditRobotDB'
#          MSSQL_USER='sa'
#          MSSQL_PASSWORD='YourStrongPassword!'
# Constructing from parts:
db_driver = os.environ.get('MSSQL_DRIVER', 'ODBC Driver 18 for SQL Server')
db_server = os.environ.get('MSSQL_SERVER', 'localhost,1433') # For local dev outside Docker
db_name = os.environ.get('MSSQL_DATABASE', 'CreditRobotDB_dev')
db_user = os.environ.get('MSSQL_USER', 'sa_dev')
db_password = os.environ.get('MSSQL_PASSWORD', 'dev_password')

# Prioritize DATABASE_URL if set directly, otherwise construct from parts
database_url = os.environ.get('DATABASE_URL')
if not database_url and os.environ.get('USE_MSSQL'): # Add a flag to switch to MSSQL
    # Ensure the password is URL-encoded if it contains special characters
    from urllib.parse import quote_plus
    db_password_encoded = quote_plus(db_password)
    database_url = f"mssql+pyodbc://{db_user}:{db_password_encoded}@{db_server}/{db_name}?driver={db_driver.replace(' ', '+')}"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url if database_url else default_db_uri
# ...
```
Using `os.environ.get('USE_MSSQL')` allows you to switch between SQLite and MS SQL Server configurations easily. The driver name often has spaces, so replace them with `+` for the URL.

## 3. Docker Compose for App and MS SQL Server

`docker-compose.yml` simplifies managing the application and SQL Server containers.

```yaml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile # Your application's Dockerfile
    image: creditrobot-app-mssql
    ports:
      - "5000:5000" # If not using Nginx in front
      # expose:
      #   - "5000" # If using Nginx
    environment:
      - FLASK_APP=app.py
      - FLASK_ENV=production
      - USE_MSSQL=true # Flag to use MS SQL configuration in app.py
      - DATABASE_URL= # Optional: Or set specific MSSQL_ parts:
      - MSSQL_DRIVER=ODBC Driver 18 for SQL Server
      - MSSQL_SERVER=db,1433 # 'db' is the service name of SQL Server, 1433 is the port
      - MSSQL_DATABASE=CreditRobotDB
      - MSSQL_USER=sa
      - MSSQL_PASSWORD=YourStrongPassword!123 # Use a strong password, manage via secrets
      - SECRET_KEY=your_flask_secret_key
      # GUNICORN_LOG_LEVEL, etc.
    volumes:
      # - static_volume:/app/static # If serving static files
      # - ./instance:/app/instance # If you had other instance data, not for DB
      - ./logs:/app/logs # Example if writing logs to a file (not recommended for stdout/stderr)
    depends_on:
      - db
    # healthcheck: # Your app's healthcheck
    #   test: ["CMD", "/app/healthcheck.py"]
    #   ...

  db:
    image: mcr.microsoft.com/mssql/server:2022-latest # Or your preferred version
    ports:
      - "1433:1433" # Expose SQL Server port to host (for debugging/management tools)
    environment:
      ACCEPT_EULA: "Y"
      MSSQL_SA_PASSWORD: "YourStrongPassword!123" # Store in .env or GitHub secrets
      MSSQL_PID: "Developer" # Or "Express" for free production use (with limitations)
      # Optional: Create a database on startup (though migrations should handle it)
      # MSSQL_DB: CreditRobotDB
      # MSSQL_USER: your_app_user # If you create a specific app user
      # MSSQL_PASSWORD: your_app_user_password
    volumes:
      - mssql_data:/var/opt/mssql # Persist SQL Server data

volumes:
  mssql_data:
  # static_volume:
```
**Important Security Note:** Avoid hardcoding passwords in `docker-compose.yml`. Use an `.env` file (added to `.gitignore`) or GitHub secrets for CI/CD.

## 4. Data Persistence for MS SQL Server

The `db` service in `docker-compose.yml` uses a named volume `mssql_data` mounted at `/var/opt/mssql`. This is where SQL Server stores its database files (`.mdf`, `.ldf`). This ensures that your data persists even if the SQL Server container is removed or recreated.

## 5. Alembic Migrations with MS SQL Server

Alembic, as used in your project, works with MS SQL Server.
1.  **`env.py` Configuration**:
    Alembic's `env.py` reads the `SQLALCHEMY_DATABASE_URI` from your Flask app's config. Ensure this URI is correctly pointing to the MS SQL Server instance when running migrations.
    ```python
    # env.py
    # ...
    # Ensure your app and db are configured correctly before this line
    # from myapp import app # Your Flask app
    # config.set_main_option('sqlalchemy.url', app.config['SQLALCHEMY_DATABASE_URI'])
    # Or, if you have a way to load config directly:
    # from myapp.config import SQLALCHEMY_DATABASE_URI
    # config.set_main_option('sqlalchemy.url', SQLALCHEMY_DATABASE_URI)
    ```
    Make sure `app.py` (or wherever `SQLALCHEMY_DATABASE_URI` is set) is correctly configured when `env.py` is invoked. You might need to set environment variables like `USE_MSSQL=true` and the `MSSQL_*` vars when running Alembic commands.

2.  **Running Migrations**:
    *   **Initial Migration**: If starting fresh with MS SQL Server, you'll generate an initial migration:
        ```bash
        # Ensure your environment is set to point to MS SQL Server
        export USE_MSSQL=true
        export MSSQL_SERVER=localhost,1433 # If running SQL Server locally or port-mapped
        # ... other MSSQL_ vars ...

        flask db init # If first time with Alembic
        flask db migrate -m "Initial migration for MS SQL Server"
        flask db upgrade
        ```
    *   **Applying Migrations**:
        You can run migrations from your local machine (if SQL Server port is exposed and ODBC drivers are installed locally) or by `exec`-ing into the application container:
        ```bash
        docker-compose exec web flask db upgrade
        ```
    *   **Important**: The first time `flask db upgrade` runs against a new MS SQL Server database, it will create the tables. If `MSSQL_DB` was set in `docker-compose.yml` for the `db` service, that database might be auto-created by SQL Server. If not, your application or migration script might need to ensure the database exists before creating tables. SQLAlchemy usually doesn't create databases, only tables. You might need to connect to `master` database first, create your `CreditRobotDB`, then reconnect to `CreditRobotDB` for migrations. This is an advanced setup. A common approach is to have the DBA create the empty database, or use an entrypoint script.

## 6. Using Azure SQL Database (Managed Alternative)

For a fully managed PaaS (Platform as a Service) offering, consider Azure SQL Database.
*   **No Docker Management:** Azure handles the infrastructure, patching, backups, and scaling of the SQL Server instance.
*   **Connection String:** You'll get a connection string from Azure Portal to use in your application's `DATABASE_URL` environment variable.
*   **Firewall Rules:** Configure firewall rules in Azure to allow your application (e.g., if hosted in Azure App Service or AKS) to connect to the Azure SQL Database.
*   **Cost:** This is a paid service, unlike running SQL Server Developer/Express edition in Docker.

## Conclusion

Integrating MS SQL Server into your Dockerized Flask application involves setting up the SQL Server container, configuring ODBC drivers and connection strings in your Flask app, and managing data persistence with volumes. Docker Compose greatly simplifies this multi-container setup. For production, always prioritize security by managing credentials properly and consider managed services like Azure SQL Database for operational efficiency.
