import runpod
import os
import uuid
import subprocess
import whisper
import boto3
from supabase import create_client

# Cek ketersediaan Environment Variables
required_envs = ['R2_ENDPOINT', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'R2_BUCKET', 'SUPABASE_URL', 'SUPABASE_KEY']
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

# LOAD MODEL DARI LOKAL (Gak pake download internet lagi)
print("🔥 MEMANASKAN MESIN: Loading Model dari /app/models...")
model = whisper.load_model('small', download_root='/app/models')
print("✅ Model AI Siap!")

def generate_mrbeast_subs(words, clip_start, ass_path):
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: MrBeast,Arial,130,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,10,5,2,10,10,600,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def format_time(seconds):
        h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = seconds % 60
        return f"{h:01d}:{m:02d}:{s:05.2f}"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        for w in words:
            start_t = max(0, w['start'] - clip_start); end_t = max(0, w['end'] - clip_start)
            if end_t <= 0: continue
            text = w['word'].strip().upper()
            f.write(f"Dialogue: 0,{format_time(start_t)},{format_time(end_t)},MrBeast,,0,0,0,,{text}\n")

def handler(job):
    try:
        supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        filename = video_url.split('/')[-1]
        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        audio_path = f"/tmp/audio_{unique_id}.wav"
        
        # Download dari R2
        print(f"📥 Downloading {filename}...")
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        
        # Audio Sterilization
        subprocess.run(["ffmpeg", "-y", "-err_detect", "ignore_err", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        
        # Transcribe
        print("🤖 AI sedang transkripsi...")
        result = model.transcribe(audio_path, language="id", word_timestamps=True)
        
        # Clipping & Upload logic (tetap sama)
        # ... (pastikan logika clipping tetap ada di bawah sini) ...
        
        return {"status": "success", "message": "Video processed!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})