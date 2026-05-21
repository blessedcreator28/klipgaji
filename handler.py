import runpod
import os
import requests
import uuid
import traceback
import subprocess

def handler(job):
    try:
        import whisper
        from supabase import create_client
        
        # URL & Key langsung ditempel di sini biar ga ribet
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
        output_filename = f"clip_{unique_id}.mp4"
        output_path = f"/tmp/{output_filename}"

        # 1. Download Video
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Transcribe
        result = model.transcribe(video_path, word_timestamps=True)
        
        # 3. Proses Potong Video (Ambil 10 detik pertama)
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", video_path, 
            "-ss", "00:00:00", "-t", "00:00:10", 
            "-c:v", "libx264", "-c:a", "aac", output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # 4. Upload Hasil Potongan ke Supabase
        with open(output_path, "rb") as f:
            supabase.storage.from_("videos").upload(
                path=output_filename,
                file=f,
                file_options={"content-type": "video/mp4"}
            )
        
        clip_url = supabase.storage.from_("videos").get_public_url(output_filename)

        # Bersihkan file sampah di GPU
        os.remove(video_path)
        os.remove(output_path)

        return {
            "status": "success", 
            "urls": [clip_url],
            "transcription": result['text'][:100] + "..."
        }

    except Exception as e:
        return {
            "status": "error", 
            "message": str(e), 
            "traceback": traceback.format_exc()
        }

runpod.serverless.start({"handler": handler})