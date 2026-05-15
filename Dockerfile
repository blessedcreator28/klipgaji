FROM python:3.10-slim

# Install ffmpeg (Wajib buat moviepy)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy daftar alat dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua kodingan lo
COPY . .

# Jalankan mesin
CMD ["python", "-u", "handler.py"]
