import runpod
import os
import requests
import uuid
import whisper
from supabase import create_client

# Konfigurasi Supabase
supabase_url = "https://dfqegfdehvpttslbzzjv.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
supabase = create_client(supabase_url, supabase_key)

# Load model Whisper (Base untuk kecepatan & akurasi optimal)
model = whisper.load_model("base")

def handler(job):
    # Sekarang video_url adalah link file mentah yang 100% aman
    video_url = job['input'].get("video_url") 
    
    if not video_url:
        return {"status": "error", "message": "Video URL tidak ditemukan."}

    unique_id = str(uuid.uuid4())[:8]
    temp_dir = "/tmp"
    video_path = os.path.join(temp_dir, f"video_{unique_id}.mp4")

    try:
        # 1. DOWNLOAD FILE MENTAH (Sangat Cepat)
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. PROSES TRANSCRIBE AI
        result = model.transcribe(video_path, word_timestamps=True)
        
        # 3. SMART FILTER: Ambil Top 15 segment (15-60 detik)
        segments = [s for s in result['segments'] if 15 <= (s['end'] - s['start']) <= 60]
        top_segments = sorted(segments, key=lambda x: (x['end'] - x['start']), reverse=True)[:15]
        
        # 4. PROSES KLIP (FFmpeg Cut & Upload ke Supabase)
        processed_urls = []
        for i, seg in enumerate(top_segments):
            clip_path = f"/tmp/clip_{unique_id}_{i}.mp4"
            
            # Potong video
            os.system(f"ffmpeg -i {video_path} -ss {seg['start']} -to {seg['end']} -c copy {clip_path} -y")
            
            # Upload ke bucket "jagoan-videos"
            file_name = f"clip_{unique_id}_{i}.mp4"
            with open(clip_path, 'rb') as f:
                supabase.storage.from_("jagoan-videos").upload(file=f, path=file_name)
            
            # Ambil public URL
            url = supabase.storage.from_("jagoan-videos").get_public_url(file_name)
            processed_urls.append(url)
            
            # Bersihkan file sementara
            os.remove(clip_path)

        os.remove(video_path) # Bersihkan file utama

        return {"status": "success", "urls": processed_urls}

    except Exception as e:
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})
