import runpod
import os
import requests
import uuid
import traceback
import subprocess
import random
import whisper
from supabase import create_client

model = whisper.load_model("tiny") 

def handler(job):
    try:
        print("DEBUG: Handler started")
        supabase_url = "https://dfqegfdehvpttslbzzjv.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
        
        supabase = create_client(supabase_url, supabase_key)

        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        print(f"DEBUG: Input video_url: {video_url}")
        if not video_url: return {"status": "error", "message": "No video_url"}

        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        
        # Download Video
        print("DEBUG: Downloading video...")
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        print("DEBUG: Video downloaded")

        print("DEBUG: Starting transcription...")
        result = model.transcribe(video_path, language="id", word_timestamps=True)
        segments = result.get("segments", [])
        total_duration = segments[-1]["end"] if segments else 60
        print(f"DEBUG: Transcription done. Total duration: {total_duration}")
        
        clip_urls = []
        start_time = 15.0
        
        print("DEBUG: Entering clipping loop...")
        while start_time < (total_duration - 15.0) and len(clip_urls) < 5:
            output_path = f"/tmp/clip_{unique_id}_{len(clip_urls)}.mp4"
            print(f"DEBUG: Processing clip at {start_time}s")
            
            # Filter visual
            base_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:10"
            ffmpeg_cmd = ["ffmpeg", "-y", "-ss", str(start_time), "-t", "20", "-i", video_path, "-vf", base_filter, "-c:v", "libx264", "-c:a", "aac", output_path]
            
            subprocess.run(ffmpeg_cmd, check=True)
            print(f"DEBUG: FFmpeg done for clip {len(clip_urls)}")

            with open(output_path, "rb") as f:
                supabase.storage.from_("videos").upload(path=f"clip_{unique_id}_{len(clip_urls)}.mp4", file=f)
            print(f"DEBUG: Upload success for clip {len(clip_urls)}")
            
            clip_urls.append(supabase.storage.from_("videos").get_public_url(f"clip_{unique_id}_{len(clip_urls)}.mp4"))
            os.remove(output_path)
            start_time += 20.0

        if os.path.exists(video_path): os.remove(video_path)
        print("DEBUG: Handler finished successfully")
        return {"status": "success", "urls": clip_urls}

    except Exception as e:
        print(f"DEBUG: Error happened: {str(e)}")
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

runpod.serverless.start({"handler": handler})