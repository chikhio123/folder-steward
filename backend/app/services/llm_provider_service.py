import json
from typing import Dict, Any

class RateLimitException(Exception):
    """Raised when the LLM provider returns a 429 Too Many Requests."""
    pass

class LLMProviderService:
    """Wrapper for LLM calls (mocked for V3 initial phase)."""

    def __init__(self, provider_type: str = "mock"):
        self.provider_type = provider_type

    def generate_rule_draft(self, user_prompt: str) -> Dict[str, Any]:
        """Mock generating a rule draft from a natural language prompt."""
        # Simple mock matching logic for demonstration
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

    def generate_classification(self, file_context: dict, rules_context: list, archive_root: str) -> Dict[str, Any]:
        """Mock generating a classification suggestion based on file content."""
        filename = file_context.get("filename", "")
        content = file_context.get("content_preview") or ""

        target_dir = "Others/AI_Sorted"
        reason = "默认 AI 分类"

        if "kant" in filename.lower() or "kant" in content.lower():
            target_dir = "Books/Philosophy"
            reason = "正文或文件名包含哲学相关关键词"

        return {
            "suggested_target_dir": target_dir,
            "directory_status": "proposed_new",
            "confidence": 0.8,
            "reason": reason,
            "evidence": ["(Mocked Evidence)"]
        }
