import streamlit as st
import requests
import time

# Konfigurasi Endpoint RunPod
RUNPOD_ENDPOINT_ID = "mj3o3oohv9up54"
RUNPOD_API_KEY = st.secrets["RUNPOD_API_KEY"] # Kita pakai Secrets biar aman

st.set_page_config(page_title="Jagoan Clipper", layout="centered")
st.title("🔥 Jagoan Clipper Web")

video_url = st.text_input("Masukkan Link Video (MP4/Direct Link):")

if st.button("Generate Klip"):
    if video_url:
        with st.spinner("Mesin lagi ngebut, tunggu bentar..."):
            try:
                # Kirim request ke RunPod
                url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"
                headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
                payload = {"input": {"video_url": video_url}}
                
                response = requests.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ Klip berhasil dibuat!")
                    for i, clip_url in enumerate(data.get("output", {}).get("urls", [])):
                        st.video(clip_url)
                        st.write(f"Klip {i+1}: {clip_url}")
                else:
                    st.error(f"Error: {response.text}")
                    
            except Exception as e:
                st.error(f"System Error: {e}")
    else:
        st.warning("Masukkan link videonya dulu bro!")
