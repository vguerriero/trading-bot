# syntax=docker/dockerfile:1.7
FROM python:3.12-slim
WORKDIR /app
COPY poetry.lock pyproject.toml ./
RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false \
 && poetry install --only main
COPY . .
CMD ["python", "-m", "ops.main"]
