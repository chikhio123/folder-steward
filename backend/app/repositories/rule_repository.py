from typing import Optional
from ..core.database import get_connection
from ..models.rule import Rule
from ..models.scan_task import now_iso

class RuleRepository:
    def create(self, rule: Rule) -> int:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO rules
               (name, rule_type, pattern, target_dir, action, priority, enabled, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (rule.name, rule.rule_type, rule.pattern, rule.target_dir,
             rule.action, rule.priority, rule.enabled, rule.created_at or now_iso()),
        )
        conn.commit()
        return cur.lastrowid

    def get(self, rule_id: int) -> Optional[Rule]:
        row = get_connection().execute(
            "SELECT * FROM rules WHERE id = ?", (rule_id,)
        ).fetchone()
        if not row:
            return None
        return Rule(**dict(row))

    def update(self, rule: Rule) -> None:
        conn = get_connection()
        conn.execute(
            """UPDATE rules SET name=?, rule_type=?, pattern=?, target_dir=?,
               action=?, priority=?, enabled=?, updated_at=?
               WHERE id=?""",
            (rule.name, rule.rule_type, rule.pattern, rule.target_dir,
             rule.action, rule.priority, rule.enabled, now_iso(), rule.id),
        )
        conn.commit()

    def list_all(self, only_enabled: bool = True) -> list[Rule]:
        conn = get_connection()
        if only_enabled:
            rows = conn.execute("SELECT * FROM rules WHERE enabled = 1 ORDER BY priority DESC").fetchall()
        else:
            rows = conn.execute("SELECT * FROM rules ORDER BY priority DESC").fetchall()
        return [Rule(**dict(r)) for r in rows]

    def delete(self, rule_id: int) -> None:
        conn = get_connection()
        conn.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
        conn.commit()
