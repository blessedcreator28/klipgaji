FROM python:3.10

# Install ffmpeg (penting buat video)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Install runpod dan boto3
RUN pip install --no-cache-dir runpod boto3

COPY . .

CMD ["python", "/app/handler.py"]