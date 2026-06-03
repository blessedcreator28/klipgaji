# Base image yang ringan dan sudah ada CUDA/PyTorch
FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel

# Install dependencies sistem
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 && \
    pip install --upgrade pip && \
    pip install runpod openai-whisper supabase requests

# Copy handler.py ke dalam container
COPY handler.py .

# Jalankan handler
CMD ["python3", "handler.py"]