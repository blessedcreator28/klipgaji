import runpod
import os
import sys
import boto3
import subprocess
import traceback
from faster_whisper import WhisperModel

sys.stdout.reconfigure(line_buffering=True)
print("--- [BOOT] SCRIPT LOADED ---", flush=True)

# Load model dari folder lokal
try:
    print("--- [MODEL] LOADING LOCAL WHISPER MODEL ---", flush=True)
    model = WhisperModel("/app/whisper-model", device="cuda", compute_type="float16")
    print("--- [MODEL] LOADED ---", flush=True)
except Exception as e:
    print(f"--- [CRITICAL] FAILED TO LOAD MODEL: {str(e)} ---", flush=True)
    model = None

def get_smart_clips(segments):
    clips = []
    current_clip = {'start': segments[0].start, 'end': 0, 'text': ""}
    
    for seg in segments:
        current_clip['text'] += seg.text + " "
        current_clip['end'] = seg.end
        duration = current_clip['end'] - current_clip['start']
        
        # Logika potong: > 30 detik DAN ada tanda baca, ATAU sudah 60 detik
        if (duration >= 30 and any(p in seg.text for p in ['.', '!', '?'])) or duration >= 60:
            clips.append(current_clip)
            current_clip = {'start': seg.end, 'end': 0, 'text': ""}
    return clips

def handler(job):
    print(f"--- [HANDLER] JOB RECEIVED ---", flush=True)
    if model is None:
        return {"status": "error", "message": "Model not loaded"}
    
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
        
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        
        segments, info = model.transcribe(audio_path, beam_size=5)
        clips = get_smart_clips(list(segments))
        
        response_data = []
        for i, clip in enumerate(clips):
            clip_filename = f"clip_{job.get('id')}_{i}.mp4"
            clip_path = f"/tmp/{clip_filename}"
            
            subprocess.run(["ffmpeg", "-y", "-ss", str(clip['start']), "-i", video_path, 
                            "-t", str(clip['end'] - clip['start']), "-c", "copy", clip_path], check=True)
            
            s3.upload_file(clip_path, os.environ['R2_BUCKET'], clip_filename, ExtraArgs={'ContentType': 'video/mp4'})
            
            # GANTI URL DI BAWAH INI DENGAN URL R2 LO
            clip_url = f"https://pub-xxxxxx.r2.dev/{clip_filename}" 
            
            response_data.append({
                "id": i,
                "url": clip_url,
                "text": clip['text'],
                "duration": round(clip['end'] - clip['start'], 2)
            })
        
        return {"status": "success", "clips": response_data}
        
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"--- [CRITICAL ERROR] ---\n{error_msg}", flush=True)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})