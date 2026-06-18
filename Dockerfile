FROM runpod/base:0.6.0-cuda12.1.0

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install library utama + library CUDA khusus pendukung faster-whisper
RUN pip3 install runpod boto3 faster-whisper nvidia-cublas-cu12 nvidia-cudnn-cu12

# PANGGANG MODEL (Cara Aman): Cuma download file mentah ke cache, tanpa nyalain engine AI-nya
RUN python3 -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-small')"

COPY . /app
WORKDIR /app

CMD ["python3", "handler.py"]
