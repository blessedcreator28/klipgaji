import requests
import os

# GANTI DENGAN KUNCI LO
RUNPOD_API_KEY = "rpa_I4UJDB6G4QB0E6HJJBG3ZQJC1DRUS70A2NTXIDBPffi5bv"
ENDPOINT_ID = "mj3o3oohv9up54" # ID Endpoint lo

url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"
headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
payload = {"input": {"test": "ping"}}

print("--- Menghubungi RunPod... ---")
try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")