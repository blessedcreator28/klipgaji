import runpod
import os
import yt_dlp
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
        # 1. DOWNLOAD (Clean & Simple)
        ydl_opts = {
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            'outtmpl': video_path,
            'quiet': True,
            'nocheckcertificate': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # 2. TRANSCRIBE (1x Proses saja)
        result = model.transcribe(video_path, word_timestamps=True)
        
        # 3. SMART FILTER: Ambil Top 15 segment (15-60 detik)
        segments = [s for s in result['segments'] if 15 <= (s['end'] - s['start']) <= 60]
        top_segments = sorted(segments, key=lambda x: (x['end'] - x['start']), reverse=True)[:15]
        
        # 4. PROSES KLIP
        processed_urls = []
        for i, seg in enumerate(top_segments):
            clip_path = f"/tmp/clip_{unique_id}_{i}.mp4"
            # FFmpeg cut
            os.system(f"ffmpeg -i {video_path} -ss {seg['start']} -to {seg['end']} -c copy {clip_path} -y")
            
            # Upload ke Supabase
            with open(clip_path, 'rb') as f:
                supabase.storage.from_("jagoan-videos").upload(file=f, path=f"clip_{unique_id}_{i}.mp4")
            
            url = supabase.storage.from_("jagoan-videos").get_public_url(f"clip_{unique_id}_{i}.mp4")
            processed_urls.append(url)
            os.remove(clip_path)

        return {"status": "success", "urls": processed_urls}

    except Exception as e:
        error_msg = str(e)
        if "Sign in" in error_msg or "DRM" in error_msg or "private" in error_msg:
            return {"status": "manual_upload_needed", "message": "Video ini terproteksi/butuh sign-in. Silakan upload file manual."}
        return {"status": "error", "message": error_msg}

runpod.serverless.start({"handler": handler})
