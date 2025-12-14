# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY language_resources/ ./language_resources/

# Create directories for user data
RUN mkdir -p /app/data/sessions /app/data/user_resources

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Expose port for web UI
EXPOSE 8080

# Run the web application
CMD ["python", "-m", "uvicorn", "text_glosser.web.main:app", "--host", "0.0.0.0", "--port", "8080"]
