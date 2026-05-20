# Menggunakan base image resmi dari RunPod yang stabil
FROM runpod/base:0.4.0-cuda12.1.0

# Install dependencies sistem
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler dan script
COPY handler.py .

# Jalankan handler
CMD ["python3", "-u", "handler.py"]
