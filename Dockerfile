FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y \
    python3-pip \
    wget \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Install FFmpeg static (paling stabil)
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar xvf ffmpeg-release-amd64-static.tar.xz && \
    mv ffmpeg-*-static/ffmpeg /usr/local/bin/ && \
    mv ffmpeg-*-static/ffprobe /usr/local/bin/

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3", "handler.py"]
