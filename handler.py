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
    """Memotong video dan mengupload ke R2"""
    output_filename = f"clip_{clip_index}.mp4"
    output_path = f"/tmp/{output_filename}"
    
    # Perintah FFmpeg untuk memotong
    duration = end - start
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(start), "-i", local_path, 
        "-t", str(duration), "-c", "copy", output_path
    ], check=True)
    
    # Upload ke R2
    s3.upload_file(output_path, BUCKET_NAME, output_filename)
    # Hapus file lokal
    os.remove(output_path)
    
    # Return URL (Ganti dengan URL publik R2 lo)
    return f"https://pub-your-r2-url.r2.dev/{output_filename}"

def handler(event):
    print("--- LOG: HANDLER V29 (CUTTING ENABLED) ---")
    job_input = event.get("input", {})
    job_id = job_input.get("job_id")
    s3_key = job_input.get("s3_key")

    if not job_id or not s3_key:
        return {"status": "error", "message": "job_id or s3_key missing"}

    try:
        clean_name = re.sub(r'[^a-zA-Z0-9._-]', '_', s3_key)
        local_path = f"/tmp/{clean_name}"
        s3.download_file(BUCKET_NAME, s3_key, local_path)

        # Transcribe
        segments, _ = model.transcribe(local_path, beam_size=5)
        transcription = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]

        # Analisis Viral
        print("LOG: Menganalisis momen viral...")
        viral_clips_data = analyze_transcription(transcription)

        # PROSES CUTTING & UPLOAD
        final_clips = []
        for i, clip in enumerate(viral_clips_data):
            print(f"LOG: Memproses klip {i}...")
            clip_url = cut_and_upload(local_path, clip['start_time'], clip['end_time'], i)
            clip['clip_url'] = clip_url # Masukkan link download ke data
            final_clips.append(clip)

        if os.path.exists(local_path): os.remove(local_path)

        supabase.table("jobs").update({
            "status": "done",
            "output_url": str(final_clips)
        }).eq("id", job_id).execute()

        return {"status": "success", "viral_clips": {"clips": final_clips}}

    except Exception as e:
        print(f"LOG: Error - {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})