FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel

# Pindah ke folder baru biar gak kena cache folder lama
WORKDIR /app_v2

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua file ke folder baru
COPY . .

# Pastikan handler.py ada di sana
ENV REFRESHED_AT=2026-06-29_15_30

# Jalankan handler dari lokasi baru
CMD ["python", "handler.py"]