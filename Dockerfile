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

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Set environment variable (Optional, can also be done via Cloud Run deployment)
# ENV GOOGLE_AI_API_KEY=your_api_key_here

# Start the Flask app
CMD ["python", "app.py"]
