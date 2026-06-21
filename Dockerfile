# Pake versi yang lebih lengkap (devel) biar library pendukung GPU ada semua
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Set environment biar ga minta input pas install
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip biar install library ga error
RUN pip install --no-cache-dir --upgrade pip

# Install library utama
RUN pip install --no-cache-dir runpod boto3 faster-whisper

COPY . .

# Biarkan RunPod yang panggil handler.py
CMD ["python3", "handler.py"]