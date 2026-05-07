import re

with open("D:/Code/Folder Steward/backend/app/services/scan_service.py", "r", encoding="utf-8") as f:
    content = f.read()

cleanup_func = """
    def _cleanup_missing_files(self, root: Path) -> int:
        \"\"\"Check active files under root and mark as deleted if missing from disk.\"\"\"
        from ..core.database import get_connection
        conn = get_connection()
        rows = conn.execute("SELECT id, current_path FROM file_records WHERE status = 'active'").fetchall()
        
        root_str = str(root.resolve())
        deleted_ids = []
        for r in rows:
            path_str = r["current_path"]
            if path_str.startswith(root_str):
                if not Path(path_str).exists():
                    deleted_ids.append(r["id"])
                    
        if deleted_ids:
            # Batch update in chunks of 500 to avoid sqlite limits
            chunk_size = 500
            for i in range(0, len(deleted_ids), chunk_size):
                chunk = deleted_ids[i:i+chunk_size]
                placeholders = ",".join("?" for _ in chunk)
                conn.execute(f"UPDATE file_records SET status = 'deleted' WHERE id IN ({placeholders})", chunk)
            conn.commit()
            
            # Also clean up FTS for deleted files using triggers we added
        return len(deleted_ids)

    def _run_scan(self, task_id: int) -> None:"""

content = re.sub(r'    def _run_scan\(self, task_id: int\) -> None:', cleanup_func, content)

run_scan_update = """                self.task_repo.update_progress(task.id, scanned, failed)
        except Exception as e:
            if self._is_cancelled(task_id):
                self._finish_cancelled(task)
                return
            task.status = "failed"
            task.error_message = f"Scan failed: {e}"
            task.finished_at = now_iso()
            self.task_repo.fail_if_running(task)
            self._running_tasks.pop(task_id, None)
            return

        # Done — check cancelled before overwriting status
        if self._is_cancelled(task_id):
            self._finish_cancelled(task)
            return

        # Cleanup missing files (e.g. deleted from file explorer)
        cleaned = self._cleanup_missing_files(root)

        task.status = "completed"
        task.total_files = scanned + failed
        task.scanned_files = scanned
        task.failed_files = failed
        task.error_message = f"Cleaned {cleaned} missing files." if cleaned > 0 else None
        task.finished_at = now_iso()
        self.task_repo.complete_if_running(task)"""

content = re.sub(r'                self\.task_repo\.update_progress\(task\.id, scanned, failed\).*?self\.task_repo\.complete_if_running\(task\)', run_scan_update, content, flags=re.DOTALL)

with open("D:/Code/Folder Steward/backend/app/services/scan_service.py", "w", encoding="utf-8") as f:
    f.write(content)
