import streamlit as st
import requests
import time
from supabase import create_client

# --- CONFIG & KEYS ---
SUPABASE_URL = "https://dfqegfdehvpttslbzzjv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmcWVnZmRlaHZwdHRzbGJ6emp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2OTQwOTgsImV4cCI6MjA5MzI3MDA5OH0.QhklGaVToBBwesBcXh-Y34RRGQSL9EKU7CfYbDJzvC0"
RUNPOD_API_KEY = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv"
RUNPOD_ENDPOINT_ID = "mj3o3oohv9up54"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- LOGIN LOGIC ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    # (Kode Login Tetap Sama Seperti Sebelumnya)
    st.markdown("🔒 **Silakan Login**")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.session:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- APP ---
st.title("🔥 Jagoan Clipper (Professional Backend)")

tab1, tab2 = st.tabs(["📁 Upload & Proses", "🔍 Cek Hasil Panen"])

with tab1:
    uploaded_file = st.file_uploader("Upload Video", type=['mp4', 'mov'])
    if uploaded_file and st.button("Proses Video"):
        # 1. Upload
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        upload_resp = requests.post("https://store1.gofile.io/uploadFile", files=files).json()
        public_url = upload_resp['data']['downloadPage']
        
        # 2. Trigger RunPod
        runpod_resp = requests.post(
            f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run",
            json={"input": {"video_url": public_url}},
            headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
        ).json()
        
        job_id = runpod_resp.get("id")
        
        # 3. SAVE KE SUPABASE (Database as the source of truth)
        supabase.table("job_status").insert({
            "id": job_id,
            "email": st.session_state.authenticated, # Simpan email user
            "status": "QUEUED"
        }).execute()
        
        st.success(f"✅ Video sedang diproses! Job ID lo: `{job_id}`")
        st.info("Lo bisa tutup tab ini. Cek status di tab sebelah nanti.")

with tab2:
    job_id_input = st.text_input("Masukkan Job ID untuk cek hasil")
    if st.button("Cek Status"):
        # Cek ke Supabase dulu, kalau blm ada baru cek ke RunPod
        data = supabase.table("job_status").select("*").eq("id", job_id_input).single().execute()
        
        # Logika: Kalau di Supabase belum ada update, check RunPod
        headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
        status_resp = requests.get(f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/{job_id_input}", headers=headers).json()
        
        if status_resp.get("status") == "COMPLETED":
            st.success("Panen Selesai!")
            st.write(status_resp.get("output"))
            # Update Supabase ke COMPLETED (bisa lo tambahin fungsi .update() di sini)
        else:
            st.warning(f"Status: {status_resp.get('status')}")