import runpod
import os
import uuid
import subprocess
import whisper
import boto3
from supabase import create_client

# Cek apakah kunci ada sebelum mulai (biar gak crash tiba-tiba)
required_envs = ['R2_ENDPOINT', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'R2_BUCKET']
for env in required_envs:
    if env not in os.environ:
        raise Exception(f"MISSING ENV VAR: {env}")

# Inisialisasi R2
s3 = boto3.client('s3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name='auto'
)

print("🔥 MEMANASKAN MESIN: R2 Online & Ready!")
model = whisper.load_model("small")

# ... (Fungsi generate_mrbeast_subs sama, taruh di sini) ...
def generate_mrbeast_subs(words, clip_start, ass_path):
    # (Kode fungsi ini tetap sama, jangan diubah)
    # ... pastikan indentasi benar ...
    pass

def handler(job):
    try:
        supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
        job_input = job.get('input', {})
        video_url = job_input.get('video_url') # Ini URL r2.dev (publik)
        
        # Ekstrak filename dari URL buat download
        filename = video_url.split('/')[-1]
        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        audio_path = f"/tmp/audio_{unique_id}.wav"
        
        # DOWNLOAD PAKE BOTO3 (LEBIH STABIL)
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        print("✅ Download dari R2 Sukses!")

        # ... (Sisa logika ffmpeg & clipping tetap sama) ...
        # (Lanjutkan render klip, lalu upload balik pake s3.upload_fileobj)
        
        return {"status": "success", "message": "Done"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})