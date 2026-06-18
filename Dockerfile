FROM runpod/base:0.6.0-cuda12.1.0

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install library utama + library CUDA lengkap (Kunci anti-unhealthy)
RUN pip3 install runpod boto3 faster-whisper nvidia-cublas-cu12 nvidia-cudnn-cu12

COPY . /app
WORKDIR /app

CMD ["python3", "handler.py"]
