FROM python:3.11-slim

# Install system dependencies for hardware libs (RPI.GPIO needs gcc)
RUN apt-get update && apt-get install -y \
    gcc \
    i2c-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY power_monitor.py .

# Ensure logs are flushed immediately
ENV PYTHONUNBUFFERED=1

CMD ["python", "power_monitor.py"]
