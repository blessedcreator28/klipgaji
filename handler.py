import runpod
import os
import requests
import uuid
import whisper
from supabase import create_client

supabase = create_client("https://dfqegfdehvpttslbzzjv.supabase.co", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0")
model = whisper.load_model("base")

def handler(job):
    print("JOB STARTED: Memulai proses...")
    video_url = job['input'].get("video_url")
    unique_id = str(uuid.uuid4())[:8]
    video_path = f"/tmp/video_{unique_id}.mp4"

    try:
        print(f"DOWNLOADING: {video_url}")
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("TRANSCRIBING: Membedah audio dengan AI...")
        result = model.transcribe(video_path, word_timestamps=True)
        
        print("PROCESSING: Memotong klip...")
        segments = [s for s in result['segments'] if 15 <= (s['end'] - s['start']) <= 60]
        top_segments = sorted(segments, key=lambda x: (x['end'] - x['start']), reverse=True)[:3] # Ambil 3 aja biar cepat
        
        processed_urls = []
        for i, seg in enumerate(top_segments):
            clip_path = f"/tmp/clip_{unique_id}_{i}.mp4"
            os.system(f"ffmpeg -i {video_path} -ss {seg['start']} -to {seg['end']} -c copy {clip_path} -y")
            
            with open(clip_path, 'rb') as f:
                supabase.storage.from_("jagoan-videos").upload(file=f, path=f"clip_{unique_id}_{i}.mp4")
            processed_urls.append(supabase.storage.from_("jagoan-videos").get_public_url(f"clip_{unique_id}_{i}.mp4"))
            os.remove(clip_path)

        os.remove(video_path)
        print("SUCCESS: Proses selesai.")
        return {"status": "success", "urls": processed_urls}

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})
