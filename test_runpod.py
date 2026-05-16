import runpod

runpod.api_key = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv"
ENDPOINT_ID = "rcvmpej9vswrlj"

def run_test():
    print("🚀 SCRIPT DIMULAI (VERSI V7 - FINAL TEST)...")
    
    try:
        print(f"📡 Menghubungi Endpoint: {ENDPOINT_ID}...")
        endpoint = runpod.Endpoint(ENDPOINT_ID)
        
        input_data = {
            "input": {
                "video_url": "https://www.youtube.com/shorts/8v_4QZ_T4_0",
                "command": "clip"
            }
        }
        
        job = endpoint.run(input_data)
        print(f"⌛ Job terkirim! ID: {job.job_id}")
        print("💡 Mesin v7 sedang memproses download dan upload asli...")
        print("⏳ Mohon sabar menanti sekitar 1 menit karena ini proses asli...")
        
        output = job.output(timeout=600)
        
        print("\n✅ SELESAI! Liat hasilnya di bawah:")
        print("-" * 50)
        print(output)
        print("-" * 50)

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    run_test()
