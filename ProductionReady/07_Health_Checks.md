# Technical Guide: Health Checks

Health checks are essential for production systems to indicate whether an application instance is running correctly and able to handle traffic. Orchestration systems like Kubernetes, Docker Swarm, or even simple load balancers use health checks to manage application lifecycle, replace unhealthy instances, and prevent routing traffic to failing instances.

This guide explains how to add a health check endpoint to the CreditRobot Flask application and configure Docker's `HEALTHCHECK` instruction.

## 1. Implement a Health Check Endpoint in Flask

A health check endpoint is a simple route in your application that returns a success status code (e.g., `200 OK`) if the application is healthy. "Healthy" can mean different things:
*   The application is running and responding to requests (basic check).
*   The application can connect to critical services like the database (deeper check).

For this guide, we'll implement a basic health check.

### 1.1. Add `/health` Route to `app.py`

Modify your `app.py` to include a `/health` endpoint:

```python
# app.py
# ... (other imports) ...
from flask import Flask, jsonify

app = Flask(__name__)
# ... (your app configuration, logging, etc.) ...

@app.route('/health')
def health_check():
    """
    Basic health check endpoint.
    Returns 200 if the app is running and responsive.
    More advanced checks could include database connectivity, etc.
    """
    # A more advanced check might look like:
    # try:
    #     db.session.execute('SELECT 1') # Example: Check database connection
    #     return jsonify(status="ok", db_connection="ok"), 200
    # except Exception as e:
    #     app.logger.error(f"Health check failed: {e}", exc_info=True)
    #     return jsonify(status="error", reason="database connection failed"), 503 # Service Unavailable

    return jsonify(status="ok", message="Application is healthy"), 200

# ... (rest of your app.py: routes, Gunicorn/Flask logging integration, etc.) ...
```

**Explanation:**
*   A new route `/health` is added.
*   It returns a JSON response with a `200 OK` status, indicating the application is up and responding.
*   The commented-out section shows an example of a more advanced health check that tries to query the database. If such a check fails, it's common to return a `503 Service Unavailable` status. For now, we'll stick to the basic "app is running" check.

## 2. Configure `HEALTHCHECK` in `Dockerfile`

Docker's `HEALTHCHECK` instruction tells Docker how to test a container to check that it is still working. This can detect cases where a process is running but is not in a healthy state (e.g., stuck in an infinite loop, unable to connect to dependencies).

We can use `curl` or a small script to perform the health check. Using a script can be more flexible if you need to make the check more sophisticated later or if `curl` isn't available in your base image (though `python:slim` images usually have it or tools like `wget`).

Let's create a small Python script for the health check and then use it in the `Dockerfile`.

### 2.1. Create a Health Check Script (`healthcheck.py`)

Create a new file named `healthcheck.py` in the root of your project (or a `scripts/` subdirectory).

`healthcheck.py`:
```python
#!/usr/bin/env python3
import http.client
import sys
import os

host = os.environ.get("HEALTHCHECK_HOST", "127.0.0.1")
port = int(os.environ.get("HEALTHCHECK_PORT", 5000)) # Gunicorn's port inside the container
path = os.environ.get("HEALTHCHECK_PATH", "/health")

try:
    conn = http.client.HTTPConnection(host, port, timeout=5) # 5 second timeout
    conn.request("GET", path)
    response = conn.getresponse()
    print(f"Health check status: {response.status}")
    if response.status == 200:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)  # Failure
finally:
    if 'conn' in locals():
        conn.close()
```
**Make this script executable:**
After creating it, you might need to make it executable: `chmod +x healthcheck.py`. The `Dockerfile` can also do this.

**Explanation:**
*   The script makes an HTTP GET request to `http://<host>:<port><path>`.
*   It expects a `200 OK` response.
*   Exits with `0` on success (HTTP 200), and `1` on failure (any other status or exception). Docker interprets these exit codes.
*   Environment variables `HEALTHCHECK_HOST`, `HEALTHCHECK_PORT`, and `HEALTHCHECK_PATH` make it configurable, defaulting to `127.0.0.1:5000/health`.

### 2.2. Update `Dockerfile` to use `HEALTHCHECK`

Modify your `Dockerfile` (from Guide `01_Dockerfile.md`) to include the `HEALTHCHECK` instruction.

