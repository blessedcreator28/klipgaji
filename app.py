import streamlit as st
import boto3
import os
import uuid
import requests
import json
from supabase import create_client

# --- MANUAL: ISI KEY DI BAWAH INI ---
RUNPOD_API_KEY = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv" # Ganti ini
ENDPOINT_ID = "mj3o3oohv9up54" # ID Endpoint lo
# ------------------------------------

# Inisialisasi R2
s3 = boto3.client('s3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name='auto'
)

st.title("🔥 KlipGaji Debugger")
uploaded_file = st.file_uploader("Upload Video", type=['mp4'])

if uploaded_file and st.button("Proses Video"):
    st.write("1. Mengupload ke R2...")
    try:
        unique_filename = f"{uuid.uuid4()}.mp4"
        s3.upload_fileobj(uploaded_file, os.environ['R2_BUCKET'], unique_filename)
        video_url = f"{os.environ['R2_ENDPOINT']}/{os.environ['R2_BUCKET']}/{unique_filename}"
        st.write(f"✅ R2 Upload Sukses: {video_url}")
        
        # DEBUG HANDSHAKE
        st.write("2. Menghubungi RunPod...")
        url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"
        headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}", "Content-Type": "application/json"}
        payload = {"input": {"video_url": video_url}}
        
        response = requests.post(url, json=payload, headers=headers)
        
        st.write(f"📡 Response Status Code: {response.status_code}")
        st.write(f"📡 Response Body: {response.text}")
        
        if response.status_code == 200:
            st.success("✅ Berhasil menembak ke RunPod!")
        else:
            st.error("❌ Gagal menembak ke RunPod. Cek API Key atau Endpoint ID.")
            
    except Exception as e:
        st.error(f"❌ Error Detail: {str(e)}")