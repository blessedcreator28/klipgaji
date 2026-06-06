cat <<EOF > handler.py
import runpod
import os
import sys
import boto3
import subprocess
import traceback

print("--- [DEBUG] SCRIPT STARTING ---", flush=True)

try:
    print("--- [DEBUG] IMPORTING LIBRARIES ---", flush=True)
    from faster_whisper import WhisperModel
    print("--- [DEBUG] IMPORT SUCCESS ---", flush=True)
except Exception as e:
    print(f"--- [CRITICAL IMPORT ERROR] {str(e)} ---", flush=True)
    sys.exit(1)

# Load model
try:
    print("--- [DEBUG] LOADING MODEL ---", flush=True)
    model = WhisperModel("/app/whisper-model", device="cuda", compute_type="float16")
    print("--- [DEBUG] MODEL LOADED ---", flush=True)
except Exception as e:
    print(f"--- [CRITICAL MODEL ERROR] {str(e)} ---", flush=True)
    sys.exit(1)

def get_smart_clips(segments):
    clips = []
    if not segments: return clips
    current_clip = {'start': segments[0].start, 'end': 0, 'text': ""}
    for seg in segments:
        current_clip['text'] += seg.text + " "
        current_clip['end'] = seg.end
        duration = current_clip['end'] - current_clip['start']
        if (duration >= 30 and any(p in seg.text for p in ['.', '!', '?'])) or duration >= 60:
            clips.append(current_clip)
            current_clip = {'start': seg.end, 'end': 0, 'text': ""}
    return clips

def handler(job):
    print("--- [HANDLER] JOB RECEIVED ---", flush=True)
    try:
        s3 = boto3.client('s3',
            endpoint_url=os.environ['R2_ENDPOINT'],
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name='auto'
        )
        
        job_input = job.get('input', {})
        video_url = job_input.get('video_url', '')
        filename = video_url.split('/')[-1]
        video_path = f"/tmp/{filename}"
        audio_path = f"/tmp/{filename.replace('.mp4', '.wav')}"
        
        print("--- [DEBUG] DOWNLOAD START ---", flush=True)
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        
        print("--- [DEBUG] FFMPEG START ---", flush=True)
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        
        print("--- [DEBUG] WHISPER START ---", flush=True)
        segments, info = model.transcribe(audio_path, beam_size=5)
        clips = get_smart_clips(list(segments))
        
        response_data = []
        for i, clip in enumerate(clips):
            clip_filename = f"clip_{job.get('id')}_{i}.mp4"
            clip_path = f"/tmp/{clip_filename}"
            subprocess.run(["ffmpeg", "-y", "-ss", str(clip['start']), "-i", video_path, 
                            "-t", str(clip['end'] - clip['start']), "-c", "copy", clip_path], check=True)
            s3.upload_file(clip_path, os.environ['R2_BUCKET'], clip_filename, ExtraArgs={'ContentType': 'video/mp4'})
            clip_url = f"https://pub-7b62ff616edc4f6aa4a15d2442e2af87.r2.dev/{clip_filename}"
            response_data.append({"id": i, "url": clip_url, "text": clip['text'], "duration": clip['end'] - clip['start']})

        return {"status": "success", "clips": response_data}
        
    except Exception as e:
        print(f"--- [CRITICAL RUNTIME ERROR] ---\n{traceback.format_exc()}", flush=True)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})
EOF