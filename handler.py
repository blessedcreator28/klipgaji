import runpod
import os
import boto3
import sys

# Konfigurasi log
sys.stdout.reconfigure(line_buffering=True)
print("--- [BOOT] SCRIPT LOADED ---", flush=True)

def handler(job):
    print(f"--- [HANDLER] JOB RECEIVED: {job.get('id')} ---", flush=True)
    
    try:
        # Pindahkan inisialisasi ke dalam try agar error tertangkap
        print("--- [DEBUG] INITIALIZING S3 ---", flush=True)
        s3 = boto3.client('s3',
            endpoint_url=os.environ['R2_ENDPOINT'],
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
            region_name='auto'
        )
        
        job_input = job.get('input', {})
        video_url = job_input.get('video_url', '')
        
        if not video_url:
             print("--- [ERROR] NO VIDEO_URL PROVIDED ---", flush=True)
             return {"status": "error", "message": "No video_url"}

        filename = video_url.split('/')[-1]
        local_path = f"/tmp/{filename}"
        
        print(f"--- [DOWNLOAD] START: {filename} ---", flush=True)
        s3.download_file(os.environ['R2_BUCKET'], filename, local_path)
        print(f"--- [DOWNLOAD] SUCCESS: {local_path} ---", flush=True)
        
        return {"status": "success", "message": "File downloaded successfully"}
        
    except Exception as e:
        print(f"--- [CRITICAL ERROR] {str(e)} ---", flush=True)
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})