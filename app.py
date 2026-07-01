import streamlit as st
import boto3
import requests
import time
import random # Buat generate viral score dummy

# --- KONFIGURASI ---
RUNPOD_API_KEY = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv"
RUNPOD_ENDPOINT_ID = "kik87fim663p19"

if 'clips_data' not in st.session_state:
    st.session_state.clips_data = None

st.set_page_config(page_title="Jagoan Clipper", layout="centered")

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0f0f0f; color: #ffffff; }
    .header-text { color: #FF6600; font-size: 40px; font-weight: bold; text-align: center; }
    div.stButton > button { background-color: #FF6600; color: white; border-radius: 8px; border: none; font-weight: bold; width: 100%; padding: 10px; }
    .card { background-color: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI ---
def trigger_runpod(video_name):
    url_run = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}", "Content-Type": "application/json"}
    payload = {"input": {"s3_key": video_name, "job_id": "550e8400-e29b-41d4-a716-446655440000"}}
    
    response = requests.post(url_run, json=payload, headers=headers)
    job_data = response.json()
    job_id = job_data.get('id')
    
    url_status = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}"
    while True:
        status_res = requests.get(url_status, headers=headers).json()
        if status_res.get('status') in ['COMPLETED', 'FAILED']: return status_res
        time.sleep(5)

# --- UI ---
st.markdown('<p class="header-text">JAGOAN CLIPPER</p>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Pilih file video (MP4)", type=['mp4'])

if uploaded_file and st.button("Proses Video Sekarang"):
    with st.spinner("AI sedang memproses klip..."):
        # (Logika upload R2 di sini tetap seperti sebelumnya)
        result = trigger_runpod("dummy_filename") # Sederhanakan buat tes
        
        if result.get("status") == "COMPLETED":
            st.session_state.clips_data = result.get('output', {}).get('viral_clips', {}).get('clips', [])
        else:
            st.error("Gagal memproses video.")

# Render Klip
if st.session_state.clips_data:
    st.success("Video berhasil diproses!")
    for index, clip in enumerate(st.session_state.clips_data):
        # Generate random score buat UI biar gak kosong
        viral_score = random.randint(85, 99) 
        
        with st.container():
            st.markdown(f"""
            <div class="card">
                <h3>✨ {clip.get('title', 'Klip Viral')}</h3>
                <p><b>Durasi:</b> {clip.get('start_time')}s - {clip.get('end_time')}s | <b>Viral Score:</b> {viral_score}%</p>
                <p><b>Analisis:</b> {clip.get('reason', 'Tidak ada analisis.')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # TOMBOL DOWNLOAD
            # CATATAN: st.download_button butuh file bytes asli.
            # Kalau backend belum ngirim file, ini tombol dummy biar gak error.
            st.download_button(
                label=f"📥 Download Klip {index + 1}",
                data=b"dummy_data", 
                file_name=f"klip_{index+1}.mp4",
                key=f"dl_{index}"
            )