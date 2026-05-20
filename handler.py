import runpod
import os
import requests
import uuid
import whisper
from supabase import create_client

# Konfigurasi Supabase
supabase = create_client("https://dfqegfdehvpttslbzzjv.supabase.co", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0")
model = whisper.load_model("base")

def handler(job):
    video_url = job['input'].get("video_url")
    
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = "/tmp"
    video_path = os.path.join(temp_dir, f"video_{unique_id}.mp4")

    try:
        # 1. TEMBUSIN YOUTUBE PAKE COBALT API
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": video_url,
            "videoQuality": "720" # Dibatasi 720p biar proses AI lebih ngebut
        }
        
        # Minta direct link ke Cobalt
        cobalt_res = requests.post("https://api.cobalt.tools/api/json", json=payload, headers=headers)
        cobalt_data = cobalt_res.json()
        
        if cobalt_data.get("status") == "error":
            return {"status": "manual_upload_needed", "message": "Video ini terproteksi hak cipta tinggi. Silakan upload file manual."}
            
        direct_url = cobalt_data.get("url")
        if not direct_url:
            return {"status": "error", "message": "Gagal mendapatkan akses video dari YouTube."}

        # 2. DOWNLOAD FILE MENTAH (Sangat Cepat, Bebas Blokir)
        r = requests.get(direct_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # 3. TRANSCRIBE (1x Proses)
        result = model.transcribe(video_path, word_timestamps=True)
        
        # 4. SMART FILTER: Ambil Top 15 segment (15-60 detik)
        segments = [s for s in result['segments'] if 15 <= (s['end'] - s['start']) <= 60]
        top_segments = sorted(segments, key=lambda x: (x['end'] - x['start']), reverse=True)[:15]
        
        # 5. PROSES KLIP (FFmpeg Cut & Upload)
        processed_urls = []
        for i, seg in enumerate(top_segments):
            clip_path = f"/tmp/clip_{unique_id}_{i}.mp4"
            
            # Potong video
            os.system(f"ffmpeg -i {video_path} -ss {seg['start']} -to {seg['end']} -c copy {clip_path} -y")
            
            # Upload ke Supabase
            with open(clip_path, 'rb') as f:
                supabase.storage.from_("jagoan-videos").upload(file=f, path=f"clip_{unique_id}_{i}.mp4")
            
            url = supabase.storage.from_("jagoan-videos").get_public_url(f"clip_{unique_id}_{i}.mp4")
            processed_urls.append(url)
            os.remove(clip_path)

        return {"status": "success", "urls": processed_urls}

    except Exception as e:
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})
