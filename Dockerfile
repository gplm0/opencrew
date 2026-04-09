FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/static

# Expose port
EXPOSE 3000

# Run the application
CMD ["python", "-m", "src.cli", "serve", "--host", "0.0.0.0", "--port", "3000"]
