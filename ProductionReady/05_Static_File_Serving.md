# Technical Guide: Static File Serving for Production

In production, serving static files (CSS, JavaScript, images) directly from Flask or Gunicorn is inefficient, especially under load. A dedicated web server like Nginx is much better suited for this task. Nginx can serve static files directly and act as a reverse proxy, forwarding dynamic requests to your Gunicorn application server.

This guide explains how to set up Nginx to serve static files and proxy requests to the CreditRobot Flask application running with Gunicorn.

## 1. Overview of the Setup

The setup involves two Docker containers managed by Docker Compose:
1.  **`web` (Your Application):** The Flask application served by Gunicorn (as configured in previous guides). This container will no longer serve static files directly in production.
2.  **`nginx` (Reverse Proxy):** An Nginx container that:
    *   Receives all incoming HTTP requests.
    *   Serves static files directly from a shared volume.
    *   Forwards (proxies) requests for dynamic content (e.g., API calls, non-static routes) to the `web` container.

## 2. Project Structure for Static Files

Your project has a `static/` directory (e.g., `static/BotHead.png`, `static/CR-RGB.png`). Nginx needs access to these files. We'll achieve this using a shared Docker volume.

## 3. Nginx Configuration (`nginx.conf`)

Create an Nginx configuration file. You can place this in a new directory, for example, `nginx/nginx.conf` or directly in the project root if you prefer.

Create `nginx/nginx.conf` (or `nginx.conf` in root):
```nginx
# nginx/nginx.conf

user nginx;
worker_processes auto; # Or set to a specific number, e.g., number of CPU cores

error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024; # Max connections per worker
}

http {
    include /etc/nginx/mime.types; # Defines file extension to MIME type mapping
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on; # Enables kernel support for sending files
    tcp_nopush on; # Optimize packet delivery
    tcp_nodelay on; # For applications that require low latency
    keepalive_timeout 65; # Timeout for keep-alive connections
    # types_hash_max_size 2048; # Adjust if you have many MIME types

    # Gzip compression (optional but recommended)
    # gzip on;
    # gzip_vary on;
    # gzip_proxied any;
    # gzip_comp_level 6;
    # gzip_buffers 16 8k;
    # gzip_http_version 1.1;
    # gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;

    server {
        listen 80; # Nginx listens on port 80 (standard HTTP)
        server_name localhost; # Or your domain name, e.g., creditrobot.example.com

        # Location for static files
        # /static/ is the URL path. /app/static/ is where files are in the shared volume.
        location /static/ {
            alias /app/static/; # Path where static files are mounted in Nginx container
            autoindex off; # Disable directory listing
            expires 1d;    # Cache static files for 1 day in client browsers
            add_header Cache-Control "public";
        }

        # Location for all other requests (dynamic content)
        location / {
            proxy_pass http://web:5000; # Forward to the 'web' service (Gunicorn) on port 5000
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support (if your app uses WebSockets, e.g., with Flask-SocketIO)
            # proxy_http_version 1.1;
            # proxy_set_header Upgrade $http_upgrade;
            # proxy_set_header Connection "upgrade";
        }
    }
}
```

**Key Nginx Configuration Points:**

*   **`worker_processes`**: Number of Nginx worker processes. `auto` is usually a good choice.
*   **`listen 80`**: Nginx listens on port 80 for incoming HTTP requests.
*   **`location /static/ { ... }`**:
    *   This block tells Nginx how to handle requests where the URL starts with `/static/`.
    *   `alias /app/static/;`: Nginx will look for files in the `/app/static/` directory *inside the Nginx container*. We will mount the project's `static` directory to this location.
    *   `expires 1d;`: Tells client browsers to cache these static files for 1 day.
*   **`location / { ... }`**:
    *   This is a catch-all for any requests not matching `/static/`.
    *   `proxy_pass http://web:5000;`: Forwards the request to the service named `web` (our Flask/Gunicorn app) on port `5000` (where Gunicorn is listening). Docker Compose's internal DNS will resolve `web` to the IP address of the `web` container.
    *   `proxy_set_header ...`: These headers pass information about the original request to Gunicorn, which is important for logging and for the application to know the client's actual IP address and protocol.

## 4. Update `Dockerfile` for the Application (Optional Whitenoise Consideration)

