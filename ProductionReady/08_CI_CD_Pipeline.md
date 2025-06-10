# Technical Guide: CI/CD Pipeline with GitHub Actions

Automating the build, test, and deployment process through a CI/CD (Continuous Integration/Continuous Deployment) pipeline is crucial for reliable and efficient software delivery. This guide outlines how to set up a basic CI/CD pipeline for the CreditRobot project using GitHub Actions.

The pipeline will:
1.  Trigger on pushes to the `main` branch and pull requests targeting `main`.
2.  Set up the Python environment.
3.  Lint the code (e.g., with Flake8).
4.  Run tests (conceptually, as detailed tests might not be fully implemented yet).
5.  Build the Docker image.
6.  Log in to a Docker container registry (e.g., Docker Hub or GitHub Container Registry).
7.  Push the Docker image to the registry.

## 1. Prerequisites

*   **GitHub Repository:** Your project should be hosted on GitHub.
*   **Docker Hub Account (Optional):** If pushing to Docker Hub, you'll need an account and an access token.
*   **GitHub Container Registry (GHCR):** Alternatively, you can use GHCR, which integrates well with GitHub Actions.

## 2. Create GitHub Actions Workflow File

GitHub Actions are defined by YAML files in the `.github/workflows/` directory of your repository.

Create a file named `.github/workflows/ci-cd-pipeline.yml`:

```yaml
# .github/workflows/ci-cd-pipeline.yml

name: CreditRobot CI/CD Pipeline

on:
  push:
    branches: [ main ] # Triggers on push to main branch
  pull_request:
    branches: [ main ] # Triggers on PRs to main branch

jobs:
  build-and-test:
    name: Build, Lint, Test, and Push Docker Image
    runs-on: ubuntu-latest # Use the latest Ubuntu runner

    steps:
      - name: Checkout code
        uses: actions/checkout@v4 # Action to checkout your repository

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12' # Match your project's Python version
          cache: 'pip' # Cache pip dependencies

      - name: Install dependencies (including linters, test tools)
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install flake8 # Or your preferred linter/formatter
          # pip install pytest pytest-cov # If using pytest

      - name: Lint with Flake8
        run: |
          # Stop the build if there are Python syntax errors or undefined names
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          # Exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
        # Add other linters or formatters (e.g., Black, Pylint) if desired

      - name: Run tests (Conceptual)
        run: |
          echo "Running tests..."
          # Replace with your actual test command, e.g.:
          # pytest --cov=./ --cov-report=xml
          # For now, we'll just simulate a successful test run
          exit 0
        # This step should be updated once tests are implemented (see Guide 10)

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3 # Allows building multi-platform images, etc.

      - name: Login to Docker Hub (Optional)
        if: github.event_name == 'push' && github.ref == 'refs/heads/main' # Only on push to main
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
        # To use GitHub Container Registry (GHCR) instead:
        # uses: docker/login-action@v3
        # with:
        #   registry: ghcr.io
        #   username: ${{ github.actor }}
        #   password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: . # Build context is the root of the repository
          file: ./Dockerfile # Path to your Dockerfile
          push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }} # Push only on merge/push to main
          tags: | # Replace with your image name and tags
            yourdockerhubusername/creditrobot-app:latest
            yourdockerhubusername/creditrobot-app:${{ github.sha }}
            # For GHCR:
            # ghcr.io/${{ github.repository_owner }}/creditrobot-app:latest
            # ghcr.io/${{ github.repository_owner }}/creditrobot-app:${{ github.sha }}
          # cache-from: type=gha # Cache Docker layers from previous runs
          # cache-to: type=gha,mode=max


    outputs: # Example of outputting image name for potential deployment job
      image_name_latest: yourdockerhubusername/creditrobot-app:latest # Update with your actual image name
      # image_name_latest_ghcr: ghcr.io/${{ github.repository_owner }}/creditrobot-app:latest
```

## 3. Understanding the Workflow

*   **`name`**: The name of your workflow.
*   **`on`**: Defines triggers for the workflow.
    *   `push: branches: [ main ]`: Runs when code is pushed to the `main` branch.
    *   `pull_request: branches: [ main ]`: Runs when a pull request is opened (or updated) targeting the `main` branch.
*   **`jobs`**: Defines a set of jobs. Here, we have one job: `build-and-test`.
    *   `runs-on: ubuntu-latest`: Specifies the runner environment.
