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

prompt = """
You are a smart file organization assistant. Analyze the file and suggest a target directory.
File Name: test.txt
File Content Preview: This is a test file
Archive Root: D:/Archive

Return ONLY raw JSON with exactly these keys, no markdown blocks, no other text:
{
    "suggested_target_dir": "Documents/Work",
    "confidence": 0.95,
    "reason": "Why did you choose this directory?"
}
"""

payload = {
    "model": s["llm_model"],
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.1
}

try:
    with httpx.Client(timeout=10.0) as client:
        res = client.post(endpoint, headers=headers, json=payload)
        print("Status:", res.status_code)
        print("Response:", res.text)
except Exception as e:
    print("Error:", str(e))
