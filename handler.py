import runpod
import os
import boto3
import subprocess

def handler(job):
    try:
        filename = job.get('input', {}).get('filename', '')
        s3 = boto3.client('s3', endpoint_url=os.environ['R2_ENDPOINT'], aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'], aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'], region_name='auto')
        
        video_path = f"/tmp/{filename}"
        s3.download_file(os.environ['R2_BUCKET'], filename, video_path)
        
        # Cuma potong 30 detik pertama tanpa filter macam-macam
        clip_path = "/tmp/test_clip.mp4"
        cmd = ["ffmpeg", "-y", "-ss", "0", "-t", "30", "-i", video_path, "-c", "copy", clip_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return {"status": "failed", "error": f"FFmpeg error: {result.stderr}"}
            
        s3.upload_file(clip_path, os.environ['R2_BUCKET'], "test_potong.mp4")
        return {"status": "success", "message": "Berhasil potong video"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
