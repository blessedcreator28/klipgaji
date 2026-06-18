FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Install sistem dependencies yang krusial
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    ffmpeg \
    libx264-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python packages
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy sisa project
COPY . .

# Set entry point
CMD ["python3", "handler.py"]
