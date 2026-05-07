import re

with open("D:/Code/Folder Steward/backend/app/services/llm_provider_service.py", "r", encoding="utf-8") as f:
    content = f.read()

# Remove response_format logic from _call_openai_api
replacement1 = """        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1
        }
        # Some proxies (like Gemini proxies) reject response_format
        # if response_format:
        #     payload["response_format"] = response_format"""

content = re.sub(r'        payload = \{\n            "model": model,\n            "messages": messages,\n            "temperature": 0\.1\n        \}\n        if response_format:\n            payload\["response_format"\] = response_format', replacement1, content)

# Update prompts to enforce JSON explicitly since we removed response_format
replacement2 = """        if s["provider"] == "openai":
            prompt = f\"\"\"
            You are a smart file organization assistant. Analyze the file and suggest a target directory.
            File Name: {file_context.get('filename')}
            File Content Preview: {file_context.get('content_preview', '')[:1000]}
            Archive Root: {archive_root}
            
            Return ONLY raw JSON with exactly these keys, no markdown blocks, no other text:
            {{
                "suggested_target_dir": "Documents/Work",
                "confidence": 0.95,
                "reason": "Why did you choose this directory?"
            }}
            \"\"\"
            try:
                result_str = self._call_openai_api(
                    [{"role": "user", "content": prompt}]
                )
                import json
                # Clean markdown blocks if the model ignored our instructions
                if result_str.startswith("```json"):
                    result_str = result_str[7:]
                if result_str.endswith("```"):
                    result_str = result_str[:-3]
                return json.loads(result_str.strip())"""

content = re.sub(r'        if s\["provider"\] == "openai":\n            prompt = f"""\n            You are a smart file organization assistant.*?return json\.loads\(result_str\)', replacement2, content, flags=re.DOTALL)

with open("D:/Code/Folder Steward/backend/app/services/llm_provider_service.py", "w", encoding="utf-8") as f:
    f.write(content)
