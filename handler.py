import runpod
import os
import boto3
import subprocess
import sys

# Konfigurasi log agar keluar di dashboard RunPod
sys.stdout.reconfigure(line_buffering=True)
from faster_whisper import WhisperModel

print("--- INITIALIZING MODEL ---")
try:
    # Load model sekali saat container start
    model = WhisperModel("Systran/faster-whisper-small", device="cuda", compute_type="float16")
    print("--- MODEL LOADED SUCCESSFULLY ---")
except Exception as e:
    print(f"CRITICAL ERROR LOADING MODEL: {str(e)}")
    model = None

def get_smart_clips(segments):
    clips = []
    if not segments: return clips
    
    current = {'start': segments[0]['start'], 'end': 0, 'text': ""}
    for seg in segments:
        current['text'] += seg['text'] + " "
        current['end'] = seg['end']
        duration = current['end'] - current['start']
        
        # Logika potong klip: durasi minimal 30s atau maksimal 60s
        if (duration >= 30 and any(p in seg['text'] for p in ['.', '!', '?'])) or duration >= 60:
            clips.append(current)
            current = {'start': seg['end'], 'end': 0, 'text': ""}
    return clips

def handler(job):
    try:
        job_input = job.get('input', {})
        filename = job_input.get('filename', '')
        if not filename: 
            return {"error": "Filename kosong"}
        
        # Validasi Env Vars
        r2_endpoint = os.environ.get('R2_ENDPOINT')
        aws_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
        r2_bucket = os.environ.get('R2_BUCKET')

        if not all([r2_endpoint, aws_key, aws_secret, r2_bucket]):
            return {"error": "Environment variables tidak lengkap"}

        s3 = boto3.client('s3',
            endpoint_url=r2_endpoint,
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region_name='auto')
        
        video_path = f"/tmp/{filename}"
        audio_path = f"/tmp/{filename.replace('.mp4', '.wav')}"
        
        print(f"Downloading {filename}...")
        s3.download_file(r2_bucket, filename, video_path)
        
        # FFmpeg extract audio
        print("Extracting audio...")
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        
        if model is None:
            return {"error": "Model tidak tersedia"}

        print("Transcribing...")
        segments, _ = model.transcribe(audio_path, beam_size=1)
        
        safe_segments = [{'start': seg.start, 'end': seg.end, 'text': seg.text} for seg in segments]
        clips = get_smart_clips(safe_segments)
        
        response_data = []
        # Filter FFmpeg: Portrait 1080x1920 + Blur Background
        filter_complex = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[bg];[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"
        
        for i, clip in enumerate(clips):
            clip_name = f"clip_{i}_{filename}"
            clip_path = f"/tmp/{clip_name}"
            
            print(f"Processing clip {i}...")
            # FIXED: Menghapus titik salah ketik sebelumnya di '-vf'
            subprocess.run([
                "ffmpeg", "-y", "-ss", str(clip['start']), "-i", video_path, "-t", str(clip['end'] - clip['start']),
                "-vf", filter_complex, "-c:v", "libx264", "-crf", "23", "-preset", "veryfast", clip_path
            ], check=True)
            
            s3.upload_file(clip_path, r2_bucket, clip_name, ExtraArgs={'ContentType': 'video/mp4'})
            response_data.append({"url": f"https://{r2_bucket}.r2.dev/{clip_name}"})

        return {"status": "success", "clips": response_data}

    except Exception as e:
        print(f"HANDLER ERROR: {str(e)}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
