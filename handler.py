cat << 'EOF' > handler.py
import runpod
import os
import yt_dlp
import uuid
from moviepy.editor import VideoFileClip
from supabase import create_client, Client

# --- CONFIGURATION SUPABASE ---
SUPABASE_URL = "https://dfqegfdehvpttslbzzjv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
BUCKET_NAME = "jagoan-videos"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def handler(job):
    job_input = job['input']
    video_url = job_input.get("video_url")
    
    if not video_url:
        return {"status": "error", "message": "Video URL tidak ditemukan!"}

    print(f"📥 Memulai eksekusi V7 untuk: {video_url}")
    
    temp_dir = "/tmp"
    unique_id = str(uuid.uuid4())[:8]
    download_path = os.path.join(temp_dir, f"raw_{unique_id}.mp4")
    hasil_path = os.path.join(temp_dir, f"clip_{unique_id}.mp4")
    remote_filename = f"jagoan_clip_{unique_id}.mp4"

    try:
        print("⏳ Mendownload video dari YouTube...")
        ydl_opts = {'format': 'best', 'outtmpl': download_path, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        print("✅ Download selesai!")

        print("✂️ Memotong video via FFMPEG...")
        clip = VideoFileClip(download_path).subclip(0, 5)
        clip.write_videofile(hasil_path, codec="libx264", audio_codec="aac", logger=None)
        clip.close()
        print("✅ Gunting video sukses!")

        print("🚀 Mengupload hasil asli ke Supabase Storage...")
        with open(hasil_path, 'rb') as f:
            supabase.storage.from_(BUCKET_NAME).upload(
                file=f,
                path=remote_filename,
                file_options={"content-type": "video/mp4"}
            )
        print("✅ Upload Supabase selesai!")

        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(remote_filename)

        # Bersih-bersih
        if os.path.exists(download_path): os.remove(download_path)
        if os.path.exists(hasil_path): os.remove(hasil_path)

        return {
            "status": "success",
            "message": "THE REAL SUCCESS! Video berhasil dipotong & di-upload!",
            "download_url": public_url
        }

    except Exception as e:
        if os.path.exists(download_path): os.remove(download_path)
        if os.path.exists(hasil_path): os.remove(hasil_path)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})
EOF