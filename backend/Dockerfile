# Use slim Python image for a smaller production image
FROM python:3.11-slim

# Prevent Python from writing pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (none needed for this stack, but useful for psycopg2 later)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run sets PORT; default to 8080
ENV PORT=8080

# Expose the port
EXPOSE ${PORT}

# Start Uvicorn — bind to 0.0.0.0 so Cloud Run can route traffic
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
