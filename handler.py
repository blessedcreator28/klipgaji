import runpod
import boto3
import os

# Setup client R2 dengan key yang sudah lo sesuaikan
s3 = boto3.client(
    's3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name='auto'
)

def handler(event):
    job_input = event.get("input", {})
    s3_key = job_input.get("s3_key")
    # Pastikan folder tmp ada
    local_path = f"/tmp/{s3_key}"

    if not s3_key:
        return {"status": "error", "message": "s3_key tidak ada di input"}

    try:
        # Download dari R2
        print(f"Mulai download: {s3_key} dari bucket {os.getenv('R2_BUCKET')}")
        s3.download_file(os.getenv('R2_BUCKET'), s3_key, local_path)
        
        if os.path.exists(local_path):
            file_size = os.path.getsize(local_path)
            return {
                "status": "success", 
                "message": f"File berhasil didownload, ukuran: {file_size} bytes"
            }
        else:
            return {"status": "error", "message": "File tidak ditemukan setelah download"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

runpod.serverless.start({"handler": handler})