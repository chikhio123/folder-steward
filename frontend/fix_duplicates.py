import re

# 1. Update FileRepository
with open("D:/Code/Folder Steward/backend/app/repositories/file_repository.py", "r", encoding="utf-8") as f:
    content = f.read()

repo_replace = """    def find_duplicate_groups(self) -> list[dict]:
        \"\"\"Return groups of files sharing the same sha256 and filename.\"\"\"
        conn = get_connection()
        rows = conn.execute(
            \"\"\"SELECT sha256, filename, size_bytes, COUNT(*) as cnt
               FROM file_records
               WHERE status='active' AND sha256 IS NOT NULL
               GROUP BY sha256, filename
               HAVING COUNT(*) > 1
               ORDER BY size_bytes DESC\"\"\"
        ).fetchall()
        groups = []
        for r in rows:
            files = conn.execute(
                "SELECT id, filename, current_path, modified_at FROM file_records WHERE sha256 = ? AND filename = ? ORDER BY id",
                (r["sha256"], r["filename"]),
            ).fetchall()
            groups.append({
                "sha256": r["sha256"],
                "filename": r["filename"],
                "size_bytes": r["size_bytes"],
                "count": r["cnt"],
                "files": [dict(f) for f in files],
            })
        return groups

    def count_duplicate_groups(self) -> int:
        row = get_connection().execute(
            \"\"\"SELECT COUNT(*) as cnt FROM (
                SELECT sha256, filename FROM file_records
                WHERE status='active' AND sha256 IS NOT NULL
                GROUP BY sha256, filename HAVING COUNT(*) > 1
            )\"\"\"
        ).fetchone()
        return row["cnt"]"""

content = re.sub(r'    def find_duplicate_groups\(self\) -> list\[dict\]:.*?\)"""\n        \)\.fetchone\(\)\n        return row\["cnt"\]', repo_replace, content, flags=re.DOTALL)
with open("D:/Code/Folder Steward/backend/app/repositories/file_repository.py", "w", encoding="utf-8") as f:
    f.write(content)


# 2. Update DuplicateService
with open("D:/Code/Folder Steward/backend/app/services/duplicate_service.py", "r", encoding="utf-8") as f:
    content = f.read()

svc_replace = """    def create_duplicate_suggestions(self, sha256: str, filename: str, keep_file_id: int) -> int:
        \"\"\"Move all files in a duplicate group (except the kept one) to Duplicates/.\"\"\"
        groups = self.file_repo.find_duplicate_groups()
        group = next((g for g in groups if g["sha256"] == sha256 and g["filename"] == filename), None)"""

content = re.sub(r'    def create_duplicate_suggestions\(self, sha256: str, keep_file_id: int\) -> int:\n        """Move all files in a duplicate group \(except the kept one\) to Duplicates/\."""\n        groups = self\.file_repo\.find_duplicate_groups\(\)\n        group = next\(\(g for g in groups if g\["sha256"\] == sha256\), None\)', svc_replace, content)
with open("D:/Code/Folder Steward/backend/app/services/duplicate_service.py", "w", encoding="utf-8") as f:
    f.write(content)


# 3. Update API
with open("D:/Code/Folder Steward/backend/app/api/duplicates.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("class GenerateDuplicateSuggestionsRequest(BaseModel):\n    sha256: str\n    keep_file_id: int", "class GenerateDuplicateSuggestionsRequest(BaseModel):\n    sha256: str\n    filename: str\n    keep_file_id: int")
content = content.replace("svc.create_duplicate_suggestions(body.sha256, body.keep_file_id)", "svc.create_duplicate_suggestions(body.sha256, body.filename, body.keep_file_id)")
with open("D:/Code/Folder Steward/backend/app/api/duplicates.py", "w", encoding="utf-8") as f:
    f.write(content)


# 4. Update Frontend API
with open("D:/Code/Folder Steward/frontend/src/services/api.ts", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("export const createDuplicateSuggestions = (sha256: string, keepFileId: number) =>\n  request<{ created_count: number }>(\"/duplicates/suggestions\", {\n    method: \"POST\",\n    body: JSON.stringify({ sha256, keep_file_id: keepFileId }),\n  });", "export const createDuplicateSuggestions = (sha256: string, filename: string, keepFileId: number) =>\n  request<{ created_count: number }>(\"/duplicates/suggestions\", {\n    method: \"POST\",\n    body: JSON.stringify({ sha256, filename, keep_file_id: keepFileId }),\n  });")
with open("D:/Code/Folder Steward/frontend/src/services/api.ts", "w", encoding="utf-8") as f:
    f.write(content)


# 5. Update Frontend DuplicatePage
with open("D:/Code/Folder Steward/frontend/src/pages/DuplicatePage.tsx", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("const suggestMutation = useMutation({\n    mutationFn: ({ sha256, keepFileId }: { sha256: string; keepFileId: number }) =>\n      createDuplicateSuggestions(sha256, keepFileId),", "const suggestMutation = useMutation({\n    mutationFn: ({ sha256, filename, keepFileId }: { sha256: string; filename: string; keepFileId: number }) =>\n      createDuplicateSuggestions(sha256, filename, keepFileId),")

# There could be an issue with `processingSha` state since now we group by two keys.
# I'll update it to use `processingKey` (sha256 + filename)
content = content.replace("const [processingSha, setProcessingSha] = useState<string | null>(null);", "const [processingKey, setProcessingKey] = useState<string | null>(null);")
content = content.replace("setProcessingSha(variables.sha256);", "setProcessingKey(variables.sha256 + variables.filename);")
content = content.replace("setProcessingSha(null);", "setProcessingKey(null);")
content = content.replace("suggestMutation.isPending && processingSha === group.sha256", "suggestMutation.isPending && processingKey === (group.sha256 + (group.filename || ''))")
# Wait, group doesn't have filename in its type definition if we didn't add it in frontend.
# It does have it dynamically, but TypeScript might complain. 
# Also, group.files[0].filename is always available.
# So I can just use group.sha256 + group.files[0].filename.
content = content.replace("suggestMutation.mutate({ sha256: group.sha256, keepFileId: f.id })", "suggestMutation.mutate({ sha256: group.sha256, filename: group.files[0].filename, keepFileId: f.id })")
content = content.replace("group.sha256 + (group.filename || '')", "group.sha256 + group.files[0].filename")

with open("D:/Code/Folder Steward/frontend/src/pages/DuplicatePage.tsx", "w", encoding="utf-8") as f:
    f.write(content)

