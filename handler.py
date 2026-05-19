import runpod
import os
import yt_dlp
import uuid
import whisper
from supabase import create_client, Client

# Koneksi Supabase
SUPABASE_URL = "https://dfqegfdehvpttslbzzjv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
BUCKET_NAME = "jagoan-videos"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
model = whisper.load_model("base")

def handler(job):
    job_input = job['input']
    video_url = job_input.get("video_url")
    
    if not video_url:
        return {"status": "error", "message": "Video URL tidak ditemukan!"}

    # 🔥 PROXY FRESH (SESI: qgCatZo0)
    PROXY_URL = 'http://bIl7z9TWKeuVbf59:NINysowUyUr96J7a_country-us_session-qgCatZo0_lifetime-30m@geo.iproyal.com:12321'
    
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = "/tmp"
    audio_path = os.path.join(temp_dir, f"audio_{unique_id}.m4a")
    hasil_path = os.path.join(temp_dir, f"clip_{unique_id}.mp4")
    remote_filename = f"jagoan_clip_{unique_id}.mp4"

    try:
        # FASE 1: DOWNLOAD AUDIO
        print("⏳ Fase 1: Mendownload Audio...")
        ydl_audio = {
            'format': 'bestaudio/best', 'outtmpl': audio_path, 'quiet': True,
            'proxy': PROXY_URL, 'extractor_args': {'youtube': {'player_client': ['tv']}},
            'geo_bypass': True, 'nocheckcertificate': True
        }
        with yt_dlp.YoutubeDL(ydl_audio) as ydl: ydl.download([video_url])
        
        # FASE 2: ANALISA AI
        print("🧠 Fase 2: Analisa AI Whisper...")
        result = model.transcribe(audio_path, word_timestamps=True)
        segments = result.get("segments", [])
        start_time = 0.0
        end_time = 45.0
        for seg in segments:
            if 30.0 <= seg["end"] <= 60.0: end_time = seg["end"]; break
            elif seg["end"] > 60.0: break
            end_time = seg["end"]
        
        # FASE 3: DOWNLOAD VIDEO (Format Fleksibel)
        print(f"🎬 Fase 3: Potong {start_time}s - {end_time}s...")
        ydl_video = {
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            'outtmpl': hasil_path, 'quiet': True, 'proxy': PROXY_URL,
            'extractor_args': {'youtube': {'player_client': ['tv']}},
            'geo_bypass': True, 'nocheckcertificate': True,
            'download_ranges': lambda info, ydl: [(start_time, end_time)],
            'force_keyframes_at_cuts': True
        }
        with yt_dlp.YoutubeDL(ydl_video) as ydl: ydl.download([video_url])

        # FASE 4: UPLOAD
        print("🚀 Fase 4: Uploading...")
        with open(hasil_path, 'rb') as f:
            supabase.storage.from_(BUCKET_NAME).upload(file=f, path=remote_filename)
        
        url = supabase.storage.from_(BUCKET_NAME).get_public_url(remote_filename)
        
        if os.path.exists(audio_path): os.remove(audio_path)
        if os.path.exists(hasil_path): os.remove(hasil_path)

        return {"status": "success", "url": url}

    except Exception as e:
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})
