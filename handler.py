import runpod
import os
import requests
import uuid
import whisper
import traceback # <-- Tambahan
from supabase import create_client

supabase = create_client("https://dfqegfdehvpttslbzzjv.supabase.co", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0")
model = whisper.load_model("base")

def handler(job):
    try:
        video_url = job['input'].get("video_url")
        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/video_{unique_id}.mp4"

        # Download
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # Transcribe
        result = model.transcribe(video_path, word_timestamps=True)
        
        # FFmpeg Check
        ffmpeg_check = os.system("ffmpeg -version")
        if ffmpeg_check != 0:
             return {"status": "error", "message": "FFMPEG GAGAL DIINSTALL DI SERVER!"}

        # Potong klip
        # ... (sisa logika pemotongan tetap sama)
        return {"status": "success", "urls": ["test"]} # Kita tes dulu simple

    except Exception as e:
        # Kirim error sedetail mungkin ke Streamlit
        return {"status": "error", "message": str(e) + "\n" + traceback.format_exc()}

runpod.serverless.start({"handler": handler})
