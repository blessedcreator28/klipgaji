import streamlit as st
import requests
import uuid
from supabase import create_client

# Konfigurasi Supabase
SUPABASE_URL = "https://dfqegfdehvpttslbzzjv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Konfigurasi RunPod
RUNPOD_API_KEY = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv" 
RUNPOD_ENDPOINT = "dcw0t4jtdqhtdo" 

st.set_page_config(page_title="Jagoan Clipper AI", layout="centered")

st.title("✂️ Jagoan Clipper AI")
st.markdown("**Sistem Auto-Klip Viral Tercepat untuk Market Lokal.**")

st.divider()

# --- BAGIAN 1: PENGUMUMAN LINK (Provokatif & Profesional) ---
st.error("🔴 **STATUS: YOUTUBE DIRECT BYPASS SEDANG DIBATASI**")
st.markdown("""
*YouTube saat ini sedang melakukan pemblokiran massal terhadap sistem AI ekstraksi secara global. Untuk menjaga keamanan data dan kualitas klip 4K Anda, fitur "Paste Link" kami alihkan sementara ke sistem **Direct Upload**.*
""")

with st.expander("💡 Cara Alternatif Download Video YouTube (Klik Disini)"):
    st.markdown("""
    Jika Anda belum memiliki file video, ikuti *workflow* sistematis ini:
    1. Buka web seperti **cobalt.tools** atau **ssyoutube.com**.
    2. Paste link YouTube yang ingin dipotong.
    3. Download dengan resolusi **720p** (ukuran paling ringan & cepat diproses AI).
    4. Upload file `.mp4` tersebut pada kolom di bawah.
    """)

# --- BAGIAN 2: UPLOAD & PROSES ---
st.markdown("### 📤 Upload Video Mentah (Max 200MB)")
uploaded_file = st.file_uploader("Drop file video Anda di sini untuk diproses AI", type=["mp4", "mov", "avi"])

if st.button("🚀 Generate Klip Viral Sekarang", type="primary", use_container_width=True):
    if uploaded_file is not None:
        with st.spinner("⏳ Mengamankan file ke server (Zero-Watching AI sedang bersiap)..."):
            try:
                # 1. Upload ke Supabase
                file_ext = uploaded_file.name.split('.')[-1]
                unique_filename = f"raw_{uuid.uuid4().hex[:8]}.{file_ext}"
                file_bytes = uploaded_file.getvalue()
                
                supabase.storage.from_("jagoan-videos").upload(path=unique_filename, file=file_bytes)
                video_url = supabase.storage.from_("jagoan-videos").get_public_url(unique_filename)
                
            except Exception as e:
                st.error(f"Gagal upload file: {e}")
                st.stop()
                
        with st.spinner("🧠 AI sedang membedah momen viral... (Membutuhkan waktu beberapa menit)"):
            try:
                # 2. Tembak ke RunPod
                headers = {
                    "Authorization": f"Bearer {RUNPOD_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "input": {
                        "video_url": video_url
                    }
                }
                
                runpod_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT}/runsync"
                response = requests.post(runpod_url, json=payload, headers=headers)
                result = response.json()
                
                # 3. Tampilkan Hasil
                if result.get("status") == "COMPLETED":
                    output = result.get("output", {})
                    if output.get("status") == "success":
                        st.success("✅ Klip berhasil dibuat! Sistem AI telah memisahkan momen terbaik.")
                        urls = output.get("urls", [])
                        
                        for i, url in enumerate(urls):
                            st.video(url)
                            st.markdown(f"[⬇️ Download Klip {i+1}]({url})")
                    else:
                        st.error(f"Error AI: {output.get('message')}")
                else:
                    st.error("Proses di RunPod gagal atau timeout.")
                    
            except Exception as e:
                st.error(f"Koneksi ke AI gagal: {e}")
    else:
        st.warning("⚠️ Mohon upload file video terlebih dahulu.")