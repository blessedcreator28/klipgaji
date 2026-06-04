FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Setup lingkungan
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Jakarta

# Install python, ffmpeg, dan git
RUN apt-get update && apt-get install -y \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# INI KUNCINYA: Paksa builder buat buang cache lama
ARG CACHEBUST=1

# Copy daftar belanja
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "handler.py"]