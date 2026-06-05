FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y python3-pip ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Menambah layer baru untuk memaksa rebuild
ENV REFRESHED_AT=2026-06-05-v1
COPY . .

# ENTRYPOINT biasanya lebih stabil daripada CMD
ENTRYPOINT ["python3", "handler.py"]