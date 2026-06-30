# Gunakan image resmi NVIDIA yang sudah include semua library CUDA
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Install python dan dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install library Python dari requirements.txt
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install google-genai secara eksplisit untuk memastikan library "otak" terpasang
RUN pip3 install --no-cache-dir google-genai

# Copy handler dan analyzer (otak AI) ke dalam container
COPY handler.py .
COPY analyzer.py .

# Jalankan
CMD ["python3", "handler.py"]