*   **`steps`**: A sequence of tasks within the job.
    *   **`actions/checkout@v4`**: Checks out your repository code into the runner.
    *   **`actions/setup-python@v5`**: Sets up the specified Python version and caches pip dependencies.
    *   **`Install dependencies`**: Installs project dependencies from `requirements.txt` and any linters/test tools.
    *   **`Lint with Flake8`**: Runs Flake8 to check code style and quality. Adjust commands as needed.
    *   **`Run tests (Conceptual)`**: This is a placeholder. Once you have tests (Guide `10_Testing.md`), replace `exit 0` with your actual test command (e.g., `pytest`).
    *   **`docker/setup-buildx-action@v3`**: Sets up Docker Buildx, which is an advanced builder backend.
    *   **`Login to Docker Hub` (or GHCR)**:
        *   This step is conditional: `if: github.event_name == 'push' && github.ref == 'refs/heads/main'`. It only runs when code is pushed to the `main` branch (i.e., after a PR is merged).
        *   Uses `docker/login-action@v3` to log in to a container registry.
        *   `secrets.DOCKERHUB_USERNAME` and `secrets.DOCKERHUB_TOKEN`: These are GitHub secrets you need to configure in your repository settings (see step 4).
        *   For GHCR, `secrets.GITHUB_TOKEN` is automatically available.
    *   **`Build and push Docker image`**:
        *   Uses `docker/build-push-action@v5`.
        *   `context: .`: The Docker build context is the root of your repository.
        *   `file: ./Dockerfile`: Specifies the path to your Dockerfile.
        *   `push: ${{ ... }}`: Conditional push, same as login.
        *   `tags`: Defines the tags for your Docker image.
            *   `yourdockerhubusername/creditrobot-app:latest` (or `ghcr.io/...:latest`)
            *   `yourdockerhubusername/creditrobot-app:${{ github.sha }}` (tags with the commit SHA for versioning)
            *   **Important:** Replace `yourdockerhubusername` with your actual Docker Hub username or use the GHCR format.
        *   `cache-from`/`cache-to`: Optional, for caching Docker layers to speed up builds.

## 4. Configure GitHub Secrets

If pushing to Docker Hub (or another external registry):
1.  Go to your GitHub repository.
2.  Click on "Settings" -> "Secrets and variables" -> "Actions".
3.  Click "New repository secret".
4.  Add `DOCKERHUB_USERNAME`: Your Docker Hub username.
5.  Add `DOCKERHUB_TOKEN`: Your Docker Hub access token (create one on Docker Hub under Account Settings -> Security).

If using GitHub Container Registry (GHCR), `GITHUB_TOKEN` is automatically provided and has permissions to push to GHCR within your repository's scope. You might need to ensure your user or organization settings allow GitHub Actions to push images to GHCR.

## 5. Committing and Testing the Workflow

1.  Create the `.github/workflows/ci-cd-pipeline.yml` file in your project.
2.  Commit and push it to your GitHub repository.
    ```bash
    git add .github/workflows/ci-cd-pipeline.yml
    git commit -m "Add GitHub Actions CI/CD pipeline"
    git push
    ```
3.  Go to the "Actions" tab in your GitHub repository. You should see the workflow running.
4.  If you push to `main` or create a PR targeting `main`, the workflow will trigger.

## 6. Next Steps: Continuous Deployment (CD)

This guide focuses on CI (building and testing the image). For CD (deploying the image):
*   You would add another job to your workflow or a separate workflow.
*   This job would trigger after the image is successfully pushed.
*   Deployment steps depend heavily on your hosting environment (e.g., a server with Docker, Kubernetes, AWS ECS, Heroku).
*   It might involve:
    *   SSHing into a server and running `docker pull yourimage && docker-compose up -d --force-recreate`.
    *   Using `kubectl apply -f kubernetes-deployment.yml`.
    *   Using `aws ecs update-service --cluster <cluster> --service <service> --force-new-deployment`.

## Conclusion

This basic CI/CD pipeline with GitHub Actions automates essential checks and the Docker image building/pushing process. It enhances code quality through linting and (eventually) testing, and ensures that a deployable Docker image is always available for your `main` branch. Remember to replace placeholders like `yourdockerhubusername` and to implement actual tests for a truly robust pipeline.
