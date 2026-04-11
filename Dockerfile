# Use a small, stable Python base image
FROM python:3.11-slim

# Set environment variables for better performance
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 5000

WORKDIR /app

# Install system dependencies if needed (none for our pure python version)
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure the database directory exists (if not using disk)
RUN mkdir -p /data

# Standard gunicorn launch - 1 worker for memory safety
CMD gunicorn --worker-class gthread --threads 4 --workers 1 --timeout 120 -b 0.0.0.0:$PORT api:app
