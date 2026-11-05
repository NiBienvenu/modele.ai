"""REST endpoints of the platform.

Questions / answers:
    POST   /question                    -> queue a prompt, return its request_id
    GET    /response/{request_id}       -> status and, when ready, the answer
Conversations (owned by the X-Device-Id header, no login):
    GET    /conversations               -> list for the sidebar
    GET    /conversations/{id}          -> one conversation with its messages
    DELETE /conversations/{id}          -> delete it

Routes only translate HTTP <-> service calls. No business logic here.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.dependencies import get_app_settings, get_chat_service, get_device_id, get_inference_service
from api.schemas import ConversationOut, ConversationSummary, QuestionAccepted, QuestionRequest, ResponseOut
from chat.service import ChatService, ConversationNotFound
from config.settings import Settings
from inference.service import InferenceService

router = APIRouter()

NOT_FOUND = "Unknown conversation."


# ---- Questions / answers --------------------------------------------------------
@router.post("/question", response_model=QuestionAccepted, status_code=status.HTTP_202_ACCEPTED)
def post_question(
    body: QuestionRequest,
    device_id: str = Depends(get_device_id),
    chat: ChatService = Depends(get_chat_service),
    settings: Settings = Depends(get_app_settings),
) -> QuestionAccepted:
    """Send a prompt to the model. The answer is generated in the background."""
    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(422, "The prompt is empty.")
    if len(prompt) > settings.server.max_prompt_length:
        raise HTTPException(
            413,
            f"The prompt is longer than {settings.server.max_prompt_length} characters.",
        )
    try:
        result = chat.ask(device_id, prompt, body.conversation_id)
    except ConversationNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return QuestionAccepted(
        request_id=result.job.request_id, status=result.job.status, conversation_id=result.conversation_id
    )


@router.get("/response/{request_id}", response_model=ResponseOut)
def get_response(request_id: str, service: InferenceService = Depends(get_inference_service)) -> ResponseOut:
    """Return the answer, or the current status if it is not ready yet."""
    job = service.get_job(request_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown or expired request_id.")
    return ResponseOut.from_job(job)


# ---- Conversations ------------------------------------------------------------------
@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    device_id: str = Depends(get_device_id), chat: ChatService = Depends(get_chat_service)
) -> list[ConversationSummary]:
    return [ConversationSummary.from_conversation(c) for c in chat.list_conversations(device_id)]


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: str, device_id: str = Depends(get_device_id), chat: ChatService = Depends(get_chat_service)
) -> ConversationOut:
    try:
        return ConversationOut.from_conversation(chat.get_conversation(device_id, conversation_id))
    except ConversationNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str, device_id: str = Depends(get_device_id), chat: ChatService = Depends(get_chat_service)
) -> Response:
    try:
        chat.delete_conversation(device_id, conversation_id)
    except ConversationNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
