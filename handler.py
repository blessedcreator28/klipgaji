import runpod
import os
import requests
import uuid
import whisper
import traceback
from supabase import create_client

# Inisialisasi
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
model = whisper.load_model("base")

def handler(job):
    try:
        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        if not video_url:
            return {"status": "error", "message": "No video_url provided"}

        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/video_{unique_id}.mp4"

        # 1. Download Video
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Transcribe
        result = model.transcribe(video_path, word_timestamps=True)
        
        # 3. Dummy Output untuk ngetes integrasi
        # Di sini lo bisa tambahin logika potong video pakai subprocess ffmpeg
        
        return {
            "status": "success", 
            "urls": [video_url], # Kembalikan link asal sebagai bukti sukses
            "transcription": result['text'][:100] # Tes kirim potongan teks
        }

    except Exception as e:
        return {
            "status": "error", 
            "message": str(e), 
            "traceback": traceback.format_exc()
        }

runpod.serverless.start({"handler": handler})
