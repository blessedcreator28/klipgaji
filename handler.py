import runpod
import os
import requests
import uuid
import traceback
import subprocess
import random
import whisper
from supabase import create_client

# Load model di luar handler biar gak loading tiap ada request (Cold Start lebih cepat)
# Gunakan "tiny" dulu kalau "small" terlalu berat di RAM
model = whisper.load_model("tiny") 

def handler(job):
    try:
        supabase_url = "https://dfqegfdehvpttslbzzjv.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
        
        supabase = create_client(supabase_url, supabase_key)

        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        if not video_url: return {"status": "error", "message": "No video_url"}

        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        font_path = "/tmp/theboldfont.ttf"
        
        # Download Font
        if not os.path.exists(font_path):
            r_font = requests.get("https://raw.githubusercontent.com/LonamiWebs/8-Bally-Pool/master/src/Resources/Original/font/theboldfont.ttf")
            with open(font_path, 'wb') as f: f.write(r_font.content)

        # Download Video
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)

        result = model.transcribe(video_path, language="id", word_timestamps=True)
        segments = result.get("segments", [])
        total_duration = segments[-1]["end"] if segments else 60
        
        clip_urls = []
        start_time = 15.0
        
        # Limit ke 5 klip dulu buat tes agar gak kelamaan
        while start_time < (total_duration - 15.0) and len(clip_urls) < 5:
            output_path = f"/tmp/clip_{unique_id}_{len(clip_urls)}.mp4"
            
            # Filter visual
            base_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:10"
            ffmpeg_cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", "20", "-i", video_path, "-vf", base_filter, "-c:v", "libx264", "-c:a", "aac", output_path]
            subprocess.run(ffmpeg_cmd, check=True)

            with open(output_path, "rb") as f:
                supabase.storage.from_("videos").upload(path=f"clip_{unique_id}_{len(clip_urls)}.mp4", file=f)
            
            clip_urls.append(supabase.storage.from_("videos").get_public_url(f"clip_{unique_id}_{len(clip_urls)}.mp4"))
            os.remove(output_path)
            start_time += 20.0

        if os.path.exists(video_path): os.remove(video_path)
        return {"status": "success", "urls": clip_urls}

    except Exception as e:
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

runpod.serverless.start({"handler": handler})