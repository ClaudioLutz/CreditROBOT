# Technical Guide: Security Hardening

Security is a critical aspect of any production application. This guide outlines several security hardening steps for the CreditRobot application, focusing on Docker image security and general Flask application best practices.

## 1. Docker Image Security

### 1.1. Use a Non-Root User in Docker Container

Running applications as the `root` user inside a container is a security risk. If an attacker compromises your application, they would gain root privileges within the container, potentially leading to further exploits.

**Steps to implement:**

1.  **Modify `Dockerfile` to create and use a non-root user:**

    ```dockerfile
    # Stage 1: Base Image Setup
    FROM python:3.12-slim-bookworm AS base
    ENV PYTHONDONTWRITEBYTECODE 1
    ENV PYTHONUNBUFFERED 1
    WORKDIR /app

    # Create a non-root user and group
    # Using --system creates users/groups without a home directory in /home and no shell
    RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

    # Stage 2: Build Stage (still as root to install packages)
    FROM base AS builder
    COPY requirements.txt .
    RUN pip install --no-cache-dir --upgrade pip && \
        pip install --no-cache-dir -r requirements.txt

    # Stage 3: Application Stage (final image)
    FROM base AS application # Start from the base again, which has 'appuser' defined

    # Copy installed dependencies from builder stage (ensure paths are correct)
    # These paths are typical for global site-packages with python:slim
    COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
    COPY --from=builder /usr/local/bin /usr/local/bin

    # Copy application code
    COPY . .

    # Ensure healthcheck.py is executable by the user (if it exists)
    # If healthcheck.py needs to be run by appuser, ensure it has correct permissions
    # RUN chmod +x /app/healthcheck.py
    # If appuser needs to own files (e.g., if it needs to write to a log file within /app, which is not recommended)
    # RUN chown -R appuser:appgroup /app
    # For instance folder, if SQLite is used AND instance folder is part of the image (not just volume):
    # RUN mkdir -p /app/instance && chown -R appuser:appgroup /app/instance
    # However, if using volumes for 'instance', permissions are managed by Docker on volume mount.

    # Switch to the non-root user
    USER appuser

    EXPOSE 5000

    # HEALTHCHECK (ensure healthcheck.py or curl can run as appuser)
    # If using healthcheck.py, it must be executable by appuser.
    # If curl is used, appuser must be able to run it.
    HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
      CMD [ "/app/healthcheck.py" ] # Or: CMD curl --fail http://localhost:5000/health || exit 1

    CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
    ```

    **Explanation:**
    *   `RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser`: Creates a system group `appgroup` and a system user `appuser` belonging to this group. System users typically don't have login shells or home directories in `/home`, which is good for security.
    *   The build stage (`builder`) can still run as root to install packages system-wide.
    *   In the final `application` stage, we start from `base` (where `appuser` was created).
    *   `USER appuser`: Switches the context to run subsequent commands (including `CMD`) as `appuser`.
    *   **File Permissions:** If `appuser` needs to write to any files or directories within the container (e.g., a temporary file, or if you were *not* using volumes for `instance/` and SQLite was inside the container), you'd need `chown` to give `appuser` ownership. However, best practice is to write persistent data to volumes and logs to `stdout`/`stderr`. The `instance` folder is usually best handled by a volume for SQLite.

### 1.2. Minimize Image Footprint

*   **Use Slim Base Images:** `python:3.12-slim-bookworm` is already a good start. Avoid full Debian/Ubuntu images if not necessary.
*   **Multi-stage Builds:** Already implemented in Guide `01_Dockerfile.md`. This ensures build tools and intermediate files are not included in the final image.
*   **`.dockerignore`:** Ensure your `.dockerignore` (Guide `01`) is comprehensive to exclude unnecessary files (VCS directories, local caches, IDE configs, tests if not run in the image, etc.).
*   **Minimize Layers:** Each `RUN` command creates a layer. Chain related `RUN` commands where sensible (e.g., `apt-get update && apt-get install && rm -rf /var/lib/apt/lists/*`).
*   **Uninstall Build Dependencies:** If you install build-time dependencies in the final stage, uninstall them if they are not needed at runtime.

### 1.3. Scan Images for Vulnerabilities

Use tools to scan your Docker images for known vulnerabilities in OS packages and application dependencies.
*   **Docker Scout:** If you use Docker Hub, Docker Scout can provide image analysis and vulnerability reports.
*   **Trivy (by Aqua Security):** An open-source scanner. Can be integrated into CI/CD.
    ```bash
    # Example: Scan an image locally
    trivy image yourdockerhubusername/creditrobot-app:latest
    ```
