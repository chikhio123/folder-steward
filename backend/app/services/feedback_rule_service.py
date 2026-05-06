from typing import List, Dict, Any
from ..core.database import get_connection
from .ai_rule_draft_service import AIRuleDraftService

class FeedbackRuleService:
    def __init__(self):
        self.draft_service = AIRuleDraftService()

    def analyze_recent_operations(self) -> List[Dict[str, Any]]:
        """
        Scans recent operation logs to find patterns where the user repeatedly moved
        files into the same target directory manually.
        Returns a list of potential new rule drafts based on these patterns.
        """
        conn = get_connection()
        # Find directories where at least 3 files were moved recently
        rows = conn.execute(
            """SELECT target_path, COUNT(*) as cnt
               FROM operation_logs
               WHERE operation_type = 'move' AND status = 'success'
               GROUP BY target_path
               HAVING cnt >= 3
               ORDER BY cnt DESC
               LIMIT 5"""
        ).fetchall()

        patterns = []
        for r in rows:
            target_path = r["target_path"]
            # Typically target_path looks like D:/Archive/MyDir/file.txt
            # We want to extract just the directory part, but since operation_logs
            # only stores target_path, we can do some simple splitting.
            # In a real scenario, we would parse out the archive_root.
            import os
            target_dir = os.path.dirname(target_path)

            patterns.append({
                "target_dir": target_dir,
                "move_count": r["cnt"],
                "suggestion_prompt": f"用户最近手动将 {r['cnt']} 个文件移动到了 {target_dir}，建议创建一个自动化规则来处理类似文件。"
            })

        return patterns

    def generate_draft_from_pattern(self, target_dir: str, keyword: str) -> int:
        """Generates an AI rule draft explicitly targeting a user-defined pattern."""
        prompt = f"把文件名包含 {keyword} 的文件全部归档到 {target_dir}"
        # We invoke the draft service synchronously here for MVP
        return self.draft_service.generate_draft(prompt)
