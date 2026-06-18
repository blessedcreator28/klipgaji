# Menggunakan image resmi RunPod yang sudah di-cache di server mereka
FROM runpod/base:0.6.0-cuda12.1.0

# Install ffmpeg (Python dan pip sudah bawaan dari RunPod)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install library pendukung aplikasi
RUN pip3 install runpod boto3 faster-whisper

COPY . /app
WORKDIR /app

CMD ["python3", "handler.py"]
