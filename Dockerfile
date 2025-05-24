#Use Python 3.12 slim base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y\
    gcc \
    g++ \
    libffi-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8080

#RUN with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers=1", "--timeout=120", "app:app"]