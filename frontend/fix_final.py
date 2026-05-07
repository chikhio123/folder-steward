with open("D:/Code/Folder Steward/backend/app/services/llm_provider_service.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

# Remove the duplicate mock generate_classification at the bottom
# It starts at line 228 and ends before generate_summary
content = re.sub(r'    def generate_classification\(self, file_context: dict, rules_context: list, archive_root: str\) -> Dict\[str, Any\]:\n        """Mock generating a classification suggestion based on file content."""\n.*?(?=    def generate_summary)', '', content, flags=re.DOTALL)

with open("D:/Code/Folder Steward/backend/app/services/llm_provider_service.py", "w", encoding="utf-8") as f:
    f.write(content)
