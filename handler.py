import os
import re
import boto3
import runpod
from faster_whisper import WhisperModel
from supabase import create_client, Client

# Import fungsi otak AI
from analyzer import analyze_transcription 

# Load Credential R2
ENDPOINT_URL = os.environ.get("R2_ENDPOINT")
ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.environ.get("R2_BUCKET")

# Setup Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("LOG: Loading Model Whisper...")
model = WhisperModel("small", device="cuda", compute_type="float16")

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto"
)

def handler(event):
    print("--- LOG: HANDLER V28 (WHISPER + GEMINI + SUPABASE) ---")
    job_input = event.get("input", {})
    
    # Ambil job_id dan s3_key dari request
    job_id = job_input.get("job_id")
    s3_key = job_input.get("s3_key")

    if not job_id or not s3_key:
        return {"status": "error", "message": "job_id or s3_key missing"}

    # 1. Update status di Supabase jadi 'processing'
    try:
        supabase.table("jobs").update({"status": "processing"}).eq("id", job_id).execute()
    except Exception as e:
        print(f"LOG: Gagal update status ke processing - {e}")

    try:
        clean_name = re.sub(r'[^a-zA-Z0-9._-]', '_', s3_key)
        local_path = f"/tmp/{clean_name}"

        print(f"LOG: Downloading {s3_key} dari R2...")
        s3.download_file(BUCKET_NAME, s3_key, local_path)

        print(f"LOG: Transcribing Video...")
        segments, _ = model.transcribe(local_path, beam_size=5)
        transcription = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]

        # --- PROSES ANALISIS VIRAL ---
        print("LOG: Menganalisis momen viral dengan Gemini 2.5 Flash...")
        viral_clips_data = analyze_transcription(transcription)

        # Cleanup file lokal
        if os.path.exists(local_path): 
            os.remove(local_path)

        # 2. Update status di Supabase jadi 'done'
        supabase.table("jobs").update({
            "status": "done",
            "output_url": str(viral_clips_data)
        }).eq("id", job_id).execute()

        return {"status": "success", "viral_clips": viral_clips_data}

    except Exception as e:
        # 3. Update status di Supabase jadi 'failed' jika error
        print(f"LOG: Error pada proses - {e}")
        supabase.table("jobs").update({"status": "failed"}).eq("id", job_id).execute()
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})