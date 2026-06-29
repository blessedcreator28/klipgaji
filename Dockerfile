FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel

WORKDIR /app

# Hapus file main.py bawaan biar sistem terpaksa pakai handler.py kita
RUN rm -f /main.py

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pastikan entrypoint-nya langsung ke handler.py
CMD ["python", "handler.py"]