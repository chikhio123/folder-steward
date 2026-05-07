import sys, sqlite3, httpx
conn = sqlite3.connect('C:/Users/lu/AppData/Roaming/folder-steward-frontend/folder_steward.db')
rows = conn.execute('SELECT key, value FROM app_settings').fetchall()
s = {r[0]: r[1] for r in rows}

base_url = s["llm_base_url"].rstrip('/')
if not base_url.endswith("/v1"):
    base_url = f"{base_url}/v1"
endpoint = f"{base_url}/chat/completions"

headers = {
    "Authorization": f"Bearer {s['llm_api_key']}",
    "Content-Type": "application/json"
}
payload = {
    "model": s["llm_model"],
    "messages": [{"role": "user", "content": "Hello, return a json string like {\"test\": 1}. Only output the raw json, no markdown blocks."}],
    "temperature": 0.1
}

try:
    with httpx.Client(timeout=10.0) as client:
        res = client.post(endpoint, headers=headers, json=payload)
        print("Status:", res.status_code)
        print("Response:", res.text)
except Exception as e:
    print("Error:", str(e))
