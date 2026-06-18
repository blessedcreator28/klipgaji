import runpod
import os
import boto3
import subprocess
import sys

sys.stdout.reconfigure(line_buffering=True)
from faster_whisper import WhisperModel

# Load model
model = WhisperModel("Systran/faster-whisper-small", device="cuda", compute_type="float16")

def handler(job):
    try:
        filename = job.get('input', {}).get('filename', '')
        video_path = f"/tmp/{filename}"
        
        # 1. Download dengan validasi file
        s3 = boto3.client('s3', endpoint_url=os.environ['R2_ENDPOINT'], aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'], aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'], region_name='auto')
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        
        # Cek apakah file ada dan tidak kosong
        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            return {"status": "failed", "error": "File unduhan kosong atau gagal diunduh"}

        # 2. Cek apakah FFmpeg bisa membaca file
        check_file = subprocess.run(["ffmpeg", "-i", video_path], capture_output=True, text=True)
        if check_file.returncode != 0:
            return {"status": "failed", "error": f"FFmpeg gagal baca file: {check_file.stderr}"}

        # 3. Eksekusi render dengan log detail
        clip_path = "/tmp/test_clip.mp4"
        cmd = [
            "ffmpeg", "-y", "-ss", "0", "-t", "5", "-i", video_path, 
            "-c:v", "libx264", "-preset", "ultrafast", clip_path
        ]
        render = subprocess.run(cmd, capture_output=True, text=True)
        
        if render.returncode != 0:
            return {"status": "failed", "error": f"FFmpeg render error: {render.stderr}"}

        return {"status": "success", "message": "Render test berhasil"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
