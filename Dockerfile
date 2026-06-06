FROM python:3.10

# Install dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory absolut
WORKDIR /app

# Install runpod
RUN pip install --no-cache-dir runpod

# Copy seluruh file
COPY . .

# Pastikan path ke handler.py jelas
CMD ["python", "/app/handler.py"]