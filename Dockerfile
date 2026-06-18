# Ganti pakai base image resmi NVIDIA yang super stabil
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Set environment agar instalasi tidak meminta input manual
ENV DEBIAN_FRONTEND=noninteractive

# Install Python, pip, dan FFmpeg secara bersih
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip ke versi terbaru
RUN pip3 install --no-cache-dir --upgrade pip

# Install semua library yang dibutuhkan handler lo
RUN pip3 install --no-cache-dir runpod boto3 faster-whisper

# Copy semua file project lo
COPY . /app
WORKDIR /app

# Perintah eksekusi utama
CMD ["python3", "handler.py"]
