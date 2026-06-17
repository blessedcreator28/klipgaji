# Ganti ke versi cudnn8 agar faster-whisper bisa jalan di GPU
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3-pip ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install semua library
RUN pip install --no-cache-dir runpod boto3 faster-whisper huggingface_hub

# Pre-download model
RUN mkdir -p /app/whisper-model && \
    python3 -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-base', local_dir='/app/whisper-model')"

COPY . .

CMD ["python3", "handler.py"]