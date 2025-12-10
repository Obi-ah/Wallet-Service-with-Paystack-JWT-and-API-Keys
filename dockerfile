# Use lightweight Python image
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose port FastAPI will run on
EXPOSE 8080

# Start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]