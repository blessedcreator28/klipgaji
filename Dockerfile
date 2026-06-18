FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3-pip ffmpeg && rm -rf /var/lib/apt/lists/*

# Kita inject langsung library CUDA & cuDNN ke dalam pip Python
RUN pip3 install runpod boto3 faster-whisper nvidia-cublas-cu12 nvidia-cudnn-cu12

COPY . /app
WORKDIR /app

CMD ["python3", "handler.py"]
