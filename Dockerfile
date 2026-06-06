FROM python:3.10

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install --no-cache-dir runpod

COPY . .

# DEBUG MODE: Kita listing file dulu biar kelihatan isi folder /app
CMD ["/bin/bash", "-c", "ls -la /app && python /app/handler.py"]