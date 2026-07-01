# Gunakan image resmi NVIDIA
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Install python dan dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Buat folder kerja
WORKDIR /app

# Install library Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir google-generativeai

# Copy source code ke /app
COPY . .

# Jalankan dari folder /app
CMD ["python3", "handler.py"]