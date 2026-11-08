
# Lightweight Python 3.12 environment
FROM python:3.12-slim

# Application directory inside the container
WORKDIR /app

# Python configuration
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and SQL transformations
COPY pipeline/ pipeline/
COPY sql/ sql/
COPY tests/ tests/

# Run Python tests by default
CMD ["python", "-m", "pytest", "-q"]
