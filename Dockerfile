# Menggunakan base image yang sudah include CUDA agar GPU bisa jalan
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Install Python, pip, dan ffmpeg
RUN apt-get update && apt-get install -y python3-pip ffmpeg && rm -rf /var/lib/apt/lists/*

# Install library yang dibutuhkan
RUN pip3 install runpod boto3 faster-whisper

# Copy semua file ke dalam container
COPY . /app
WORKDIR /app

# Perintah untuk menjalankan worker
CMD ["python3", "handler.py"]
