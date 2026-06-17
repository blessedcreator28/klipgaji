import streamlit as st
import boto3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def process_video(uploaded_file):
    file_name = uploaded_file.name
    s3 = boto3.client('s3', 
        endpoint_url=os.getenv('R2_ENDPOINT'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name='auto')
    
    s3.upload_fileobj(uploaded_file, "klipgaji-bucket", file_name)
    
    response = requests.post(os.getenv('RUNPOD_ENDPOINT'), 
        headers={"Authorization": f"Bearer {os.getenv('RUNPOD_API_KEY')}"},
        json={"input": {"nama_file_di_r2": file_name}})
    
    return response

st.title("KlipGaji Revenue Factory")
uploaded_file = st.file_uploader("Pilih video MP4", type=["mp4"])

if uploaded_file is not None:
    if st.button("Proses Video"):
        with st.spinner('Sedang upload...'):
            try:
                resp = process_video(uploaded_file)
                if resp.status_code == 200:
                    st.success("Sukses! Sistem sedang bekerja.")
                else:
                    st.error(f"Gagal: {resp.text}")
            except Exception as e:
                st.error(f"Error: {e}")
