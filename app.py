import streamlit as st
import os
import requests
import time
from supabase import create_client

# 1. Konfigurasi Kunci Akses (Diambil dari Secrets Streamlit)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
RUNPOD_API_KEY = st.secrets["RUNPOD_API_KEY"]
RUNPOD_ENDPOINT_ID = "mj3o3oohv9up54"

# Inisialisasi Supabase Client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Jagoan Clipper", layout="centered")
st.title("🔥 Jagoan Clipper Web")

st.write("Silakan upload video hasil download lo di bawah:")

# Fitur Upload File - Memblokir Paste Link
uploaded_file = st.file_uploader("Pilih file video (MP4)", type=['mp4', 'mov'])

if uploaded_file is not None:
    if st.button("Generate Klip"):
        # --- PROSES 1: UPLOAD KE SUPABASE ---
        with st.spinner("Lagi upload video ke database..."):
            try:
                file_name = f"{int(time.time())}_{uploaded_file.name}" # Tambah timestamp unik agar tidak duplikat
                
                # Upload file ke bucket 'videos'
                supabase.storage.from_("videos").upload(
                    path=file_name,
                    file=uploaded_file.getvalue(),
                    file_options={"content-type": "video/mp4"}
                )
                
                # Ambil Link Public dari Supabase
                public_url = supabase.storage.from_("videos").get_public_url(file_name)
                
            except Exception as e:
                st.error(f"Gagal upload ke database: {e}")
                st.stop()
        
        # --- PROSES 2: PROSES DI RUNPOD GPU ---
        with st.spinner("Video sukses diupload! Sekarang AI lagi proses potong video, tunggu bentar..."):
            try:
                # Nembak API RunPod secara Synchronous
                runpod_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync"
                headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
                payload = {"input": {"video_url": public_url}}
                
                response = requests.post(runpod_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Cek jika output dari AI sukses
                    output_data = data.get("output", {})
                    if output_data.get("status") == "success" or "urls" in output_data:
                        st.success("✅ Klip berhasil dibuat!")
                        
                        # Menampilkan semua klip video hasil potongan AI
                        clips = output_data.get("urls", [])
                        for i, clip_url in enumerate(clips):
                            st.write(f"🎬 **Klip {i+1}**")
                            st.video(clip_url)
                    else:
                        st.error(f"AI Gagal Memproses: {output_data}")
                else:
                    st.error(f"Koneksi RunPod Gagal: {response.text}")
                    
            except Exception as e:
                st.error(f"System Error saat hit RunPod: {e}")
else:
    # Mengingatkan user jika mencoba mencari kolom link teks
    st.info("Sistem paste link dinonaktifkan. Gunakan tombol 'Browse files' di atas untuk memproses video.")