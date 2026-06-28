import runpod
import boto3
import os
from faster_whisper import WhisperModel
from moviepy.video.io.VideoFileClip import VideoFileClip

# Setup client R2
s3 = boto3.client(
    's3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name='auto'
)

# Load model Whisper (Base/Small biar cepet)
model = WhisperModel("base", device="cuda", compute_type="float16")

def handler(event):
    job_input = event.get("input", {})
    s3_key = job_input.get("s3_key")
    local_path = f"/tmp/{s3_key}"

    try:
        # 1. Download
        s3.download_file(os.getenv('R2_BUCKET'), s3_key, local_path)
        
        # 2. Transkripsi (Faster-Whisper)
        segments, _ = model.transcribe(local_path, beam_size=5)
        transcript = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
        
        # 3. Clipping (Contoh: Potong 10 detik pertama sebagai tes)
        output_path = f"/tmp/clip_{s3_key}"
        with VideoFileClip(local_path) as video:
            new_clip = video.subclip(0, 10)
            new_clip.write_videofile(output_path, codec="libx264")
        
        # 4. Upload Balik ke R2
        output_key = f"clips/clip_{s3_key}"
        s3.upload_file(output_path, os.getenv('R2_BUCKET'), output_key)
        
        return {
            "status": "success",
            "message": "Proses selesai!",
            "transcript_count": len(transcript),
            "output_key": output_key
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})