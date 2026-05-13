# Pake base image Python yang ringan
FROM python:3.10-slim

# Install tools video & font (WAJIB)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fontconfig \
    libass-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory di dalem container
WORKDIR /app

# Copy Font sakti lo ke dalem sistem Linux container
COPY TheBoldFont.ttf /usr/share/fonts/truetype/TheBoldFont.ttf
RUN fc-cache -f -v

# Copy requirements dan install library
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy kodingan mesin utama
COPY handler.py .

# Perintah buat jalanin server pas nyala
CMD [ "python", "-u", "handler.py" ]