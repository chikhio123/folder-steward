from typing import List, Optional
from ..core.database import get_connection
from ..models.scan_task import now_iso
from ..models.ai_classification_suggestion import AIClassificationSuggestion
from ..repositories.ai_classification_repository import AIClassificationRepository
from .prompt_context_service import PromptContextService
from .llm_provider_service import LLMProviderService
from .directory_policy_service import DirectoryPolicyService

class AIClassificationService:
    def __init__(self):
        self.class_repo = AIClassificationRepository()
        self.context_service = PromptContextService()
        self.llm_service = LLMProviderService()
        self.dir_policy = DirectoryPolicyService()

    def process_classification_task(self, file_id: int, archive_root: str) -> None:
        """Processes an AI classification task for a single file and saves the result."""
        # 1. Build context
        file_context = self.context_service.build_file_context(file_id, max_preview_length=800)
        rules_context = self.context_service.build_rules_context()

        if not file_context:
            return

        # 2. Call LLM
        result = self.llm_service.generate_classification(file_context, rules_context, archive_root)

        target_dir = result.get("suggested_target_dir", "")
        # 3. Policy Check
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
        self.class_repo.create(sug)

    def process_classification_batch(
        self,
        file_ids: List[int],
        archive_root: str,
        batch_size: int = 30,
        task: Optional[object] = None
    ) -> None:
        """Process multiple files in batches, with automatic fallback on failure.

        Every file in file_ids will get a suggestion record (pending or failed).
        No file is silently skipped.
        """
        rules_context = self.context_service.build_rules_context()
        valid_file_ids = set(file_ids)
        classified_fids: set[int] = set()
        processed = 0

        # Chunk file_ids into batches
        batches = [file_ids[i:i + batch_size] for i in range(0, len(file_ids), batch_size)]

        for batch in batches:
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

                # Save valid results, ignore ghost records (fid not in original input)
                for item in results:
                    fid = item.get("file_id")
                    if fid is None:
                        continue
                    if fid not in valid_file_ids:
                        print(f"Ghost record ignored: LLM returned file_id={fid} which is not in batch")
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
                    self.class_repo.create(sug)
                    classified_fids.add(fid)

            # Update progress: count all files in this batch (success or fail)
            processed += len(batch)
            if task:
                task.processed_items = processed
                from ..repositories.ai_task_repository import AITaskRepository
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
                self.class_repo.create(sug)
                print(f"Missing classification result for file_id={fid}, wrote failed record")

    def _classify_with_fallback(
        self,
        contexts: list[dict],
        rules_context: list,
        archive_root: str,
        original_batch_size: int
    ) -> list[dict]:
        """Try batch classification, with fallback to smaller batches or single-file."""
        # Try full batch first
        try:
            return self.llm_service.generate_classifications_batch(contexts, rules_context, archive_root)
        except Exception as e:
            print(f"Batch classification failed ({len(contexts)} files): {e}")

        # Fallback 1: split into smaller batches (half size, min 10)
        if len(contexts) > 10:
            small_size = max(10, len(contexts) // 2)
            print(f"Retrying with smaller batches of {small_size}...")
            results = []
            for i in range(0, len(contexts), small_size):
                chunk = contexts[i:i + small_size]
                try:
                    results.extend(self.llm_service.generate_classifications_batch(chunk, rules_context, archive_root))
                except Exception as e2:
                    print(f"Small batch failed ({len(chunk)} files): {e2}")
                    # Fallback 2: single file
                    results.extend(self._classify_single_files(chunk, rules_context, archive_root))
            return results

        # Fallback 2: single file (for small batches that failed)
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
            except Exception as e:
                print(f"Single file classification failed for file_id={fid}: {e}")
                # Return a failed entry so the caller can still record it
                results.append({
                    "file_id": fid,
                    "suggested_target_dir": "",
                    "confidence": 0.0,
                    "reason": f"Classification failed: {e}"
                })
        return results
