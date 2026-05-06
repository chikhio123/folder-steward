from fastapi import APIRouter, HTTPException
import json
from ..schemas.file_summary_schema import GenerateSummaryRequest, FileSummaryResponse
from ..services.ai_summary_service import AISummaryService
from ..services.ai_task_queue_service import AITaskQueueService
from ..models.ai_task import AITask
from ..repositories.file_summary_repository import FileSummaryRepository

router = APIRouter(tags=["ai_summaries"])
summary_service = AISummaryService()
queue_service = AITaskQueueService()
summary_repo = FileSummaryRepository()

@router.post("/ai/summaries", response_model=dict)
def create_summary_task(body: GenerateSummaryRequest):
    task = AITask(
        task_type="summary",
        total_items=1,
        input_json=json.dumps({"file_id": body.file_id})
    )

    def handler(t: AITask):
        inputs = json.loads(t.input_json)
        summary_service.process_summary_task(inputs["file_id"])
        t.processed_items = 1

    task_id = queue_service.enqueue_task(task, handler)
    return {"task_id": task_id, "status": "pending"}

@router.get("/files/{file_id}/summary", response_model=FileSummaryResponse)
def get_file_summary(file_id: int):
    summary = summary_repo.get_by_file_id(file_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    return FileSummaryResponse(
        file_id=summary.file_id,
        summary=summary.summary,
        status=summary.status,
        error_message=summary.error_message
    )
