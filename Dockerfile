FROM python:3.10-slim

# Install dasar saja
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Cuma install runpod dulu
RUN pip install --no-cache-dir runpod

COPY . .

CMD ["python3", "handler.py"]