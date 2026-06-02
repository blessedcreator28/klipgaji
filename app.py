import streamlit as st
import requests
import time
from supabase import create_client

# --- CONFIG & KEYS ---
SITE_TITLE = "🔥 Jagoan Clipper"
SITE_SUBTITLE = "Transform Long-Form ke Viral Moments"

SUPABASE_URL = "https://dfqegfdehvpttslbzzjv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
RUNPOD_API_KEY = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv"
RUNPOD_ENDPOINT_ID = "mj3o3oohv9up54"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CSS PREMIUM ORANGE THEME ---
st.set_page_config(page_title="Jagoan Clipper", layout="centered")
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .stButton>button { border: 2px solid #FF7F50; color: #FF7F50; background-color: transparent; border-radius: 8px; width: 100%; }
    .stButton>button:hover { background-color: #FF7F50; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { color: #FFFFFF; }
    .stTabs [aria-selected="true"] { color: #FF7F50; border-bottom: 2px solid #FF7F50; }
</style>
""", unsafe_allow_html=True)

# --- SISTEM LOGIN (GEMBOK DEPAN) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown(f"<h1 style='text-align: center; color: #FF7F50;'>🔒 {SITE_TITLE}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Sistem ini eksklusif. Masukkan email dan password lo buat akses mesin ini.</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="email@domain.com")
        password = st.text_input("Password", type="password", placeholder="Password sementara lo")
        submit = st.form_submit_button("Akses Member Area")
        
        if submit:
            if not email or not password:
                st.warning("Isi email dan password dulu, Bro.")
            else:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.session:
                        st.session_state.authenticated = True
                        st.rerun()
                except Exception as e:
                    st.error("Akses Ditolak! Email atau password lo salah.")
    st.stop() 

# --- MAIN APP ---
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()

st.title(SITE_TITLE)
st.markdown(f"### {SITE_SUBTITLE}")

# --- TABS SYSTEM ---
tab1, tab2 = st.tabs(["🔗 Paste Link (Main)", "📁 Upload Manual"])

with tab1:
    st.warning("⚠️ Fitur Paste Link sedang maintenance sebelum rilis resmi. Gunakan fitur 'Upload Manual' untuk sementara.")
    st.text_input("Paste Link YouTube:", placeholder="https://youtube.com/...", disabled=True)
    st.button("Proses Link (Maintenance)", disabled=True)

with tab2:
    st.info("💡 **Panduan Download:** Belum punya file videonya? Ikuti langkah ini:")
    st.markdown("""
    1. Buka [**ytdown.to**](https://app.ytdown.to/)
    2. Paste link YouTube lo di sana dan *download* videonya.
    3. Setelah berhasil download, **Upload** file videonya di bawah ini:
    """)
    
    uploaded_file = st.file_uploader("Upload video mentah (Max 200MB, disarankan durasi < 20 menit):", type=['mp4', 'mov'])
    
    if uploaded_file and st.button("Bikin Viral Sekarang"):
        public_url = ""
        progress_text = st.empty()
        
        # 1. Upload ke GoFile
        progress_text.text("Step 1/3: Uploading to Bypass Server (GoFile)...")
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            upload_resp = requests.post("https://store1.gofile.io/uploadFile", files=files)
            
            if upload_resp.status_code == 200:
                result = upload_resp.json()
                if result['status'] == 'ok':
                    public_url = result['data']['downloadPage']
                else:
                    st.error(f"Gagal upload ke server bypass: {result.get('status')}")
                    st.stop()
            else:
                st.error("Gagal koneksi ke server upload (GoFile).")
                st.stop()
        except Exception as e:
            st.error(f"Error Bypass Server: {e}")
            st.stop()

        if public_url:
            progress_text.text("Step 2/3: Menyiapkan Mesin AI di RunPod...")
            runpod_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run"
            headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
            response = requests.post(runpod_url, json={"input": {"video_url": public_url}}, headers=headers)
            
            if response.status_code == 200:
                job_id = response.json().get("id")
                progress_text.text("Step 3/3: Mesin AI sedang bekerja memotong video... (Jangan tutup tab ini)")
                
                status_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id}"
                while True:
                    try:
                        status_resp = requests.get(status_url, headers=headers).json()
                        status = status_resp.get("status")
                        
                        if status == "COMPLETED":
                            progress_text.text("🔥 Panen Klip Selesai!")
                            output_data = status_resp.get("output", {})
                            clips = output_data.get("urls", [])
                            total_clips = output_data.get("total_clips", len(clips))
                            
                            st.success(f"Berhasil panen {total_clips} klip!")
                            
                            cols = st.columns(3)
                            for i, clip_url in enumerate(clips):
                                if i < 3:
                                    with cols[i % 3]:
                                        st.video(clip_url)
                                        st.markdown(f"📥 [**Download {i+1}**]({clip_url})")
                                else:
                                    st.markdown(f"📥 [**Download Klip {i+1}**]({clip_url})")
                            break
                        elif status in ["FAILED", "CANCELLED"]:
                            st.error("Proses AI gagal di tengah jalan (Error dari RunPod).")
                            break
                        time.sleep(5)
                    except Exception as e:
                        st.error("Koneksi terputus dari server. Silakan muat ulang halaman dan coba lagi.")
                        break 
            else:
                st.error("Koneksi awal ke RunPod gagal.")