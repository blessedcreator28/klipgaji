import runpod
import os
import boto3
import subprocess
import sys

sys.stdout.reconfigure(line_buffering=True)
from faster_whisper import WhisperModel

model = WhisperModel("small", device="cuda", compute_type="float16")

def get_smart_clips(segments):
    clips = []
    if not segments: return clips
    current = {'start': segments[0].start, 'end': 0, 'text': ""}
    for seg in segments:
        current['text'] += seg.text + " "
        current['end'] = seg.end
        duration = current['end'] - current['start']
        if (duration >= 30 and any(p in seg.text for p in ['.', '!', '?'])) or duration >= 60:
            clips.append(current)
            current = {'start': seg.end, 'end': 0, 'text': ""}
    return clips

def handler(job):
    job_input = job.get('input', {})
    filename = job_input.get('filename', '')
    if not filename: return {"error": "Filename kosong"}
    
    s3 = boto3.client('s3',
        endpoint_url=os.environ['R2_ENDPOINT'],
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        region_name='auto')
    
    video_path = f"/tmp/{filename}"
    audio_path = f"/tmp/{filename.replace('.mp4', '.wav')}"
    s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
    
    # Generate Audio
    subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
    segments, _ = model.transcribe(audio_path, beam_size=1)
    clips = get_smart_clips(list(segments))
    
    response_data = []
    # Filter FFmpeg untuk Portrait + Blur Background
    filter_complex = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[bg];[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"
    
    for i, clip in enumerate(clips):
        clip_name = f"clip_{i}.mp4"
        clip_path = f"/tmp/{clip_name}"
        # Jalankan editing (Resize + Blur + Trim)
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(clip['start']), "-i", video_path, "-t", str(clip['end'] - clip['start']),
            "-vf", filter_complex, "-c:v", "libx264", "-crf", "23", "-preset", "veryfast", clip_path
        ], check=True)
        
        s3.upload_file(clip_path, os.environ['R2_BUCKET'], clip_name, ExtraArgs={'ContentType': 'video/mp4'})
        response_data.append({"url": f"https://pub-7b62ff616edc4f6aa4a15d2442e2af87.r2.dev/{clip_name}"})

    return {"status": "success", "clips": response_data}

runpod.serverless.start({"handler": handler})
