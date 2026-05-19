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

# Load model di luar handler agar di-download SAAT INITIALIZING (Masa Biru)
print("🧠 Memuat model AI Whisper ke dalam memori GPU...")
model = whisper.load_model("base")

def handler(job):
    job_input = job['input']
    video_url = job_input.get("video_url")
    
    if not video_url:
        return {"status": "error", "message": "Video URL tidak ditemukan!"}

    print(f"📥 Memulai eksekusi JAGOAN CLIPPER SMART CUT untuk: {video_url}")
    
    temp_dir = "/tmp"
    unique_id = str(uuid.uuid4())[:8]
    download_path = os.path.join(temp_dir, f"raw_{unique_id}.mp4")
    hasil_path = os.path.join(temp_dir, f"clip_{unique_id}.mp4")
    remote_filename = f"jagoan_smart_clip_{unique_id}.mp4"

    try:
        # 1. DOWNLOAD VIDEO VIA PROXY WEBSHARE
        print("⏳ Mendownload video asli...")
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': download_path,
            'noplaylist': True,
            'quiet': True,
            # Kunci proxy berbayar lo
            'proxy': 'http://dipoveax:fjtpxd7e8buv@9.142.14.32:6688',
            
            # KUNCI MATI SMART TV ONLY (Tanpa campuran android/web penimbul bot)
            'extractor_args': {
                'youtube': {
                    'player_client': ['tv'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'geo_bypass': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # 2. PROSES AI WHISPER
        print("🧠 AI Whisper mulai menganalisis audio pembicaraan...")
        result = model.transcribe(download_path, word_timestamps=True)
        
        # 3. LOGIKA SMART CUTTING (30-60 Detik Tanpa Potong Kalimat)
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

        print(f"🎬 Hasil Analisis AI: Memotong dari detik {start_time} sampai {end_time}")

        # 4. EKSEKUSI PEMOTONGAN VIDEO
        clip = VideoFileClip(download_path).subclip(start_time, end_time)
        clip.write_videofile(hasil_path, codec="libx264", audio_codec="aac", logger=None)
        clip.close()

        # 5. UPLOAD KE SUPABASE
        print("🚀 Uploading hasil potongan pintar ke Supabase...")
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
            "message": "🔥 BOOM! Smart Cutting Berhasil, Vin! Pembicaraan tidak terputus!",
            "download_url": public_url,
            "text_detected": result.get("text", "")[:200] + "..."
        }

    except Exception as e:
        if os.path.exists(download_path): os.remove(download_path)
        if os.path.exists(hasil_path): os.remove(hasil_path)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})
