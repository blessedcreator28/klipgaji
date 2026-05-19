import runpod
import os
import yt_dlp
import uuid
import whisper
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

    print(f"📥 Memulai eksekusi SAAS JAGOAN CLIPPER (Smart Partial) untuk: {video_url}")
    
    temp_dir = "/tmp"
    unique_id = str(uuid.uuid4())[:8]
    audio_path = os.path.join(temp_dir, f"audio_{unique_id}.m4a")
    hasil_path = os.path.join(temp_dir, f"clip_{unique_id}.mp4")
    remote_filename = f"jagoan_smart_clip_{unique_id}.mp4"
    
    # 🔥 GANTI DENGAN LINK PROXY IPROYAL LO YANG PALING BARU (SESI FRESH)
    PROXY_URL = 'PROXY_BARU_LO_DI_SINI'

    try:
        # ==========================================
        # FASE 1: SEDOT AUDIO SAJA (Super Kilat)
        # ==========================================
        print("⏳ Fase 1: Mendownload Audio saja...")
        audio_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'outtmpl': audio_path,
            'noplaylist': True,
            'quiet': True,
            'cachedir': False,
            'proxy': PROXY_URL,
            'extractor_args': {'youtube': {'player_client': ['tv']}},
            'geo_bypass': True,
            'nocheckcertificate': True
        }
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.download([video_url])

        # ==========================================
        # FASE 2: ANALISA AI WHISPER
        # ==========================================
        print("🧠 Fase 2: AI Whisper menganalisis timestamps...")
        result = model.transcribe(audio_path, word_timestamps=True)
        
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

        print(f"🎬 Hasil AI: Potongan viral dari detik {start_time} sampai {end_time}")

        # ==========================================
        # FASE 3: SMART DOWNLOAD VIDEO (Langsung Potong dari Youtube)
        # ==========================================
        print("🚀 Fase 3: Smart Download Video! Hanya menyedot potongan klip...")
        video_opts = {
            'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
            'outtmpl': hasil_path,
            'noplaylist': True,
            'quiet': True,
            'cachedir': False,
            'proxy': PROXY_URL,
            'extractor_args': {'youtube': {'player_client': ['tv']}},
            'geo_bypass': True,
            'nocheckcertificate': True,
            
            # FITUR SHORTCUT DEWA: Jangan download full, ambil rentang waktunya aja!
            'download_ranges': lambda info, ydl: [(start_time, end_time)],
            'force_keyframes_at_cuts': True
        }
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            ydl.download([video_url])

        # ==========================================
        # FASE 4: UPLOAD KE SUPABASE
        # ==========================================
        print("☁️ Fase 4: Uploading ke Supabase...")
        with open(hasil_path, 'rb') as f:
            supabase.storage.from_(BUCKET_NAME).upload(
                file=f,
                path=remote_filename,
                file_options={"content-type": "video/mp4"}
            )

        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(remote_filename)

        # BERSIH-BERSIH SERVER
        if os.path.exists(audio_path): os.remove(audio_path)
        if os.path.exists(hasil_path): os.remove(hasil_path)

        return {
            "status": "success",
            "message": "🔥 TUNTAS VIN! Arsitektur Smart Partial sukses bypass Timeout!",
            "download_url": public_url,
            "text_detected": result.get("text", "")[:200] + "..."
        }

    except Exception as e:
        if os.path.exists(audio_path): os.remove(audio_path)
        if os.path.exists(hasil_path): os.remove(hasil_path)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})
