import runpod
import os
import yt_dlp
import uuid
import whisper
from moviepy.editor import VideoFileClip
from supabase import create_client, Client

SUPABASE_URL = "https://dfqegfdehvpttslbzzjv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
BUCKET_NAME = "jagoan-videos"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🧠 Memuat model AI Whisper ke dalam memori GPU...")
model = whisper.load_model("base")

def handler(job):
    job_input = job['input']
    video_url = job_input.get("video_url")
    
    if not video_url:
        return {"status": "error", "message": "Video URL tidak ditemukan!"}

    print(f"📥 Memulai eksekusi SAAS JAGOAN CLIPPER untuk: {video_url}")
    
    temp_dir = "/tmp"
    unique_id = str(uuid.uuid4())[:8]
    download_path = os.path.join(temp_dir, f"raw_{unique_id}.mp4")
    hasil_path = os.path.join(temp_dir, f"clip_{unique_id}.mp4")
    remote_filename = f"jagoan_smart_clip_{unique_id}.mp4"

    try:
        print("⏳ Mendownload video asli dengan Residential Proxy...")
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': download_path,
            'noplaylist': True,
            'quiet': True,
            'cachedir': False,
            
            # 🔥 PROXY PRESISI 100% HASIL COPAS (Udah gue ekstrak dari tulisan curl lo)
            'proxy': 'http://bIl7z9TWKeuVbf59:NINysowUyUr96J7a_country-us_session-tdeP3weK_lifetime-30m@geo.iproyal.com:12321',
            
            'extractor_args': {
                'youtube': {
                    'player_client': ['tv', 'web_creator'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'geo_bypass': True,
            'nocheckcertificate': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        print("🧠 AI Whisper mulai menganalisis audio pembicaraan...")
        result = model.transcribe(download_path, word_timestamps=True)
        
        print("✂️ Menghitung titik potong aman...")
        segments = result.get("segments", [])
        
        start_time = 0.0
        end_time = 45.0
        
        for seg in segments:
            if 30.0 <= seg["end"] <= 60.0:
                end_time = seg["end"]
                break
            elif seg["end"] > 60.0:
                break
            end_time = seg["end"]

        print(f"🎬 Memotong dari detik {start_time} sampai {end_time}")

        clip = VideoFileClip(download_path).subclip(start_time, end_time)
        clip.write_videofile(hasil_path, codec="libx264", audio_codec="aac", logger=None)
        clip.close()

        print("🚀 Uploading ke Supabase...")
        with open(hasil_path, 'rb') as f:
            supabase.storage.from_(BUCKET_NAME).upload(
                file=f,
                path=remote_filename,
                file_options={"content-type": "video/mp4"}
            )

        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(remote_filename)

        if os.path.exists(download_path): os.remove(download_path)
        if os.path.exists(hasil_path): os.remove(hasil_path)

        return {
            "status": "success",
            "message": "🔥 TUNTAS VIN! Residential Proxy nembus tanpa ampun!",
            "download_url": public_url,
            "text_detected": result.get("text", "")[:200] + "..."
        }

    except Exception as e:
        if os.path.exists(download_path): os.remove(download_path)
        if os.path.exists(hasil_path): os.remove(hasil_path)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})
