FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Jakarta

RUN apt-get update && apt-get install -y \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- BARIS SAKTI INI YANG BIKIN CEPET ---
# Mendownload model whisper 'small' saat build agar tidak download saat runtime
RUN python3 -c "import whisper; whisper.load_model('small')"
# ----------------------------------------

COPY . .

CMD ["python3", "handler.py"]