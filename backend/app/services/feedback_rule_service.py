import os
from collections import defaultdict
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
        # Fetch all successful move operations
        rows = conn.execute(
            """SELECT target_path
               FROM operation_logs
               WHERE operation_type = 'move' AND status = 'success'"""
        ).fetchall()

        dir_counts = defaultdict(int)
        for r in rows:
            target_path = r["target_path"]
            if target_path:
                # Extract the directory part
                target_dir = os.path.dirname(target_path)
                dir_counts[target_dir] += 1

        patterns = []
        for target_dir, count in dir_counts.items():
            if count >= 3:
                patterns.append({
                    "target_dir": target_dir,
                    "move_count": count,
                    "suggestion_prompt": f"用户最近手动将 {count} 个文件移动到了 {target_dir}，建议创建一个自动化规则来处理类似文件。"
                })

        # Sort by move_count descending and limit to 5
        patterns.sort(key=lambda x: x["move_count"], reverse=True)
        return patterns[:5]

    def generate_draft_from_pattern(self, target_dir: str, keyword: str) -> int:
        """Generates an AI rule draft explicitly targeting a user-defined pattern."""
        prompt = f"把文件名包含 {keyword} 的文件全部归档到 {target_dir}"
        return self.draft_service.generate_draft(prompt)