If you choose **not** to use Nginx for static files (e.g., for a simpler setup, though Nginx is generally better for production), you could use a library like [Whitenoise](http://whitenoise.evans.io/). Whitenoise allows your Python application to serve static files efficiently itself, with proper caching headers.

**If using Whitenoise (alternative to Nginx for static files):**
1.  Add `whitenoise` to `requirements.txt`.
2.  Modify `app.py` to wrap the Flask app with Whitenoise:
    ```python
    # app.py
    from whitenoise import WhiteNoise
    # ...
    app = Flask(__name__)
    # Assuming your static files are in 'static/' relative to app.py
    # and accessible via '/static/' URL path.
    app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')
    # ... rest of your app
    ```
    In this case, you would *not* need the Nginx `location /static/` block, and Nginx would proxy all requests to Gunicorn. However, for this guide, we are focusing on the Nginx setup.

**For the Nginx setup, no changes are typically needed in the application's `Dockerfile` or `app.py` regarding static file serving, as Nginx will handle it externally.**

## 5. Create `Dockerfile` for Nginx (Optional, if customizing Nginx image)

Usually, the official Nginx image is sufficient. You only need a custom Dockerfile for Nginx if you need to install extra Nginx modules or make complex setup changes to the Nginx image itself. For our case (just providing a config file), we can mount the config using Docker Compose.

If you did need one (e.g., `nginx/Dockerfile`):
```dockerfile
# nginx/Dockerfile (Optional - only if you need to customize the Nginx image itself)
FROM nginx:1.25-alpine
# Remove default config
RUN rm /etc/nginx/conf.d/default.conf
# Copy your custom config
COPY nginx.conf /etc/nginx/nginx.conf
```

## 6. Update `docker-compose.yml`

Modify your `docker-compose.yml` to include the Nginx service and share the static files via a volume.

```yaml
version: '3.8'

services:
  web:
    build: . # Path to your Flask app's Dockerfile
    image: creditrobot-app
    # Gunicorn is now only accessible within the Docker network, not directly from host
    # ports:
    #   - "5000:5000" # No longer map Gunicorn directly if Nginx is the entry point
    expose:
      - "5000" # Expose Gunicorn's port to other services in the network
    environment:
      SECRET_KEY: 'your_super_secret_production_key'
      DATABASE_URL: 'sqlite:////app/instance/creditrobot.db'
      FLASK_ENV: 'production'
      GUNICORN_LOG_LEVEL: 'info'
    volumes:
      - creditrobot_db_data:/app/instance
      - static_volume:/app/static  # Share static files with Nginx
    # depends_on:
    #   - db # If you have a separate db container

  nginx:
    image: nginx:1.25-alpine # Use the official Nginx image
    ports:
      - "80:80" # Map Nginx port 80 to host port 80 (or e.g., 8080:80)
    volumes:
      - ./static/:/app/static/:ro # Mount project's static folder to /app/static in Nginx (read-only)
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro # Mount your Nginx config (read-only)
      # If you used a custom nginx/Dockerfile:
      # - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro # Path might differ
    depends_on:
      - web # Nginx should start after the web service is available (though proxy will retry)

volumes:
  creditrobot_db_data:
  static_volume: # Define the volume for static files (can be empty if bind mounting to nginx)
                 # Actually, for Nginx serving static files directly from the host path,
                 # this named volume isn't strictly necessary for the web app if Nginx handles all /static.
                 # The web app's Dockerfile still copies static/ into its image,
                 # which is fine but not used if Nginx serves them.
                 # The crucial part is - ./static/:/app/static/:ro for nginx.
```
**Explanation of `docker-compose.yml` changes:**

*   **`web` service:**
    *   The `ports` mapping for Gunicorn (e.g., `5000:5000`) is removed or commented out. Nginx will be the public entry point.
    *   `expose: - "5000"` makes Gunicorn's port 5000 accessible to other services in the Docker network (specifically, to Nginx) but not directly from the host.
    *   `volumes: - static_volume:/app/static`: This line might be redundant if Nginx is serving directly from a bind mount of `./static`. If your Flask app *also* needs access to static files internally (e.g., for templates using `url_for('static', ...)` to generate URLs that Nginx will then serve), then having the files in the `web` container at `/app/static` is still correct. The Dockerfile's `COPY . .` already does this.
*   **`nginx` service:**
    *   `image: nginx:1.25-alpine`: Uses the official lightweight Nginx image.
    *   `ports: - "80:80"`: Maps port 80 of the Nginx container to port 80 on your host machine. This is how users access your application.
    *   `volumes:`
        *   `./static/:/app/static/:ro`: This is crucial. It bind-mounts your project's local `./static` directory into the `/app/static` directory inside the Nginx container in read-only (`ro`) mode. This is where Nginx will find the static files to serve.
        *   `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`: Mounts your custom Nginx configuration file into the Nginx container, replacing its default configuration.
    *   `depends_on: - web`: Tells Docker Compose to start the `web` service before the `nginx` service.

## 7. Running the Setup

1.  Ensure you have `nginx/nginx.conf` (or `nginx.conf`) created.
2.  Ensure your `static/` directory contains your static assets.
3.  Run Docker Compose:
    ```bash
    docker-compose up -d --build
    ```
    The `--build` flag rebuilds your images if necessary.

Now, when you access `http://localhost` (or your server's IP/domain) in a browser:
*   Requests for `http://localhost/static/somefile.css` will be served directly by Nginx from your `./static` folder.
*   Requests for `http://localhost/` or any other non-static path will be proxied by Nginx to your Gunicorn application running on the `web` service.

## 8. SSL/HTTPS (Further Steps)

For a true production setup, you'll need HTTPS. Nginx is also the ideal place to handle SSL termination:
*   Obtain an SSL certificate (e.g., from Let's Encrypt).
*   Configure Nginx to listen on port 443 (HTTPS) and use the SSL certificate.
*   Typically, you'd redirect HTTP traffic on port 80 to HTTPS on port 443.
This is an advanced topic beyond this specific guide but is a critical next step for production. Tools like Certbot can help automate certificate management with Nginx.

By using Nginx for static file serving and as a reverse proxy, you create a more robust, performant, and scalable production environment for your CreditRobot application.
