import runpod
import os
import requests
import uuid
import traceback
import subprocess
import whisper
import boto3
from supabase import create_client

# Inisialisasi R2
s3 = boto3.client('s3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name='auto'
)

print("🔥 MEMANASKAN MESIN: R2 Online & AI Ready!")
model = whisper.load_model("small")

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
            f.write(f"Dialogue: 0,{format_time(start_t)},{format_time(end_t)},MrBeast,,0,0,0,,{w['word'].strip().upper()}\n")

def handler(job):
    try:
        supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
        job_input = job.get('input', {})
        video_url = job_input.get('video_url')
        unique_id = str(uuid.uuid4())[:8]
        video_path = f"/tmp/input_{unique_id}.mp4"
        audio_path = f"/tmp/audio_{unique_id}.wav"
        
        # Download
        r = requests.get(video_url, stream=True, timeout=120)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            
        # Audio Sterilization
        subprocess.run(["ffmpeg", "-y", "-err_detect", "ignore_err", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        
        # AI Transcription
        result = model.transcribe(audio_path, language="id", word_timestamps=True)
        
        # Clipping Logic
        segments = result.get("segments", [])
        clips = []
        current_clip = {"start": 0, "end": 0, "words": []}
        for seg in segments:
            if not current_clip["words"]: current_clip["start"] = seg["start"]
            if "words" in seg: current_clip["words"].extend(seg["words"])
            current_clip["end"] = seg["end"]
            if (current_clip["end"] - current_clip["start"]) >= 40.0:
                clips.append(current_clip)
                current_clip = {"start": 0, "end": 0, "words": []}
        
        clip_urls = []
        for i, c in enumerate(clips):
            output_path = f"/tmp/clip_{unique_id}_{i}.mp4"
            ass_path = f"/tmp/subs_{unique_id}_{i}.ass"
            generate_mrbeast_subs(c["words"], c["start"], ass_path)
            
            # Rendering with Subtitles
            subprocess.run(["ffmpeg", "-y", "-ss", str(c["start"]), "-t", str(c["end"]-c["start"]), "-i", video_path, "-vf", f"subtitles='{ass_path.replace(':', '\\:')}'", "-c:v", "libx264", output_path], check=True)
            
            # UPLOAD TO R2
            with open(output_path, "rb") as f:
                s3.upload_fileobj(f, os.environ['R2_BUCKET'], f"clip_{unique_id}_{i}.mp4")
            
            # Generate URL (Sesuaikan dengan domain R2 lo)
            clip_urls.append(f"https://{os.environ['R2_BUCKET']}.r2.dev/clip_{unique_id}_{i}.mp4")
            
        return {"status": "success", "urls": clip_urls}
    except Exception as e:
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

runpod.serverless.start({"handler": handler})