# Use an official lightweight Python image
FROM python:3.11-slim

# Set system environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to take advantage of Docker cache
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Run Streamlit upon container launch
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
