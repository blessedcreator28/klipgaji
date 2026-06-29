FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel

WORKDIR /app

# Menghapus file sampah yang mungkin mengganggu
RUN rm -f /main.py

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Memastikan Python menjalankan handler.py sebagai entrypoint utama
ENV RUNPOD_DEBUG_LEVEL=debug
CMD ["python", "handler.py"]