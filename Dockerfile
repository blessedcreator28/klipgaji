FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

# Paksa instalasi jalan tanpa nanya lokasi
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Jakarta

RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "handler.py"]