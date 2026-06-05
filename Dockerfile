FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Install tools yang dibutuhkan
RUN apt-get update && apt-get install -y python3-pip ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# PRE-DOWNLOAD MODEL (Ini kuncinya, dia bakal simpen model di image)
RUN python3 -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

COPY . .

CMD ["python3", "handler.py"]