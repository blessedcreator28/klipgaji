import runpod

# Kunci akses RunPod lo
runpod.api_key = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv"

# ID MESIN V5 LO YANG BARU (Gue udah masukin)
ENDPOINT_ID = "2e9mtheg7e8o7b"

def run_test():
    print("🚀 SCRIPT DIMULAI (VERSI V5 - SUPABASE)...")
    
    try:
        print(f"📡 Menghubungi Endpoint v5: {ENDPOINT_ID}...")
        endpoint = runpod.Endpoint(ENDPOINT_ID)
        
        input_data = {
            "input": {
                "video_url": "https://www.youtube.com/shorts/8v_4QZ_T4_0",
                "command": "clip"
            }
        }
        
        job = endpoint.run(input_data)
        print(f"⌛ Job terkirim! ID: {job.job_id}")
        print("💡 Mesin v5 sedang memproses dan upload ke Supabase...")
        print("⏳ Tunggu sebentar (sekitar 1-2 menit)...")
        
        output = job.output(timeout=600)
        
        print("\n✅ BERHASIL! Ini link download dari Supabase:")
        print("-" * 50)
        print(output)
        print("-" * 50)

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    run_test()