FROM runpod/base:0.4.0-cuda12.1.0

# Install system dependencies (FFmpeg & Git wajib buat Whisper)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch dengan index yang benar (INI KUNCI BIAR GAK CRASH)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY handler.py .

CMD ["python3", "-u", "handler.py"]
