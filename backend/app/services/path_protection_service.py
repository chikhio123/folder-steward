import os
from typing import List, Tuple


class PathProtectionService:
    """集中管理 AI 排除目录的路径校验与过滤。"""

    SETTING_KEY = "ai_exclude_paths"

    def __init__(self, settings_repo=None, file_repo=None):
        from ..repositories.settings_repository import SettingsRepository
        from ..repositories.file_repository import FileRepository
        self.settings_repo = settings_repo or SettingsRepository()
        self.file_repo = file_repo or FileRepository()

    def get_exclude_paths(self) -> List[str]:
        """从 app_settings 读取排除路径列表，支持 JSON 数组或逗号/换行分隔字符串。"""
        val = self.settings_repo.get(self.SETTING_KEY)
        if not val:
            return []
        raw_str = val.strip()
        if not raw_str:
            return []

        # 尝试 JSON 数组格式
        try:
            import json
            parsed = json.loads(raw_str)
            if isinstance(parsed, list):
                return [self.normalize_path(p) for p in parsed if isinstance(p, str) and p.strip()]
        except (json.JSONDecodeError, TypeError):
            pass

        # 回退：逗号或换行分隔的字符串
        parts = [p.strip() for p in raw_str.replace("\n", ",").split(",") if p.strip()]
        return [self.normalize_path(p) for p in parts]

    def normalize_path(self, path: str) -> str:
        """展开 ~，转绝对路径，normpath，统一大小写。"""
        expanded = os.path.expanduser(path.strip())
        abs_path = os.path.abspath(expanded)
        return os.path.normpath(abs_path)

    def _is_excluded_with_list(self, file_path: str, exclude_paths: List[str]) -> bool:
        """判断文件路径是否被排除，使用已查询的排除路径列表。"""
        if not exclude_paths:
            return False
        norm_file = os.path.normcase(self.normalize_path(file_path))
        for ep in exclude_paths:
            norm_ep = os.path.normcase(ep)
            if norm_file == norm_ep:
                return True
            try:
                if os.path.commonpath([norm_file, norm_ep]) == norm_ep:
                    return True
            except ValueError:
                continue
        return False

    def is_excluded(self, file_path: str) -> bool:
        """判断文件路径是否被排除（用 commonpath 精确匹配子路径）。"""
        exclude_paths = self.get_exclude_paths()
        return self._is_excluded_with_list(file_path, exclude_paths)

    def filter_file_ids(self, file_ids: List[int]) -> Tuple[List[int], int]:
        """过滤文件ID列表，返回 (有效列表, 跳过数量)。"""
        if not file_ids:
            return [],0
        exclude_paths = self.get_exclude_paths()
        if not exclude_paths:
            return file_ids, 0

        valid = []
        skipped = 0

        chunk_size = 900
        for i in range(0, len(file_ids), chunk_size):
            chunk = file_ids[i:i+chunk_size]
            rows = self.file_repo.get_paths_by_ids(chunk)

            for row in rows:
                if not row["current_path"]:
                    valid.append(row["id"])
                    continue
                if self._is_excluded_with_list(row["current_path"], exclude_paths):
                    skipped += 1
                else:
                    valid.append(row["id"])

        return valid, skipped
