from uuid import UUID

from fastapi import APIRouter, Depends

from app.auth import get_current_user_id
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    return ChatResponse(
        reply="This is a stub. Connect to Amazon Bedrock (or another AI service) to generate answers from the user's budgets, goals, and transactions."
    )
