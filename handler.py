import runpod
import os
import sys
import uuid
from moviepy.editor import VideoFileClip
from supabase import create_client, Client

# Import yt_dlp di awal
import yt_dlp

SUPABASE_URL = "https://dfqegfdehvpttslbzzjv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
BUCKET_NAME = "jagoan-videos"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def handler(job):
    # SENJATA PAMUNGKAS: Paksa robot update patch anti-bot terbaru saat runtime
    print("🔄 Memaksa update patch anti-bot yt-dlp ke versi paling gres...")
    os.system(f"{sys.executable} -m pip install --no-cache-dir --upgrade yt-dlp")
    
    # Reload library agar Python langsung membaca otak baru yang barusan di-download
    import importlib
    importlib.reload(yt_dlp)

    job_input = job['input']
    video_url = job_input.get("video_url")
    
    if not video_url:
        return {"status": "error", "message": "Video URL tidak ditemukan!"}

    print(f"📥 Memulai eksekusi UTUSAN FINAL untuk: {video_url}")
    
    temp_dir = "/tmp"
    unique_id = str(uuid.uuid4())[:8]
    download_path = os.path.join(temp_dir, f"raw_{unique_id}.mp4")
    hasil_path = os.path.join(temp_dir, f"clip_{unique_id}.mp4")
    remote_filename = f"jagoan_clip_{unique_id}.mp4"

    try:
        print("⏳ Mendownload video asli via Proxy Berbayar + Auto-Patch...")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': download_path,
            'noplaylist': True,
            'quiet': False,
            'no_warnings': False,
            
            # KUNCI PROXY BERBAYAR WEBSHARE LO
            'proxy': 'http://dipoveax:fjtpxd7e8buv@9.142.14.32:6688',
            
            # Penyamaran kombinasi client TV & Android
            'extractor_args': {
                'youtube': {
                    'player_client': ['tv', 'android'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'geo_bypass': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        print("✂️ Memotong 5 detik...")
        clip = VideoFileClip(download_path).subclip(0, 5)
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
            "message": "🔥 BOOM! KELAR VIN! Video asli sukses dipotong dan di-upload!",
            "download_url": public_url
        }

    except Exception as e:
        if os.path.exists(download_path): os.remove(download_path)
        if os.path.exists(hasil_path): os.remove(hasil_path)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})
