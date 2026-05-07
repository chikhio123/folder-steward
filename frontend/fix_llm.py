import re
with open("D:/Code/Folder Steward/backend/app/services/llm_provider_service.py", "r", encoding="utf-8") as f:
    content = f.read()

correct_rule_draft = """    def generate_rule_draft(self, user_prompt: str) -> Dict[str, Any]:
        s = self._get_settings()
        if s["provider"] != "mock":
            prompt = f\"\"\"
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
            \"\"\"
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

        # Mock generating a rule draft from a natural language prompt."""

# Find def generate_rule_draft and replace until Mock generating
content = re.sub(r'    def generate_rule_draft\(self, user_prompt: str\) -> Dict\[str, Any\]:.*?(?=        # Mock generating a rule draft)', correct_rule_draft + "\n\n", content, flags=re.DOTALL)

with open("D:/Code/Folder Steward/backend/app/services/llm_provider_service.py", "w", encoding="utf-8") as f:
    f.write(content)
