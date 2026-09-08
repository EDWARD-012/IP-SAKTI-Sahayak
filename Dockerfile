# IP-SAKTI Sahayak — Docker image
# Note: This container runs the Django web app only.
# Ollama (LLM) must be accessible via OLLAMA_BASE_URL (host machine or separate container).
# Chroma and SQLite are file-based and persist at /app/data volume mount.

FROM python:3.11-slim

# System dependencies for PDF parsing + sentence-transformers
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Collect static files
RUN python manage.py collectstatic --no-input

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Gunicorn: 1 worker (embedded Chroma read-only), 4 threads
CMD ["gunicorn", "ip_sakti.wsgi:application", \
     "--workers", "1", \
     "--threads", "4", \
     "--timeout", "120", \
     "--bind", "0.0.0.0:8000"]

EXPOSE 8000
