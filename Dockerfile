# Image ini sudah berisi PyTorch dan CUDA, jadi tidak perlu install torch lagi
FROM runpod/pytorch:2.2.0-py3.10-cuda12.1.0-devel-ubuntu22.04

# Install sistem dependensi yang ringan saja
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install sisanya (tanpa torch, karena sudah ada di image)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler
COPY handler.py .

CMD ["python3", "-u", "handler.py"]
