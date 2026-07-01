import streamlit as st
import boto3
import requests
import time

# --- KONFIGURASI ---
R2_ENDPOINT = "https://df3050e61e1819164a9f528c7eddaa86.r2.cloudflarestorage.com"
AWS_KEY = "b33eb75134afc31f82a16aac4dbee7d6"
AWS_SECRET = "3b643d675df524f4ca2595c1a5df87876774646ea96a6589b36a836700bb9f04"
BUCKET_NAME = "klipgaji-bucket"
RUNPOD_API_KEY = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv"
RUNPOD_ENDPOINT_ID = "kik87fim663p19"

# Session State
if 'clips_data' not in st.session_state: st.session_state.clips_data = None

st.set_page_config(page_title="Jagoan Clipper", layout="centered")

def upload_to_r2(file):
    s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT, aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET, region_name='auto')
    s3.upload_fileobj(file, BUCKET_NAME, file.name)
    return file.name

def trigger_runpod(video_name):
    url_run = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}", "Content-Type": "application/json"}
    payload = {"input": {"s3_key": video_name, "job_id": "job_123"}}
    response = requests.post(url_run, json=payload, headers=headers, timeout=300)
    return response.json()

# --- UI ---
st.markdown('<h1 style="color:#FF6600; text-align:center;">JAGOAN CLIPPER</h1>', unsafe_allow_html=True)

# 1. Uploader (Yang tadi hilang)
uploaded_file = st.file_uploader("Pilih file video (MP4)", type=['mp4'])

# 2. Tombol Proses
if uploaded_file and st.button("Proses Video Sekarang"):
    with st.spinner("AI sedang memproses... jangan refresh!"):
        filename = upload_to_r2(uploaded_file)
        result = trigger_runpod(filename)
        
        if "output" in result:
            st.session_state.clips_data = result.get('output', {}).get('viral_clips', {}).get('clips', [])
        else:
            st.error(f"Error: {result}")

# 3. Render Hasil
if st.session_state.clips_data:
    st.success("Video berhasil diproses!")
    for index, clip in enumerate(st.session_state.clips_data):
        st.write(f"### {clip.get('title')}")
        st.link_button(f"📥 Download Klip {index + 1}", clip.get('clip_url', '#'))