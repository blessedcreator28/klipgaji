FROM runpod/base:0.6.0-cuda12.1.0

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install library utama
RUN pip3 install runpod boto3 faster-whisper nvidia-cublas-cu12 nvidia-cudnn-cu12

# Baris pemecah cache (WAJIB biar Docker nge-refresh handler.py baru)
RUN echo "Build Terakhir Sore Ini"

COPY . /app
WORKDIR /app

CMD ["python3", "handler.py"]
