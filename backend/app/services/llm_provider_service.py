import json
import httpx
import os
import asyncio
from typing import Dict, Any
from ..core.database import get_connection
from .ai_task_queue_service import cancel_event_var

class TaskCancelledException(Exception):
    """Raised when an AI task is cancelled by the user mid-flight."""
    pass

class RateLimitException(Exception):
    """Raised when the LLM provider returns a 429 Too Many Requests."""
    pass

class LLMProviderService:
    """Wrapper for LLM calls."""

    def __init__(self, provider_type: str = "mock", settings_repo=None):
        self.provider_type = provider_type
        from ..repositories.settings_repository import SettingsRepository
        self.settings_repo = settings_repo or SettingsRepository()
    
    def _get_settings(self):
        s = self.settings_repo.get_all()
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

        async def do_request():
            nonlocal base_url
            cancel_event = cancel_event_var.get()

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
            else:
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
                async with httpx.AsyncClient(timeout=120.0) as client:
                    req_task = asyncio.create_task(client.post(endpoint, headers=headers, json=payload))

                    while not req_task.done():
                        if cancel_event and cancel_event.is_set():
                            req_task.cancel()
                            raise TaskCancelledException("Task was cancelled by user")
                        await asyncio.sleep(0.5)

                    res = await req_task

                    if res.status_code == 429:
                        raise RateLimitException("Rate limited by provider")
                    res.raise_for_status()
                    data = res.json()

                    if provider == "anthropic-messages":
                        return data["content"][0]["text"]
                    else:
                        return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise RateLimitException("Rate limited by provider")
                raise Exception(f"API Error: {e.response.text}")
            except RateLimitException:
                raise
            except TaskCancelledException:
                raise
            except Exception as e:
                raise Exception(f"Failed to call LLM: {str(e)}")

        # Run the async request in a new event loop for this thread
        return asyncio.run(do_request())

    def generate_classification(self, file_context: dict, rules_context: list, archive_root: str) -> Dict[str, Any]:
        s = self._get_settings()
        if s["provider"] != "mock":

            prompt = f"""
            You are a smart file organization assistant. Analyze the file and suggest a target directory.
            File Name: {file_context.get('filename')}
            File Content Preview: {(file_context.get('content_preview') or '')[:1000]}
            Archive Root: {archive_root}

            Ensure that your suggested directory name adheres to any global conventions inferred from the prompt or standard practice. If the user expects Chinese names, use Chinese directory names.

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
            # Compute folder summary from file_contexts
            folder_summary = self._compute_folder_summary(file_contexts)

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

Folder Context:
{folder_summary}

Files to classify:
---
{files_block}
---

Ensure that your suggested directory names adhere to any global conventions inferred or requested by the user. If the user expects Chinese names, use Chinese directory names.

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

    def _compute_folder_summary(self, file_contexts: list[dict]) -> str:
        """Compute a summary of folder context from file_contexts."""
        # Group by parent directory
        dirs = {}
        for fc in file_contexts:
            path = fc.get("current_path", "")
            if not path:
                # Files without a valid path go to a special group
                parent = "_ungrouped_"
            else:
                normalized = os.path.normpath(path).lower()
                parent = os.path.dirname(normalized)
                parent = parent or "_root_"
            if parent not in dirs:
                dirs[parent] = {"files": 0, "exts": set(), "names": []}
            dirs[parent]["files"] += 1
            ext = fc.get("extension", "")
            if ext:
                dirs[parent]["exts"].add(ext)
            fname = fc.get("filename", "")
            if fname:
                dirs[parent]["names"].append(fname)

        # Build summary text
        lines = []
        for dir_path in sorted(dirs.keys()):
            info = dirs[dir_path]
            ext_str = ", ".join(sorted(info["exts"])) if info["exts"] else "none"
            lines.append(f"Folder: {dir_path}")
            lines.append(f"  File count: {info['files']}")
            lines.append(f"  Common extensions: {ext_str}")
            # Show up to 5 filenames as sample
            samples = info["names"][:5]
            if samples:
                lines.append(f"  Sample files: {', '.join(samples)}")
            if len(info["names"]) > 5:
                lines.append(f"  ... and {len(info['names']) - 5} more")
        return "\n".join(lines)

    def generate_rule_draft(
        self,
        user_prompt: str,
        rules_context: list | None = None,
        directories_context: list | None = None
    ) -> Dict[str, Any]:
        s = self._get_settings()
        if s["provider"] != "mock":
            context_block = ""
            if rules_context:
                # 只传核心摘要，不传长篇大论
                context_block += "Existing Active Rules:\n"
                for r in rules_context:
                    context_block += f"- Rule: {r.get('name')} -> moves to '{r.get('target_dir')}' (Pattern: {r.get('pattern')})\n"
                context_block += "\n"

            if directories_context:
                context_block += "Known Common Directories in Library:\n"
                for d in directories_context:
                    context_block += f"- {d}\n"
                context_block += "\n"

            prompt = f"""
            You are a smart file organization assistant. Create a file matching rule based on the user's prompt.
            User Prompt: {user_prompt}

            {context_block}
            Important: Prefer reusing existing Known Common Directories as target_dir if they conceptually match the user's request. Avoid creating slightly different synonyms (e.g. if 'Finance/Receipts' exists, don't invent 'Financial/Invoices' unless necessary).
            If the user asks to use a specific naming convention (e.g. "use Chinese directory names" or "name everything in Chinese"), ensure the `target_dir` you generate strictly adheres to that instruction.

            Return ONLY raw JSON with exactly these keys, no markdown blocks, no other text.
            The "rule_type" MUST be exactly one of the following strings: "extension", "filename_keyword", or "content_keyword". Do not include any other text in the rule_type value.
            {{
                "name": "Short rule name",
                "rule_type": "content_keyword",
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
