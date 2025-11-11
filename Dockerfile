# Use official Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for database if it doesn't exist
RUN mkdir -p /app/data

# Set environment variable for database path (can be overridden)
ENV DB_PATH=/app/data/multiverse.db

# Run the bot
CMD ["python", "main.py"]
