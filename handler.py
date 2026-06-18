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
        if (current['end'] - current['start'] >= 30):
            clips.append(current)
            current = {'start': seg['end'], 'end': 0, 'text': ""}
    return clips

def handler(job):
    try:
        job_input = job.get('input', {})
        filename = job_input.get('filename', '')
        if not filename: return {"error": "Filename kosong"}
        
        # Setup S3/R2
        s3 = boto3.client('s3',
            endpoint_url=os.environ.get('R2_ENDPOINT'),
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name='auto')
        
        video_path = f"/tmp/{filename}"
        audio_path = f"/tmp/{filename}.wav"
        
        print(f"Downloading {filename}...")
        s3.download_file(os.environ.get('R2_BUCKET'), filename, video_path)
        
        print("Extracting audio...")
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        
        print("Transcribing...")
        segments, _ = model.transcribe(audio_path, beam_size=1)
        clips = get_smart_clips([{'start': s.start, 'end': s.end, 'text': s.text} for s in segments])
        
        response_data = []
        # Filter disederhanakan: Menghindari crash karena boxblur berat
        filter_simple = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
        
        for i, clip in enumerate(clips):
            clip_name = f"clip_{i}_{filename}"
            clip_path = f"/tmp/{clip_name}"
            
            print(f"Rendering clip {i}...")
            cmd = [
                "ffmpeg", "-y", "-ss", str(clip['start']), "-i", video_path, 
                "-t", str(clip['end'] - clip['start']),
                "-vf", filter_simple, 
                "-c:v", "libx264", "-crf", "28", "-preset", "ultrafast", 
                "-threads", "1", clip_path
            ]
            
            # Eksekusi dengan capture_output agar kita bisa lihat error aslinya
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"FFMPEG ERROR: {result.stderr}")
                return {"status": "failed", "error": f"FFmpeg error: {result.stderr}"}
            
            s3.upload_file(clip_path, os.environ.get('R2_BUCKET'), clip_name)
            response_data.append({"url": f"https://{os.environ.get('R2_BUCKET')}.r2.dev/{clip_name}"})

        return {"status": "success", "clips": response_data}

    except Exception as e:
        print(f"HANDLER ERROR: {str(e)}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
