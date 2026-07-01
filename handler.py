import os
import boto3
import runpod
import subprocess
from faster_whisper import WhisperModel
from analyzer import analyze_transcription 

# Load Credential R2
ENDPOINT_URL = os.environ.get("R2_ENDPOINT")
PUBLIC_BUCKET_URL = "https://pub-7b62ff616edc4f6aa4a15d2442e2af87.r2.dev"
ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.environ.get("R2_BUCKET")

# Inisialisasi Whisper dan S3
model = WhisperModel("small", device="cuda", compute_type="float16")
s3 = boto3.client("s3", endpoint_url=ENDPOINT_URL, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name="auto")

def cut_and_upload(local_path, start, end, clip_index):
    output_filename = f"clip_{clip_index}.mp4"
    output_path = f"/tmp/{output_filename}"
    duration = end - start
    
    try:
        # 1. FFmpeg
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(start), "-i", local_path, 
            "-t", str(duration), "-c:v", "libx264", "-c:a", "aac", output_path
        ], check=True, capture_output=True, text=True)
        
        # 2. Upload
        if not os.path.exists(output_path):
            return "ERROR: File output tidak ditemukan setelah ffmpeg"
            
        s3.upload_file(output_path, BUCKET_NAME, output_filename, ExtraArgs={'ContentType': 'video/mp4'})
        os.remove(output_path)
        
        return f"{PUBLIC_BUCKET_URL}/{output_filename}"
    
    except subprocess.CalledProcessError as e:
        return f"FFMPEG_ERROR: {e.stderr}"
    except Exception as e:
        return f"SYSTEM_ERROR: {str(e)}"

def handler(event):
    job_input = event.get("input", {})
    s3_key = job_input.get("s3_key")

    try:
        local_path = f"/tmp/input_video.mp4"
        s3.download_file(BUCKET_NAME, s3_key, local_path)

        segments, _ = model.transcribe(local_path, beam_size=5)
        transcription = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
        
        # Murni memanggil analyzer tanpa setting API key lagi di sini
        viral_clips_data = analyze_transcription(transcription)

        for clip in viral_clips_data:
            result = cut_and_upload(local_path, clip['start_time'], clip['end_time'], viral_clips_data.index(clip))
            clip['clip_url'] = result 

        if os.path.exists(local_path): os.remove(local_path)
        return {"status": "success", "viral_clips": {"clips": viral_clips_data}}

    except Exception as e:
        return {"status": "error", "message": f"HANDLER_CRITICAL: {str(e)}"}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})