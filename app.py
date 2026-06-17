import streamlit as st
import boto3
import requests
import time  # Wajib ditambahin buat ngasih jeda ngecek

# --- KONFIGURASI LOKAL ---
R2_ENDPOINT = "https://df3050e61e1819164a9f528c7eddaa86.r2.cloudflarestorage.com"
AWS_KEY = "b33eb75134afc31f82a16aac4dbee7d6"
AWS_SECRET = "3b643d675df524f4ca2595c1a5df87876774646ea96a6589b36a836700bb9f04"
BUCKET_NAME = "klipgaji-bucket"
RUNPOD_API_KEY = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv"
RUNPOD_ENDPOINT_ID = "8xt58348tekm24"

def upload_to_r2(file):
    s3 = boto3.client('s3', 
                      endpoint_url=R2_ENDPOINT,
                      aws_access_key_id=AWS_KEY,
                      aws_secret_access_key=AWS_SECRET,
                      region_name='auto')
    s3.upload_fileobj(file, BUCKET_NAME, file.name)
    return file.name

def trigger_runpod(video_name):
    # 1. Kirim tugas (Pakai endpoint /run, BUKAN /runsync)
    url_run = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}", "Content-Type": "application/json"}
    payload = {"input": {"video_url": video_name}}
    
    response = requests.post(url_run, json=payload, headers=headers)
    job_data = response.json()
    job_id = job_data.get('id')
    
    if not job_id:
        return {"error": "Gagal bikin antrean di RunPod", "detail": job_data}

    # 2. Sistem Mandor (Ngecek status tiap 5 detik)
    url_status = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}"
    
    while True:
        status_res = requests.get(url_status, headers=headers).json()
        status = status_res.get('status')
        
        if status == 'COMPLETED':
            return status_res
        elif status in ['FAILED', 'CANCELLED']:
            return status_res
        
        # Kalau masih IN_QUEUE atau IN_PROGRESS, tunggu 5 detik lalu cek lagi
        time.sleep(5)

# --- UI STREAMLIT ---
st.title("Jagoan Clipper MVP")
uploaded_file = st.file_uploader("Upload video lo (format MP4)", type=['mp4'])

if uploaded_file and st.button("Proses Video"):
    try:
        with st.spinner("Upload ke R2..."):
            filename = upload_to_r2(uploaded_file)
            st.write(f"Berhasil upload: {filename}")
        
        with st.spinner("AI sedang memproses klip... Ini butuh waktu, jangan di-refresh ya Bro!"):
            result = trigger_runpod(filename)
            
        if result.get("status") == "COMPLETED" and "output" in result:
            st.success("Selesai! AI berhasil motong video lo.")
            clips = result['output'].get('clips', [])
            for clip in clips:
                st.video(clip['url'])
                st.write(f"**Transkrip:** {clip['text']}")
                st.write(f"---")
        else:
            st.error(f"Error atau Gagal dari RunPod: {result}")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")