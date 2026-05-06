from typing import Optional
from ..core.database import get_connection
from ..models.ai_task import AITask

class AITaskRepository:
    def create(self, task: AITask) -> int:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO ai_tasks
               (task_type, status, input_json, result_ref_type, result_ref_id,
                total_items, processed_items, error_message, retry_count, estimated_tokens,
                actual_tokens, estimated_cost, started_at, finished_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task.task_type, task.status, task.input_json, task.result_ref_type,
             task.result_ref_id, task.total_items, task.processed_items,
             task.error_message, task.retry_count, task.estimated_tokens, task.actual_tokens,
             task.estimated_cost, task.started_at, task.finished_at,
             task.created_at, task.updated_at),
        )
        conn.commit()
        return cur.lastrowid

    def get(self, task_id: int) -> Optional[AITask]:
        row = get_connection().execute(
            "SELECT * FROM ai_tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        # Provide a default for retry_count if column doesn't exist yet
        row_dict = dict(row)
        if "retry_count" not in row_dict:
            row_dict["retry_count"] = 0
        return AITask(**row_dict)

    def update(self, task: AITask) -> None:
        conn = get_connection()
        conn.execute(
            """UPDATE ai_tasks SET
               task_type=?, status=?, input_json=?, result_ref_type=?, result_ref_id=?,
               total_items=?, processed_items=?, error_message=?, retry_count=?, estimated_tokens=?,
               actual_tokens=?, estimated_cost=?, started_at=?, finished_at=?, updated_at=?
               WHERE id=?""",
            (task.task_type, task.status, task.input_json, task.result_ref_type, task.result_ref_id,
             task.total_items, task.processed_items, task.error_message, task.retry_count, task.estimated_tokens,
             task.actual_tokens, task.estimated_cost, task.started_at, task.finished_at,
             task.updated_at, task.id),
        )
        conn.commit()
