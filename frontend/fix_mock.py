with open("D:/Code/Folder Steward/backend/app/services/llm_provider_service.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
bad_mock = """        if "kant" in filename.lower() or "kant" in content.lower():
            target_dir = "Books/Philosophy"
            reason = "正文或文件名包含哲学相关关键词\"\"\""""

replacement = """        if "kant" in filename.lower() or "kant" in content.lower():
            target_dir = "Books/Philosophy"
            reason = "正文或文件名包含哲学相关关键词"
        elif "简历" in filename or "python" in content.lower():
            target_dir = "Personal/Resume"
            reason = "识别到简历相关特征"
        elif "报销" in filename or "发票" in filename:
            target_dir = "Finance/Receipts"
            reason = "识别到财务相关凭证"

        return {
            "suggested_target_dir": target_dir,
            "confidence": 0.88,
            "reason": reason
        }"""

content = re.sub(r'        if "kant" in filename\.lower\(\) or "kant" in content\.lower\(\):.*?reason = "正文或文件名包含哲学相关关键词"', replacement, content, flags=re.DOTALL)

with open("D:/Code/Folder Steward/backend/app/services/llm_provider_service.py", "w", encoding="utf-8") as f:
    f.write(content)
