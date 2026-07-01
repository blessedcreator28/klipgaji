import os
import re
import boto3
import runpod
import subprocess
from faster_whisper import WhisperModel
from supabase import create_client, Client
from analyzer import analyze_transcription 

# Load Credential R2
ENDPOINT_URL = os.environ.get("R2_ENDPOINT")
PUBLIC_BUCKET_URL = "https://pub-7b62ff616edc4f6aa4a15d2442e2af87.r2.dev"
ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.environ.get("R2_BUCKET")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("LOG: Loading Model Whisper...")
model = WhisperModel("small", device="cuda", compute_type="float16")

s3 = boto3.client("s3", endpoint_url=ENDPOINT_URL, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name="auto")

def cut_and_upload(local_path, start, end, clip_index):
    output_filename = f"clip_{clip_index}.mp4"
    output_path = f"/tmp/{output_filename}"
    
    print(f"DEBUG: Memulai cutting clip_{clip_index} dari {start} ke {end} detik...")
    
    # Perintah FFmpeg
    duration = end - start
    try:
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(start), "-i", local_path, 
            "-t", str(duration), "-c:v", "libx264", "-c:a", "aac", output_path
        ], check=True)
        print(f"DEBUG: FFmpeg berhasil memotong clip_{clip_index}")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: FFmpeg gagal memotong clip_{clip_index}: {e}")
        return None
    
    # Upload ke R2
    print(f"DEBUG: Mengupload clip_{clip_index} ke R2...")
    s3.upload_file(output_path, BUCKET_NAME, output_filename, ExtraArgs={'ContentType': 'video/mp4'})
    os.remove(output_path)
    
    url = f"{PUBLIC_BUCKET_URL}/{output_filename}"
    print(f"DEBUG: Upload sukses, URL: {url}")
    return url

def handler(event):
    job_input = event.get("input", {})
    job_id = job_input.get("job_id")
    s3_key = job_input.get("s3_key")

    try:
        clean_name = re.sub(r'[^a-zA-Z0-9._-]', '_', s3_key)
        local_path = f"/tmp/{clean_name}"
        s3.download_file(BUCKET_NAME, s3_key, local_path)

        segments, _ = model.transcribe(local_path, beam_size=5)
        transcription = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
        viral_clips_data = analyze_transcription(transcription)

        final_clips = []
        for i, clip in enumerate(viral_clips_data):
            print(f"DEBUG: Memproses klip indeks {i}")
            clip_url = cut_and_upload(local_path, clip['start_time'], clip['end_time'], i)
            
            if clip_url:
                clip['clip_url'] = clip_url 
            else:
                clip['clip_url'] = "ERROR_CUTTING" # Flag kalau gagal
            
            final_clips.append(clip)

        if os.path.exists(local_path): os.remove(local_path)

        return {"status": "success", "viral_clips": {"clips": final_clips}}

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})