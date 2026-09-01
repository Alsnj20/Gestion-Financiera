FROM python:3.12-slim

RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*
RUN pip install uv

WORKDIR /app
ENV PYTHONPATH=/app/src
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
