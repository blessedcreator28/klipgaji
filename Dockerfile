FROM runpod/pytorch:2.2.0-py3.10-cuda12.1.0-devel-ubuntu22.04

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler
COPY handler.py .

CMD ["python3", "-u", "handler.py"]
