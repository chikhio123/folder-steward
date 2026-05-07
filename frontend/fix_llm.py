import re

with open("D:/Code/Folder Steward/backend/app/services/llm_provider_service.py", "r", encoding="utf-8") as f:
    content = f.read()

call_api_code = """    def _call_api(self, messages, response_format=None) -> str:
        s = self._get_settings()
        provider = s["provider"]
        api_key = s["api_key"]
        base_url = s["base_url"].rstrip('/')
        model = s["model"]
        
        if provider == "anthropic-messages":
            if not base_url:
                base_url = "https://api.anthropic.com"
            endpoint = f"{base_url}/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            system_msg = ""
            anthropic_messages = []
            for m in messages:
                if m["role"] == "system":
                    system_msg += m["content"] + "\n"
                else:
                    anthropic_messages.append({"role": m["role"], "content": m["content"]})
                    
            payload = {
                "model": model,
                "max_tokens": 1024,
                "messages": anthropic_messages,
                "temperature": 0.1
            }
            if system_msg:
                payload["system"] = system_msg
                
            try:
                with httpx.Client(timeout=30.0) as client:
                    res = client.post(endpoint, headers=headers, json=payload)
                    if res.status_code == 429:
                        raise RateLimitException("Rate limited by provider")
                    res.raise_for_status()
                    data = res.json()
                    return data["content"][0]["text"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise RateLimitException("Rate limited by provider")
                raise Exception(f"API Error: {e.response.text}")
            except Exception as e:
                raise Exception(f"Failed to call LLM: {str(e)}")
                
        else: # openai, openai-raw, openai-response-format
            if not base_url.endswith("/v1"):
                base_url = f"{base_url}/v1"
                
            endpoint = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.1
            }
            
            if provider == "openai-response-format" and response_format:
                payload["response_format"] = response_format
                
            try:
                with httpx.Client(timeout=30.0) as client:
                    res = client.post(endpoint, headers=headers, json=payload)
                    if res.status_code == 429:
                        raise RateLimitException("Rate limited by provider")
                    res.raise_for_status()
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise RateLimitException("Rate limited by provider")
                raise Exception(f"API Error: {e.response.text}")
            except Exception as e:
                raise Exception(f"Failed to call LLM: {str(e)}")"""

content = re.sub(r'    def _call_openai_api\(self, messages, response_format=None\) -> str:.*?(?=    def generate_classification)', call_api_code + "\n\n", content, flags=re.DOTALL)

# Replace if s["provider"] == "openai":
content = content.replace('if s["provider"] == "openai":', 'if s["provider"] != "mock":')

# Replace _call_openai_api with _call_api
content = content.replace('self._call_openai_api(', 'self._call_api(')

with open("D:/Code/Folder Steward/backend/app/services/llm_provider_service.py", "w", encoding="utf-8") as f:
    f.write(content)
