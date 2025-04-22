FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

ARG GOOGLE_API_KEY
ARG LINE_CHANNEL_ACCESS_TOKEN
ARG LINE_CHANNEL_SECRET
ENV GOOGLE_API_KEY=$GOOGLE_API_KEY
ENV LINE_CHANNEL_ACCESS_TOKEN=$LINE_CHANNEL_ACCESS_TOKEN
ENV LINE_CHANNEL_SECRET=$LINE_CHANNEL_SECRET

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY main.py .

# Expose the app port
EXPOSE 8000

# Start FastAPI using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

