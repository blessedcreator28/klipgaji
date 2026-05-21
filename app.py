import streamlit as st
import os
import requests
import time
from supabase import create_client

# Kunci & URL langsung ditempel di sini
SUPABASE_URL = "https://dfqegfdehvpttslbzzjv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
RUNPOD_API_KEY = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv"
RUNPOD_ENDPOINT_ID = "mj3o3oohv9up54"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Jagoan Clipper", layout="centered")
st.title("🔥 Jagoan Clipper Web")

st.write("Silakan upload video hasil download lo di bawah:")

uploaded_file = st.file_uploader("Pilih file video (MP4)", type=['mp4', 'mov'])

if uploaded_file is not None:
    if st.button("Generate Klip"):
        with st.spinner("Lagi upload video ke database..."):
            try:
                file_name = f"{int(time.time())}_{uploaded_file.name}"
                supabase.storage.from_("videos").upload(
                    path=file_name,
                    file=uploaded_file.getvalue(),
                    file_options={"content-type": "video/mp4"}
                )
                public_url = supabase.storage.from_("videos").get_public_url(file_name)
            except Exception as e:
                st.error(f"Gagal upload ke database: {e}")
                st.stop()
        
        # --- SISTEM POLLING (NGECEK BERKALA) ---
        with st.spinner("Video sukses diupload! AI lagi proses (Bisa makan waktu 1-3 menit)..."):
            try:
                runpod_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run"
                headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
                payload = {"input": {"video_url": public_url}}
                
                response = requests.post(runpod_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    job_data = response.json()
                    job_id = job_data.get("id")
                    
                    status_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}"
                    
                    while True:
                        status_resp = requests.get(status_url, headers=headers)
                        if status_resp.status_code == 200:
                            status_data = status_resp.json()
                            status = status_data.get("status")
                            
                            if status == "COMPLETED":
                                output_data = status_data.get("output", {})
                                if output_data.get("status") == "success":
                                    st.success("✅ Klip berhasil dibuat!")
                                    clips = output_data.get("urls", [])
                                    for i, clip_url in enumerate(clips):
                                        st.write(f"🎬 **Klip {i+1}**")
                                        st.video(clip_url)
                                    st.write("Preview Whisper:", output_data.get("transcription", ""))
                                else:
                                    st.error(f"Error dari mesin AI:\n{output_data}")
                                break 
                            
                            elif status in ["FAILED", "CANCELLED"]:
                                st.error(f"RunPod Gagal: {status_data}")
                                break 
                            
                            else:
                                time.sleep(3) 
                        else:
                            st.error("Gagal ngecek status ke RunPod.")
                            break
                else:
                    st.error(f"Koneksi awal RunPod Gagal: {response.text}")
                    
            except Exception as e:
                st.error(f"System Error: {e}")
else:
    st.info("Sistem paste link dinonaktifkan. Gunakan tombol 'Browse files' di atas untuk memproses video.")