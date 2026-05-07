import re

with open("D:/Code/Folder Steward/backend/app/services/llm_provider_service.py", "r", encoding="utf-8") as f:
    content = f.read()

replacement = """    def generate_classification(self, file_context: dict, rules_context: list, archive_root: str) -> Dict[str, Any]:
        s = self._get_settings()
        with open("C:/Users/lu/provider_debug.txt", "a") as f:
            f.write(s["provider"] + "\n")
            
        if s["provider"] != "mock":
"""

content = re.sub(r'    def generate_classification\(self, file_context: dict, rules_context: list, archive_root: str\) -> Dict\[str, Any\]:\n        s = self\._get_settings\(\)\n        if s\["provider"\] != "mock":', replacement, content)

with open("D:/Code/Folder Steward/backend/app/services/llm_provider_service.py", "w", encoding="utf-8") as f:
    f.write(content)
