# Use Python 3.12 Alpine as required by project
FROM python:3.12-alpine

# Set working directory inside container
WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and templates
COPY app.py .
COPY templates/ ./templates/

# Expose port 5000
EXPOSE 5000

# Run the Flask application
CMD ["python", "app.py"]