*   **Snyk:** A commercial tool with a free tier, can scan code, dependencies, and Docker images.
*   **GitHub Dependabot and Code Scanning:** GitHub provides automated dependency updates and can scan code for vulnerabilities (including some container scanning capabilities).

**In CI/CD (GitHub Actions Example - Conceptual):**
```yaml
# ... (in your ci-cd-pipeline.yml) ...
      - name: Scan image with Trivy
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'yourdockerhubusername/creditrobot-app:latest' # Or the GHCR path
          format: 'table'
          exit-code: '0' # '0' means report vulnerabilities but don't fail build
                         # '1' means fail build on vulnerabilities (based on severity)
          ignore-unfixed: true
          vuln-type: 'os,library'
          severity: 'CRITICAL,HIGH' # Fail on CRITICAL or HIGH
```

### 1.4. Regular Updates

*   **Base Images:** Regularly update your base image (`python:3.12-slim-bookworm`) by rebuilding your application image. Base images receive security patches.
*   **Python Dependencies:** Regularly update your Python packages in `requirements.txt` and rebuild. Tools like `pip-audit` or Dependabot can help identify vulnerable dependencies.
    ```bash
    pip install pip-audit
    pip-audit -r requirements.txt
    ```

## 2. Flask Application Security Best Practices

### 2.1. Secret Key Management
*   As covered in Guide `04_Configuration_Management.md`, ensure `SECRET_KEY` is strong, unique for production, and loaded from environment variables, not hardcoded.

### 2.2. Input Validation
*   Always validate and sanitize user-supplied data to prevent common web vulnerabilities like Cross-Site Scripting (XSS) and SQL Injection (though SQLAlchemy helps with SQLi if used correctly).
*   Use libraries like WTForms for form handling, which include validation.
*   For APIs, validate incoming data structures and types.

### 2.3. Cross-Site Scripting (XSS) Protection
*   Flask's template engine (Jinja2) automatically escapes HTML by default, which helps prevent XSS. Be cautious if you ever disable autoescaping (e.g., using `|safe` filter) – only do so on trusted content.
*   Set appropriate `Content-Security-Policy` (CSP) headers. Flask-Talisman can help with this.

### 2.4. Cross-Site Request Forgery (CSRF) Protection
*   Use Flask-WTF or Flask-SeaSurf to implement CSRF protection for forms. This involves generating and validating unique tokens for each user session.

### 2.5. Secure Headers
*   Use HTTP headers to enhance security. Examples:
    *   `X-Frame-Options: DENY` (prevents clickjacking)
    *   `X-Content-Type-Options: nosniff`
    *   `Content-Security-Policy`
    *   `Strict-Transport-Security` (HSTS) (if using HTTPS)
*   Libraries like [Flask-Talisman](https://github.com/GoogleCloudPlatform/flask-talisman) can automatically set many of these.
    1. Add `Flask-Talisman` to `requirements.txt`.
    2. Initialize in `app.py`:
       ```python
       from flask_talisman import Talisman
       # ...
       app = Flask(__name__)
       Talisman(app, content_security_policy=None) # Basic setup, customize CSP as needed
       ```

### 2.6. HTTPS
*   As mentioned in Guide `05_Static_File_Serving.md`, use Nginx to handle SSL/TLS termination and enforce HTTPS in production.

### 2.7. Rate Limiting
*   Protect against brute-force attacks and denial-of-service by implementing rate limiting on sensitive endpoints (e.g., login). Libraries like [Flask-Limiter](https://flask-limiter.readthedocs.io/) can be used.

### 2.8. Debug Mode
*   Ensure `FLASK_ENV` is set to `production` and `app.debug = False` in production. The `Dockerfile` and Gunicorn should handle this. Never expose the Werkzeug debugger in production.

### 2.9. Dependency Updates
*   Keep Flask and all its extensions and other Python dependencies up-to-date to receive security patches. Use `pip-audit` or other tools to monitor for vulnerabilities.

## 3. Secrets Management (Advanced)

For highly sensitive data, consider using dedicated secrets management tools, especially in complex deployments:
*   HashiCorp Vault
*   AWS Secrets Manager
*   Google Cloud Secret Manager
*   Azure Key Vault

These tools provide secure storage, access control, and auditing for secrets. Application code would then fetch secrets from these services at runtime.

## Conclusion

Security is an ongoing process, not a one-time setup. Regularly review your security posture, update dependencies, scan for vulnerabilities, and stay informed about best practices. Implementing the steps in this guide provides a solid foundation for securing your CreditRobot application in production.
