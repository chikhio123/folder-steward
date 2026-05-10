import os
from typing import List, Optional, Dict
from ..core.database import get_connection
from ..models.scan_task import now_iso
from ..models.ai_classification_suggestion import AIClassificationSuggestion
from ..repositories.ai_classification_repository import AIClassificationRepository
from .prompt_context_service import PromptContextService
from .llm_provider_service import LLMProviderService, RateLimitException
from .directory_policy_service import DirectoryPolicyService
from .path_protection_service import PathProtectionService
from .ai_task_queue_service import raise_if_cancelled
from ..core.uow import UnitOfWork

class AIClassificationService:
    def __init__(
        self,
        class_repo=None,
        context_service=None,
        llm_service=None,
        dir_policy=None,
        path_protection=None,
    ):
        self.class_repo = class_repo or AIClassificationRepository()
        self.context_service = context_service or PromptContextService()
        self.llm_service = llm_service or LLMProviderService()
        self.dir_policy = dir_policy or DirectoryPolicyService()
        self.path_protection = path_protection or PathProtectionService()

    def process_classification_task(self, file_id: int, archive_root: str) -> None:
        """Processes an AI classification task for a single file and saves the result."""
        file_context = self.context_service.build_file_context(file_id, max_preview_length=800)
        rules_context = self.context_service.build_rules_context()

        if not file_context:
            return

        result = self.llm_service.generate_classification(file_context, rules_context, archive_root)

        target_dir = result.get("suggested_target_dir", "")
        policy_status = self.dir_policy.evaluate(target_dir, archive_root)
        status = "pending"
        if policy_status == "invalid":
            status = "failed"

        sug = AIClassificationSuggestion(
            file_id=file_id,
            suggested_target_dir=target_dir,
            directory_status=policy_status,
            confidence=result.get("confidence", 0.0),
            reason=result.get("reason"),
            evidence_json=None,
            source_context_hash=None,
            status=status,
            created_at=now_iso()
        )
        with UnitOfWork():
            self.class_repo.create(sug)

    def process_classification_batch(
        self,
        file_ids: List[int],
        archive_root: str,
        batch_size: int = 30,
        task: Optional[object] = None
    ) -> None:
        """Process multiple files in path-aware batches, with automatic fallback on failure.

        Files are grouped by parent directory first, then merged into batches respecting batch_size.
        Every file in file_ids will get a suggestion record (pending or failed).
        No file is silently skipped.
        """
        # 防御性过滤：排除目录（防线3）
        path_protection = self.path_protection
        file_ids, skipped = path_protection.filter_file_ids(file_ids)
        if skipped > 0:
            print(f"Skipped {skipped} files due to AI exclude paths (defense layer)")
        if task:
            task.total_items = len(file_ids)
        if not file_ids:
            raise ValueError("应用 AI 排除目录后，没有可处理的文件。")
        rules_context = self.context_service.build_rules_context()
        classified_fids: set[int] = set()
        processed = 0

        # Step 1: Group files by parent directory (normalized path)
        groups = self._group_files_by_directory(file_ids)

        # Step 2: Merge groups into batches respecting batch_size as hard limit
        batches = self._merge_groups_to_batches(groups, batch_size)

        for batch in batches:
            raise_if_cancelled()

            # Build contexts for this batch
            contexts = []
            context_fids = set()
            for fid in batch:
                fc = self.context_service.build_file_context(fid, max_preview_length=500)
                if fc:
                    fc["file_id"] = fid
                    contexts.append(fc)
                    context_fids.add(fid)

            if contexts:
                # Try batch classification with fallback
                results = self._classify_with_fallback(contexts, rules_context, archive_root, batch_size)

                # Track seen file_ids to detect duplicates
                seen_fids = set()

                # Save valid results, ignore ghost records (fid not in current batch)
                for item in results:
                    fid = item.get("file_id")
                    if fid is None:
                        continue
                    try:
                        fid = int(fid)
                    except ValueError:
                        pass

                    if fid in seen_fids:
                        print(f"Duplicate classification result ignored: file_id={fid}")
                        continue
                    seen_fids.add(fid)

                    if fid not in context_fids:
                        print(f"Ghost record ignored: LLM returned file_id={fid} which is not in this batch. (context_fids: {context_fids})")
                        continue

                    target_dir = item.get("suggested_target_dir", "")
                    # Empty target_dir means classification failed — skip policy check
                    if not target_dir:
                        sug = AIClassificationSuggestion(
                            file_id=fid,
                            suggested_target_dir="",
                            directory_status="unknown",
                            confidence=0.0,
                            reason=item.get("reason", "Classification failed"),
                            evidence_json=None,
                            source_context_hash=None,
                            status="failed",
                            created_at=now_iso()
                        )
                        with UnitOfWork():
                            self.class_repo.create(sug)
                        classified_fids.add(fid)
                        continue

                    policy_status = self.dir_policy.evaluate(target_dir, archive_root)
                    status = "pending" if policy_status != "invalid" else "failed"

                    sug = AIClassificationSuggestion(
                        file_id=fid,
                        suggested_target_dir=target_dir,
                        directory_status=policy_status,
                        confidence=item.get("confidence", 0.0),
                        reason=item.get("reason"),
                        evidence_json=None,
                        source_context_hash=None,
                        status=status,
                        created_at=now_iso()
                    )
                    with UnitOfWork():
                        self.class_repo.create(sug)
                    classified_fids.add(fid)

            # Update progress: count all files in this batch (success or fail)
            processed += len(batch)
            if task:
                task.processed_items = processed
                from ..repositories.ai_task_repository import AITaskRepository
                with UnitOfWork():
                    AITaskRepository().update(task)

        # Write failed records for any file that got no result (ghost or LLM omission)
        for fid in file_ids:
            if fid not in classified_fids:
                sug = AIClassificationSuggestion(
                    file_id=fid,
                    suggested_target_dir="",
                    directory_status="unknown",
                    confidence=0.0,
                    reason="Classification failed: LLM returned no result for this file_id",
                    evidence_json=None,
                    source_context_hash=None,
                    status="failed",
                    created_at=now_iso()
                )
                with UnitOfWork():
                    self.class_repo.create(sug)
                print(f"Missing classification result for file_id={fid}, wrote failed record")

    def _group_files_by_directory(self, file_ids: List[int]) -> Dict[str, List[int]]:
        """Group file_ids by their normalized parent directory path."""
        conn = get_connection()
        groups: Dict[str, List[int]] = {}
        for fid in file_ids:
            row = conn.execute("SELECT current_path FROM file_records WHERE id = ?", (fid,)).fetchone()
            if not row or not row["current_path"]:
                # Files without a valid path go to a special group
                key = "_ungrouped_"
            else:
                # Normalize path and get parent directory
                normalized = os.path.normpath(row["current_path"]).lower()
                parent = os.path.dirname(normalized)
                key = parent or "_root_"
            if key not in groups:
                groups[key] = []
            groups[key].append(fid)
        return groups

    def _merge_groups_to_batches(self, groups: Dict[str, List[int]], batch_size: int) -> List[List[int]]:
        """Merge directory groups into batches, respecting batch_size as hard limit."""
        batches: List[List[int]] = []
        current_batch: List[int] = []

        # Sort groups by directory name for determinism
        for dir_path in sorted(groups.keys()):
            files = groups[dir_path]
            # If a single directory exceeds batch_size, split it internally
            if len(files) > batch_size:
                # Flush current batch if not empty
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                # Split large directory into chunks of batch_size
                for i in range(0, len(files), batch_size):
                    batches.append(files[i:i + batch_size])
            else:
                # Try to add this directory's files to current batch
                if len(current_batch) + len(files) <= batch_size:
                    current_batch.extend(files)
                else:
                    # Flush current batch and start new one with this directory
                    if current_batch:
                        batches.append(current_batch)
                    current_batch = files.copy()
        # Don't forget the last batch
        if current_batch:
            batches.append(current_batch)
        return batches

    def _classify_with_fallback(
        self,
        contexts: list[dict],
        rules_context: list,
        archive_root: str,
        original_batch_size: int
    ) -> list[dict]:
        """Try batch classification, with fallback to smaller batches or single-file.
        Re-groups contexts by directory if falling back.
        """
        # Try full batch first
        try:
            return self.llm_service.generate_classifications_batch(contexts, rules_context, archive_root)
        except RateLimitException:
            raise
        except Exception as e:
            print(f"Batch classification failed ({len(contexts)} files): {e}")

        # Fallback: re-group current contexts by directory
        if len(contexts) > 10:
            # Re-group contexts by parent directory
            dir_groups: Dict[str, list] = {}
            for fc in contexts:
                path = fc.get("current_path", "")
                if not path:
                    key = "_ungrouped_"
                else:
                    normalized = os.path.normpath(path).lower()
                    key = os.path.dirname(normalized) or "_root_"
                if key not in dir_groups:
                    dir_groups[key] = []
                dir_groups[key].append(fc)

            # Use smaller batch size for fallback
            small_size = max(5, len(contexts) // 3)
            print(f"Retrying with smaller directory-aware batches, max size {small_size}...")
            results = []
            for dir_path in sorted(dir_groups.keys()):
                chunk = dir_groups[dir_path]
                if len(chunk) > small_size:
                    # Split large directory chunk
                    for i in range(0, len(chunk), small_size):
                        sub_chunk = chunk[i:i + small_size]
                        try:
                            results.extend(self.llm_service.generate_classifications_batch(sub_chunk, rules_context, archive_root))
                        except RateLimitException:
                            raise
                        except Exception as e2:
                            print(f"Dir-aware batch failed ({len(sub_chunk)} files): {e2}")
                            results.extend(self._classify_single_files(sub_chunk, rules_context, archive_root))
                else:
                    try:
                        results.extend(self.llm_service.generate_classifications_batch(chunk, rules_context, archive_root))
                    except RateLimitException:
                        raise
                    except Exception as e2:
                        print(f"Dir-aware batch failed ({len(chunk)} files): {e2}")
                        results.extend(self._classify_single_files(chunk, rules_context, archive_root))
            return results

        # Fallback 2: single file (for small batches that failed)
        print(f"Fallback to single file classification for {len(contexts)} files...")
        return self._classify_single_files(contexts, rules_context, archive_root)

    def _classify_single_files(
        self,
        contexts: list[dict],
        rules_context: list,
        archive_root: str
    ) -> list[dict]:
        """Classify files one by one as last resort. Failed files still get a result entry."""
        results = []
        for fc in contexts:
            fid = fc.get("file_id", 0)
            try:
                result = self.llm_service.generate_classification(fc, rules_context, archive_root)
                result["file_id"] = fid
                results.append(result)
            except RateLimitException:
                raise
            except Exception as e:
                # Only raise to the queue wrapper if it's REALLY a connection failure on a SINGLE item
                is_retryable = any(x in str(e).lower() for x in ["disconnected", "timed out", "timeout", "readerror"])
                if is_retryable:
                    raise
                print(f"Single file classification failed for file_id={fid}: {e}")
                # Return a failed entry so the caller can still record it
                results.append({
                    "file_id": fid,
                    "suggested_target_dir": "",
                    "confidence": 0.0,
                    "reason": f"Classification failed: {e}"
                })
        return results
