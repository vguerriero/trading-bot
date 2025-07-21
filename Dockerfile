# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and leverage pip cache for faster, more reliable installs
COPY requirements.txt ./

# Install dependencies with caching and increased timeouts
# Requires BuildKit: set DOCKER_BUILDKIT=1 for cache mounts to work
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install --no-cache-dir --retries 10 --timeout 120 -r requirements.txt

# Copy the rest of the application code
COPY . .

# Default command to run the orchestration module
CMD ["python", "-m", "ops.main"]
