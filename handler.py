import runpod
import os
import yt_dlp
import uuid
import whisper
import subprocess
from supabase import create_client, Client

# Koneksi Supabase
supabase = create_client("https://dfqegfdehvpttslbzzjv.supabase.co", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0")

# Load model AI (hanya sekali saat worker start)
model = whisper.load_model("base")

def handler(job):
    job_input = job['input']
    video_url = job_input.get("video_url")
    # 🔥 GANTI DENGAN LINK PROXY FRESH LO (Sesi kyVEVYLU)
    PROXY_URL = 'http://bIl7z9TWKeuVbf59:NINysowUyUr96J7a_country-us_session-kyVEVYLU_lifetime-30m@geo.iproyal.com:12321'
    
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = "/tmp"
    audio_path = os.path.join(temp_dir, f"audio_{unique_id}.m4a")
    hasil_path = os.path.join(temp_dir, f"clip_{unique_id}.mp4")
    remote_filename = f"jagoan_clip_{unique_id}.mp4"

    try:
        # 1. Download Audio saja buat Whisper (Cepat & Ringan)
        ydl_audio = {
            'format': 'bestaudio[ext=m4a]', 'outtmpl': audio_path, 'quiet': True,
            'proxy': PROXY_URL, 'extractor_args': {'youtube': {'player_client': ['tv']}}
        }
        with yt_dlp.YoutubeDL(ydl_audio) as ydl: ydl.download([video_url])
        
        # 2. Whisper Analysis
        result = model.transcribe(audio_path, word_timestamps=True)
        start_time = 0.0
        end_time = 45.0 # default
        for seg in result.get("segments", []):
            if 30.0 <= seg["end"] <= 60.0: end_time = seg["end"]; break
        
        # 3. Smart Download & Cut (Instan)
        ydl_video = {
            'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]',
            'outtmpl': hasil_path, 'quiet': True, 'proxy': PROXY_URL,
            'extractor_args': {'youtube': {'player_client': ['tv']}},
            'download_ranges': lambda info, ydl: [(start_time, end_time)],
            'force_keyframes_at_cuts': True
        }
        with yt_dlp.YoutubeDL(ydl_video) as ydl: ydl.download([video_url])

        # 4. Upload Supabase
        with open(hasil_path, 'rb') as f:
            supabase.storage.from_("jagoan-videos").upload(file=f, path=remote_filename)
        
        url = supabase.storage.from_("jagoan-videos").get_public_url(remote_filename)
        return {"status": "success", "url": url}

    except Exception as e:
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})
