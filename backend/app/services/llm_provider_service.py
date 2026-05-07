import json
import httpx
from typing import Dict, Any
from ..core.database import get_connection

class RateLimitException(Exception):
    """Raised when the LLM provider returns a 429 Too Many Requests."""
    pass

class LLMProviderService:
    """Wrapper for LLM calls."""

    def __init__(self, provider_type: str = "mock"):
        self.provider_type = provider_type
        # Lazy load settings to get latest
    
    def _get_settings(self):
        conn = get_connection()
        rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        s = {row["key"]: row["value"] for row in rows}
        return {
            "provider": s.get("llm_provider", "mock"),
            "api_key": s.get("llm_api_key", ""),
            "base_url": s.get("llm_base_url", ""),
            "model": s.get("llm_model", "gpt-4o-mini")
        }

    def _call_api(self, messages, response_format=None) -> str:
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
                raise Exception(f"Failed to call LLM: {str(e)}")

    def generate_classification(self, file_context: dict, rules_context: list, archive_root: str) -> Dict[str, Any]:
        s = self._get_settings()
        if s["provider"] != "mock":

            prompt = f"""
            You are a smart file organization assistant. Analyze the file and suggest a target directory.
            File Name: {file_context.get('filename')}
            File Content Preview: {(file_context.get('content_preview') or '')[:1000]}
            Archive Root: {archive_root}

            Return ONLY raw JSON with exactly these keys, no markdown blocks, no other text:
            {{
                "suggested_target_dir": "Documents/Work",
                "confidence": 0.95,
                "reason": "Why did you choose this directory?"
            }}
            """
            try:
                result_str = self._call_api(
                    [{"role": "user", "content": prompt}]
                )
                import json
                # Clean markdown blocks if the model ignored our instructions
                if result_str.startswith("```json"):
                    result_str = result_str[7:]
                if result_str.endswith("```"):
                    result_str = result_str[:-3]
                return json.loads(result_str.strip())
            except Exception as e:
                print(f"LLM Classification Error: {e}")
                # Raise the error so it can be handled by the task queue
                raise e

        # Mock Fallback
        filename = file_context.get("filename", "")
        content = file_context.get("content_preview") or ""
        ext = ""
        if "." in filename:
            ext = filename.rsplit(".", 1)[-1].lower()

        target_dir = "Others/AI_Sorted"
        reason = "默认 AI 分类 (未能命中测试关键词)"

        if "kant" in filename.lower() or "kant" in content.lower():
            target_dir = "Books/Philosophy"
            reason = "正文或文件名包含哲学相关关键词"
        elif "简历" in filename or "python" in content.lower() or "resume" in filename.lower():
            target_dir = "Personal/Resume"
            reason = "识别到简历相关特征"
        elif "报销" in filename or "发票" in filename or "receipt" in filename.lower():
            target_dir = "Finance/Receipts"
            reason = "识别到财务相关凭证"
        elif ext in ["png", "jpg", "jpeg", "webp", "gif"]:
            target_dir = "Images/Misc"
            reason = "识别为图片文件"
        elif ext in ["md", "txt"]:
            target_dir = "Notes/Text"
            reason = "识别为纯文本笔记"
        elif ext in ["pdf", "doc", "docx"]:
            target_dir = "Documents/General"
            reason = "识别为文档文件"

        return {
            "suggested_target_dir": target_dir,
            "confidence": 0.88,
            "reason": reason
        }

    def generate_classifications_batch(self, file_contexts: list[dict], rules_context: list, archive_root: str) -> list[dict]:
        """Batch classify multiple files in a single LLM request.

        Returns a list of dicts matching generate_classification() output format,
        with an additional 'file_id' field for correlation.
        """
        s = self._get_settings()
        if s["provider"] != "mock":
            # Build batch prompt
            files_desc = []
            for fc in file_contexts:
                fid = fc.get('file_id', 'unknown')
                fname = fc.get('filename', '')
                preview = (fc.get('content_preview') or '')[:500]
                ext = fc.get('extension', '')
                current_path = fc.get('current_path', '')
                files_desc.append(
                    f"File ID: {fid}\nFilename: {fname}\nExtension: {ext}\nCurrent Path: {current_path}\nContent Preview: {preview}"
                )

            files_block = "\n---\n".join(files_desc)

            prompt = f"""
You are a smart file organization assistant. Analyze the following files and suggest a target directory for EACH file.

Archive Root: {archive_root}

Files to classify:
---
{files_block}
---

Return ONLY raw JSON in this exact format, no markdown blocks, no other text:
{{
    "items": [
        {{
            "file_id": 1,
            "suggested_target_dir": "Documents/Work",
            "confidence": 0.95,
            "reason": "Why did you choose this directory?"
        }},
        {{
            "file_id": 2,
            "suggested_target_dir": "Images/Photos",
            "confidence": 0.88,
            "reason": "Detected as image file with photo metadata"
        }}
    ]
}}

IMPORTANT:
- Return one item for EVERY file_id in the input, in the same order.
- Use the file_id values exactly as provided in the input.
- suggested_target_dir should be a relative path from archive_root.
"""
            try:
                result_str = self._call_api(
                    [{"role": "user", "content": prompt}]
                )
                import json
                # Clean markdown blocks if the model ignored our instructions
                if result_str.startswith("```json"):
                    result_str = result_str[7:]
                if result_str.endswith("```"):
                    result_str = result_str[:-3]
                result = json.loads(result_str.strip())
                items = result.get("items", [])
                # Validate: ensure all items have file_id
                for item in items:
                    if "file_id" not in item:
                        raise ValueError("LLM batch response missing file_id in items")
                return items
            except Exception as e:
                print(f"LLM Batch Classification Error: {e}")
                raise e

        # Mock batch fallback - classify each file using the same logic as single
        results = []
        for fc in file_contexts:
            single_result = self.generate_classification(fc, rules_context, archive_root)
            single_result["file_id"] = fc.get("file_id", 0)
            results.append(single_result)
        return results

    def generate_rule_draft(self, user_prompt: str) -> Dict[str, Any]:
        s = self._get_settings()
        if s["provider"] != "mock":
            prompt = f"""
            You are a smart file organization assistant. Create a file matching rule based on the user's prompt.
            User Prompt: {user_prompt}
            
            Return ONLY raw JSON with exactly these keys, no markdown blocks, no other text:
            {{
                "name": "Short rule name",
                "rule_type": "One of: extension, filename_keyword, content_keyword",
                "pattern": "Comma separated values",
                "target_dir": "e.g. Documents/Work",
                "action": "move_to",
                "priority": 95,
                "reason": "string",
                "confidence": 0.85
            }}
            """
            try:
                result_str = self._call_api(
                    [{"role": "user", "content": prompt}]
                )
                import json
                if result_str.startswith("```json"):
                    result_str = result_str[7:]
                if result_str.endswith("```"):
                    result_str = result_str[:-3]
                return json.loads(result_str.strip())
            except Exception as e:
                print(f"LLM Rule Draft Error: {e}")
                raise e

        # Mock generating a rule draft from a natural language prompt.

        # Mock generating a rule draft from a natural language prompt.
        target = "University/Thesis" if "论文" in user_prompt else "Custom/Target"
        pattern = "论文,毕业" if "论文" in user_prompt else "keyword1,keyword2"

        return {
            "name": "AI生成的规则草案",
            "rule_type": "content_keyword",
            "pattern": pattern,
            "target_dir": target,
            "action": "move_to",
            "priority": 95,
            "reason": f"基于用户输入推断：{user_prompt}",
            "confidence": 0.85
        }


    def generate_summary(self, file_context: dict) -> str:
        """Mock generating a summary for a file."""
        filename = file_context.get("filename", "Unknown")
        content = file_context.get("content_preview") or ""

        if len(content) > 100:
            return f"这是一份关于 {filename} 的 AI 摘要。核心内容涉及：{content[:50]}..."
        elif content:
            return f"简短文件摘要：{content}"
        return f"文件 {filename} 的元数据摘要，暂无正文提取信息。"
