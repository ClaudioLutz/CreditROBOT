# Technical Guide: Creating a Dockerfile

This guide provides detailed instructions for creating a `Dockerfile` to containerize the CreditRobot application. A `Dockerfile` is a script containing a series of instructions that Docker uses to build a custom image. We will also create a `.dockerignore` file to exclude unnecessary files from the build context, optimizing the build process.

## 1. Create `.dockerignore` File

Before writing the `Dockerfile`, it's good practice to create a `.dockerignore` file in the project's root directory. This file lists files and directories that should be excluded from the Docker image. This helps in reducing the image size and speeding up the build process by not copying unnecessary files (like local virtual environments, cache files, or IDE configurations).

Create a file named `.dockerignore` in the root of your project with the following content:

```
# Git
.git
.gitignore

# Python virtual environment
.venv
venv/
env/
*/env/
*/venv/
*.pyc
__pycache__/
*.pyo
*.pyd

# Instance folder (if database is managed outside or via volume)
# Comment out if you intend to bake the initial SQLite DB into the image for some reason.
# instance/

# IDE and OS specific
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store

# Test files (if you run tests in a separate stage or outside the main app image)
# tests/
# *.test.py
# pytest.ini
# .pytest_cache/

# Documentation files (unless you need them in the image)
# Description Deutsch/
# Description English/
# Description Französisch/
# Description Italienisch/
# Documentation.md
# MemoryPlan.md
# ReadMe.md
# ProductionReady/ # Exclude the guide itself from the image

# Logs
*.log
questions_log.txt
```

**Note on `instance/`:** The `instance/creditrobot.db` SQLite database is currently included. If you plan to manage the database using Docker volumes (recommended, see guide `03_Database_Management.md`) or switch to an external database, you should uncomment `instance/` in `.dockerignore` to prevent the local database from being copied into the image. For now, we'll assume it might be needed for initial image testing, but for true production, it should be externalized.

## 2. Create the `Dockerfile`

Create a file named `Dockerfile` (no extension) in the root of your project. Add the following instructions:

```dockerfile
# Stage 1: Base Image Setup
FROM python:3.12-slim-bookworm AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Consider adding FLASK_APP=app.py and FLASK_ENV=production later,
# or manage these through docker run -e or docker-compose.yml

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any are needed, e.g., for certain Python packages)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Stage 2: Build Stage (for installing dependencies)
# This helps in caching dependencies and rebuilding faster if only app code changes.
FROM base AS builder

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# Consider creating and using a virtual environment within the Docker image for better isolation,
# though it's less critical when the container itself is an isolated environment.
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Application Stage (final image)
FROM base AS application

# Copy the installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code into the container
COPY . .
# If you uncommented 'instance/' in .dockerignore and want to initialize an empty one:
# RUN mkdir -p instance

# Expose the port Gunicorn will run on
# This should match the port used in the CMD instruction
EXPOSE 5000

# Add a non-root user and switch to it
# (Details in Security Hardening guide)
# RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
# USER appuser

# Command to run the application using Gunicorn
# Ensure 'gunicorn' is in your requirements.txt
# The command should be: gunicorn -b <host>:<port> <your_wsgi_module>:<your_flask_app_instance>
# For this project, it's likely app:app (referring to app.py and the Flask instance named 'app')
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```

## 3. Key `Dockerfile` Instructions Explained

*   **`FROM python:3.12-slim-bookworm AS base`**: Specifies the base image. `python:3.12-slim-bookworm` is a good choice as it's lightweight and based on Debian Bookworm. Using `AS base` names this stage, useful for multi-stage builds.
*   **`ENV PYTHONDONTWRITEBYTECODE 1`**: Prevents Python from writing `.pyc` files to disk.
*   **`ENV PYTHONUNBUFFERED 1`**: Ensures that Python output (like logs) is sent straight to the terminal without being buffered, which is good for Docker logging.
*   **`WORKDIR /app`**: Sets the default directory for subsequent commands and when you `docker exec` into the container.
*   **`COPY requirements.txt .`**: Copies the `requirements.txt` file into the image. This is done before copying the rest of the code to leverage Docker's layer caching. If `requirements.txt` doesn't change, Docker can reuse the layer where dependencies were installed, speeding up builds.
*   **`RUN pip install --no-cache-dir -r requirements.txt`**: Installs the Python dependencies. `--no-cache-dir` reduces image size by not storing the pip download cache.
*   **Multi-stage builds (`AS builder`, `AS application`, `COPY --from=builder ...`):**
    *   The `builder` stage installs dependencies.
    *   The `application` stage starts again from the `base` (which is cleaner) and copies only the installed packages from the `builder` stage and the application code. This can result in a smaller final image by excluding build tools or intermediate files if they were part of the builder stage.
*   **`COPY . .`**: Copies the rest of the application code from your project directory into the `/app` directory in the image. This respects `.dockerignore`.
*   **`EXPOSE 5000`**: Informs Docker that the application listens on port 5000 at runtime. This is documentation; you still need to map this port when running the container (e.g., `docker run -p 80:5000 ...`).
*   **`CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]`**: Specifies the default command to run when the container starts. We're using Gunicorn, a production-ready WSGI server.
    *   `app:app` refers to the `app` Flask application instance within the `app.py` file.
    *   `--config gunicorn.conf.py` points to a Gunicorn configuration file, which we'll discuss in the "Production-Grade Web Server" guide. You'll need to create this file.

## 4. Next Steps

*   **Add Gunicorn to `requirements.txt`**: If not already present, add `gunicorn` to your `requirements.txt` file.
*   **Create `gunicorn.conf.py`**: This file will contain Gunicorn settings (see Guide `02_Production_Web_Server.md`).
*   **Build the image**: Navigate to your project's root directory (where the `Dockerfile` is) and run `docker build -t creditrobot-app .`.
*   **Run the container**: After a successful build, you can try running it: `docker run -p 5000:5000 creditrobot-app`. You'll need to configure Gunicorn and potentially database access for it to fully work.

This guide provides a solid foundation for your `Dockerfile`. Subsequent guides will elaborate on Gunicorn configuration, database management, security hardening (like adding a non-root user), and other production considerations.
