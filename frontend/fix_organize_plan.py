import re

with open("D:/Code/Folder Steward/backend/app/services/organize_plan_service.py", "r", encoding="utf-8") as f:
    content = f.read()

replacement = """
    def generate_plan(self, scope: str, min_confidence: float = 0.65, task=None) -> int:
        \"\"\"Classifies files and aggregates suggestions into a structured plan.\"\"\"
        from .ai_classification_service import AIClassificationService
        class_service = AIClassificationService()
        
        conn = get_connection()
        row = conn.execute("SELECT value FROM app_settings WHERE key = 'archive_root'").fetchone()
        archive_root = row["value"] if row else ""

        # Find files to classify based on scope
        if scope == "others":
            # Files not matched by any rules yet (this is simplified)
            file_rows = conn.execute("SELECT id FROM file_records WHERE status = 'active'").fetchall()
        else:
            file_rows = conn.execute("SELECT id FROM file_records WHERE status = 'active'").fetchall()

        file_ids = [r["id"] for r in file_rows]

        if task:
            task.total_items = len(file_ids)
            from ..repositories.ai_task_repository import AITaskRepository
            task_repo = AITaskRepository()
            task_repo.update(task)

        # Clear existing pending suggestions so we start fresh
        conn.execute("DELETE FROM ai_classification_suggestions WHERE status = 'pending'")
        conn.commit()

        # Classify all target files
        for fid in file_ids:
            class_service.process_classification_task(fid, archive_root)
            if task:
                task.processed_items += 1
                task_repo.update(task)

        # Fetch pending AI suggestions that meet confidence
        rows = conn.execute(
            \"\"\"SELECT a.*, f.current_path
               FROM ai_classification_suggestions a
               JOIN file_records f ON a.file_id = f.id
               WHERE a.status = 'pending' AND a.confidence >= ?
            \"\"\", (min_confidence,)
        ).fetchall()

        if not rows:
            raise ValueError("No pending AI classification suggestions found with sufficient confidence.")
"""

content = re.sub(
    r'    def generate_plan\(self, scope: str, min_confidence: float = 0\.65\) -> int:.*?(?=        plan = OrganizePlan\()',
    replacement,
    content,
    flags=re.DOTALL
)

with open("D:/Code/Folder Steward/backend/app/services/organize_plan_service.py", "w", encoding="utf-8") as f:
    f.write(content)
