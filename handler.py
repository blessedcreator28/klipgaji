cat <<EOF > handler.py
import runpod
import os
import boto3
import subprocess
import sys
from faster_whisper import WhisperModel

sys.stdout.reconfigure(line_buffering=True)

# Load model di awal
model = WhisperModel("/app/whisper-model", device="cuda", compute_type="float16")

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
    s3 = boto3.client('s3',
        endpoint_url=os.environ['R2_ENDPOINT'],
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        region_name='auto'
    )
    
    video_url = job_input.get('video_url', '')
    filename = video_url.split('/')[-1]
    video_path = f"/tmp/{filename}"
    audio_path = f"/tmp/{filename.replace('.mp4', '.wav')}"
    
    s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
    subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
    
    # SPEED OPTIMIZED: beam_size=1
    segments, _ = model.transcribe(audio_path, beam_size=1)
    clips = get_smart_clips(list(segments))
    
    response_data = []
    for i, clip in enumerate(clips):
        clip_name = f"clip_{job.get('id')}_{i}.mp4"
        clip_path = f"/tmp/{clip_name}"
        subprocess.run(["ffmpeg", "-y", "-ss", str(clip['start']), "-i", video_path, "-t", str(clip['end'] - clip['start']), "-c", "copy", clip_path], check=True)
        s3.upload_file(clip_path, os.environ['R2_BUCKET'], clip_name, ExtraArgs={'ContentType': 'video/mp4'})
        
        response_data.append({
            "url": f"https://pub-7b62ff616edc4f6aa4a15d2442e2af87.r2.dev/{clip_name}",
            "text": clip['text'],
            "duration": round(clip['end'] - clip['start'], 2)
        })

    return {"status": "success", "clips": response_data}

runpod.serverless.start({"handler": handler})
EOF