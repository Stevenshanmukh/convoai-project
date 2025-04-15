# Use Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install ffmpeg and dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Ensure ffmpeg and ffprobe are in the PATH
ENV PATH="/usr/local/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Start the Flask app
CMD ["python", "main.py"]
