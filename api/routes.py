"""The two REST endpoints of the platform.

    POST /question                 -> queue a prompt, return its request_id
    GET  /response/{request_id}    -> status and, when ready, the answer

Routes only translate HTTP <-> service calls. No business logic here.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_app_settings, get_inference_service
from api.schemas import QuestionAccepted, QuestionRequest, ResponseOut
from config.settings import Settings
from inference.service import InferenceService

router = APIRouter()


@router.post("/question", response_model=QuestionAccepted, status_code=status.HTTP_202_ACCEPTED)
def post_question(
    body: QuestionRequest,
    service: InferenceService = Depends(get_inference_service),
    settings: Settings = Depends(get_app_settings),
) -> QuestionAccepted:
    """Send a prompt to the model. The answer is generated in the background."""
    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "The prompt is empty.")
    if len(prompt) > settings.server.max_prompt_length:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"The prompt is longer than {settings.server.max_prompt_length} characters.",
        )
    job = service.submit(prompt)
    return QuestionAccepted(request_id=job.request_id, status=job.status)


@router.get("/response/{request_id}", response_model=ResponseOut)
def get_response(request_id: str, service: InferenceService = Depends(get_inference_service)) -> ResponseOut:
    """Return the answer, or the current status if it is not ready yet."""
    job = service.get_job(request_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown or expired request_id.")
    return ResponseOut.from_job(job)
