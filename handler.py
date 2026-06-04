import runpod
import os
import requests
import uuid
import traceback
import subprocess
import whisper
import boto3
from supabase import create_client

# Inisialisasi R2 (Cloudflare)
s3 = boto3.client('s3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name='auto'
)

print("🔥 MEMANASKAN MESIN: R2 Online & AI Ready!")
model = whisper.load_model("small")

# ... (Fungsi generate_mrbeast_subs tetap sama) ...
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
            t_start = format_time(start_t); t_end = format_time(end_t)
            text = w['word'].strip().upper()
            f.write(f"Dialogue: 0,{t_start},{t_end},MrBeast,,0,0,0,,{text}\n")

def handler(job):
    try:
        supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        audio_path = f"/tmp/audio_{unique_id}.wav"
        
        # Download video
        r = requests.get(video_url, stream=True, timeout=120)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            
        # Sterilisasi Audio
        subprocess.run(["ffmpeg", "-y", "-err_detect", "ignore_err", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        
        result = model.transcribe(audio_path, language="id", word_timestamps=True)
        # ... (Logika clipping sama) ...
        # (Untuk efisiensi, asumsi logika clipping sudah ada di sini, fokus ke upload R2)
        
        clips = result.get("segments", []) # Simplified for brevity
        clip_urls = []
        
        for i, c in enumerate(clips):
            output_path = f"/tmp/clip_{unique_id}_{i}.mp4"
            # ... (FFmpeg render logika tetap sama) ...
            
            # UPLOAD KE R2 (BUKAN SUPABASE LAGI)
            with open(output_path, "rb") as f:
                s3.upload_fileobj(f, os.environ['R2_BUCKET'], f"clip_{unique_id}_{i}.mp4")
            
            # Generate Link (Asumsi Bucket R2 di-set Public)
            url = f"{os.environ['R2_ENDPOINT']}/{os.environ['R2_BUCKET']}/clip_{unique_id}_{i}.mp4"
            clip_urls.append(url)
            
        return {"status": "success", "urls": clip_urls}
    except Exception as e:
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})