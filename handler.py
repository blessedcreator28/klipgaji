import runpod
import os
import requests
import uuid
import traceback
import subprocess
import random

def handler(job):
    try:
        import whisper
        from supabase import create_client
        
        # Key Supabase tertanam
        supabase_url = "https://dfqegfdehvpttslbzzjv.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"

        supabase = create_client(supabase_url, supabase_key)
        model = whisper.load_model("base")

        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        
        if not video_url:
            return {"status": "error", "message": "No video_url provided"}

        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        output_filename = f"final_{unique_id}.mp4"
        output_path = f"/tmp/{output_filename}"

        # 1. Download Video
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Transcribe & Durasi Random
        result = model.transcribe(video_path)
        target_dur = random.randint(30, 60)
        
        # 3. Pembersihan Teks untuk FFmpeg
        raw_text = result.get('text', '')[:60].strip()
        # Buang tanda kutip dan titik dua yang bisa bikin FFmpeg crash
        safe_text = raw_text.replace("'", "").replace('"', '').replace(':', '').replace('\n', ' ') + "..."
        
        # 4. FFMPEG Proses (Portrait, Blur Background, Auto Caption)
        # Pisahkan layer dengan jelas biar tidak bentrok
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:10[bg];"
            "[0:v]scale=1080:-2[fg];"
            f"[bg][fg]overlay=0:(H-h)/2[merged];"
            f"[merged]drawtext=text='{safe_text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-300:box=1:boxcolor=black@0.5:boxborderw=10"
        )
        
        ffmpeg_cmd = [
            "ffmpeg", "-y", 
            "-ss", "00:00:15", "-t", str(target_dur), 
            "-i", video_path,
            "-filter_complex", filter_complex,
            "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", 
            output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # 5. Upload ke Supabase
        with open(output_path, "rb") as f:
            supabase.storage.from_("videos").upload(path=output_filename, file=f)
        
        clip_url = supabase.storage.from_("videos").get_public_url(output_filename)

        os.remove(video_path)
        os.remove(output_path)

        return {"status": "success", "urls": [clip_url]}

    except Exception as e:
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

runpod.serverless.start({"handler": handler})