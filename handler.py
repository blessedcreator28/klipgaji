import runpod
import os
import boto3
import subprocess
import sys

sys.stdout.reconfigure(line_buffering=True)
from faster_whisper import WhisperModel

print("--- INITIALIZING MODEL ---")
model = WhisperModel("Systran/faster-whisper-small", device="cuda", compute_type="float16")

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
        filename = job.get('input', {}).get('filename', '')
        # Bersihkan nama file agar tidak ada karakter aneh
        clean_filename = "".join([c for c in filename if c.isalnum() or c in ['.', '_', '-']])
        
        s3 = boto3.client('s3',
            endpoint_url=os.environ['R2_ENDPOINT'],
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name='auto')
        
        video_path = f"/tmp/{clean_filename}"
        audio_path = f"/tmp/{clean_filename}.wav"
        
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        
        # Ekstrak audio
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        
        segments, _ = model.transcribe(audio_path, beam_size=1)
        clips = get_smart_clips([{'start': s.start, 'end': s.end, 'text': s.text} for s in segments])
        
        for i, clip in enumerate(clips):
            clip_path = f"/tmp/clip_{i}.mp4"
            # Command FFmpeg yang lebih aman
            cmd = [
                "ffmpeg", "-y", "-ss", str(clip['start']), "-i", video_path, 
                "-t", str(clip['end'] - clip['start']),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[bg];[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2",
                "-c:v", "libx264", "-crf", "23", "-preset", "veryfast", clip_path
            ]
            subprocess.run(cmd, check=True)
            s3.upload_file(clip_path, os.environ['R2_BUCKET'], f"clip_{i}_{clean_filename}")
            
        return {"status": "success"}
    except Exception as e:
        print(f"DETAIL ERROR: {str(e)}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
