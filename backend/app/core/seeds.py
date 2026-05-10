import sqlite3

def seed_default_rules(conn: sqlite3.Connection) -> None:
    rule_count = conn.execute("SELECT COUNT(*) as cnt FROM rules").fetchone()["cnt"]
    if rule_count == 0:
        from ..models.scan_task import now_iso
        now = now_iso()
        default_rules = [
            # Content Keyword Rules (highest priority)
            ("学术论文", "content_keyword", "论文,毕业,开题,thesis,dissertation", "University/Thesis", "move_to", 90),
            ("财务凭证", "content_keyword", "发票,invoice,receipt,收据,税号", "Finance/Receipts", "move_to", 90),
            ("求职简历", "content_keyword", "简历,resume,curriculum vitae", "Personal/Resume", "move_to", 90),
            ("哲学经典", "content_keyword", "康德,Kant,纯粹理性批判", "Books/Philosophy", "move_to", 90),
            # Filename Keyword Rules
            ("工作报告", "filename_keyword", "报告,report,总结", "Work/Reports", "move_to", 80),
            ("屏幕截图", "filename_keyword", "照片,photo,screenshot,截图", "Images/Screenshots", "move_to", 80),
            # Extension Rules
            ("文档_PDF", "extension", ".pdf", "Documents/PDF", "move_to", 50),
            ("文档_Word", "extension", ".doc,.docx", "Documents/Word", "move_to", 50),
            ("文档_Excel", "extension", ".xls,.xlsx", "Documents/Excel", "move_to", 50),
            ("文档_PPT", "extension", ".ppt,.pptx", "Documents/PowerPoint", "move_to", 50),
            ("笔记文本", "extension", ".md,.txt", "Notes", "move_to", 50),
            ("图片文件", "extension", ".png,.jpg,.jpeg,.webp,.gif,.bmp,.svg", "Images", "move_to", 50),
            ("压缩归档", "extension", ".zip,.rar,.7z,.tar,.gz", "Archives", "move_to", 50),
            ("视频文件", "extension", ".mp4,.mov,.avi,.mkv,.webm", "Videos", "move_to", 50),
            ("音频文件", "extension", ".mp3,.wav,.flac,.aac", "Audio", "move_to", 50),
            ("代码源码", "extension", ".py,.js,.ts,.java,.cpp,.c,.h,.rs,.go", "Code", "move_to", 50),
        ]
        for r in default_rules:
            conn.execute(
                """INSERT INTO rules (name, rule_type, pattern, target_dir, action, priority, enabled, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 1, ?)""",
                (r[0], r[1], r[2], r[3], r[4], r[5], now)
            )
