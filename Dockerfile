# syntax=docker/dockerfile:1.7
FROM python:3.12-slim
WORKDIR /app

# 1️⃣ Copy only the poetry files first
COPY pyproject.toml poetry.lock ./

# 2️⃣ Install Poetry & your dependencies (no-root avoids installing your package)
RUN pip install --no-cache-dir poetry \
 && poetry config virtualenvs.create false \
 && poetry install --only main --no-root

# 3️⃣ Copy the rest of your code
COPY . .

# 4️⃣ Default entrypoint
CMD ["python", "-m", "ops.main"]