```dockerfile
# Stage 1: Base Image Setup
FROM python:3.12-slim-bookworm AS base
# ... (ENV vars, WORKDIR as before) ...

# Stage 2: Build Stage
FROM base AS builder
# ... (COPY requirements.txt, RUN pip install as before) ...

# Stage 3: Application Stage (final image)
FROM base AS application
# ... (COPY --from=builder for dependencies as before) ...

# Copy the application code into the container
COPY . .

# Ensure healthcheck.py is executable
# This assumes healthcheck.py is in the root of the build context
RUN chmod +x /app/healthcheck.py

# Expose the port Gunicorn will run on
EXPOSE 5000

# Add a non-root user and switch to it (Recommended - see Security Hardening guide)
# RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
# USER appuser

# Healthcheck Instruction
# Docker will run this command inside the container to check its health.
# --interval: Run the health check every 30 seconds.
# --timeout: If the command takes longer than 10 seconds, consider it failed.
# --start-period: Grace period of 15 seconds for the container to start up before first check.
# --retries: The container is considered unhealthy after 3 consecutive failures.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD [ "/app/healthcheck.py" ]
  # Alternatively, using curl if available and preferred:
  # CMD curl --fail http://localhost:5000/health || exit 1

# Command to run the application using Gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```

**Explanation of `HEALTHCHECK` in Dockerfile:**
*   `COPY . .`: This now also copies `healthcheck.py` into `/app/healthcheck.py` in the image.
*   `RUN chmod +x /app/healthcheck.py`: Makes the script executable.
*   **`HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 CMD [ "/app/healthcheck.py" ]`**:
    *   `--interval=30s`: Docker will run the health check every 30 seconds.
    *   `--timeout=10s`: If the `healthcheck.py` script takes longer than 10 seconds to run, the check is considered failed.
    *   `--start-period=15s`: Provides a grace period of 15 seconds after the container starts before the first health check is performed. This gives the application time to initialize.
    *   `--retries=3`: If the health check fails 3 consecutive times, the container is marked as `unhealthy`.
    *   `CMD [ "/app/healthcheck.py" ]`: The command Docker runs. It executes our Python script.
    *   The alternative `CMD curl --fail http://localhost:5000/health || exit 1` is a simpler option if `curl` is available and the check is basic. `--fail` makes curl return an error code on HTTP errors (4xx, 5xx).

## 3. Building and Testing Health Checks

1.  **Rebuild your Docker image:**
    ```bash
    docker build -t creditrobot-app .
    # Or if using Docker Compose:
    # docker-compose build web
    ```

2.  **Run the container:**
    ```bash
    docker run -d -p 5000:5000 --name creditrobot_healthy creditrobot-app
    # Or if using Docker Compose:
    # docker-compose up -d web
    ```

3.  **Check container status:**
    After the container starts (and after the `start-period`), Docker will begin performing health checks.
    ```bash
    docker ps
    ```
    You should see output similar to this:
    ```
    CONTAINER ID   IMAGE             COMMAND                  CREATED          STATUS                           PORTS                    NAMES
    abcdef123456   creditrobot-app   "gunicorn --config g…"   10 seconds ago   Up 9 seconds (health: starting)   0.0.0.0:5000->5000/tcp   creditrobot_healthy
    ```
    After a short while (interval + processing time), the status should change to `(healthy)`:
    ```
    CONTAINER ID   IMAGE             COMMAND                  CREATED          STATUS                   PORTS                    NAMES
    abcdef123456   creditrobot-app   "gunicorn --config g…"   45 seconds ago   Up 44 seconds (healthy)   0.0.0.0:5000->5000/tcp   creditrobot_healthy
    ```
    If it becomes `(unhealthy)`, something is wrong. Check the container logs (`docker logs creditrobot_healthy`) and ensure the `/health` endpoint is working and accessible from within the container at `http://127.0.0.1:5000/health`.

4.  **Inspect Health Check Details:**
    You can get more details about the health checks using `docker inspect`:
    ```bash
    docker inspect creditrobot_healthy | grep -A5 Health
    ```
    This will show the recent health check logs and status.

## Conclusion

Implementing a `/health` endpoint in your Flask application and adding a `HEALTHCHECK` instruction to your `Dockerfile` significantly improves the robustness of your application in a containerized environment. It allows Docker (or an orchestrator) to automatically manage your application's state, leading to higher availability and reliability. Remember to tailor the complexity of your health check (e.g., checking database connections) to your application's specific needs.
