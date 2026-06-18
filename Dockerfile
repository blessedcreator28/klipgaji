# Gunakan base image yang sudah ada CUDA-nya
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Install Python dan dependencies
RUN apt-get update && apt-get install -y python3-pip ffmpeg
RUN pip3 install runpod boto3 faster-whisper

# Copy file aplikasi
COPY . /app
WORKDIR /app

# Jalankan worker
CMD ["python3", "handler.py"]
