import streamlit as st
import boto3
import os
import uuid
import requests
from supabase import create_client

# Inisialisasi R2 (Cloudflare) - Menarik kunci dari 'Secrets' Streamlit
s3 = boto3.client('s3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name='auto'
)

# Inisialisasi Supabase
supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

st.title("🔥 KlipGaji (Dev Mode)")
st.write("Mesin pencetak klip otomatis. Upload, tinggal tidur, panen!")

uploaded_file = st.file_uploader("Upload Video Mentah (Max 1GB)", type=['mp4', 'mov'])

if uploaded_file and st.button("Proses Video"):
    with st.spinner('Uploading ke R2...'):
        try:
            unique_filename = f"{uuid.uuid4()}.mp4"
            
            # Upload ke R2
            s3.upload_fileobj(uploaded_file, os.environ['R2_BUCKET'], unique_filename)
            video_url = f"{os.environ['R2_ENDPOINT']}/{os.environ['R2_BUCKET']}/{unique_filename}"
            
            st.success("Video berhasil di-upload ke R2!")
            
            # Panggil RunPod
            runpod_url = "https://api.runpod.ai/v2/b06tr4ms0r49ue/run" 
            headers = {"Authorization": f"Bearer {os.environ['RUNPOD_API_KEY']}"}
            payload = {"input": {"video_url": video_url}}
            
            response = requests.post(runpod_url, json=payload, headers=headers)
            st.write("Mesin sedang bekerja, cek tab Logs di RunPod!")
            
        except Exception as e:
            st.error(f"Error: {e}")