# src\api\chat.py
from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from src.api.security import get_api_key
from src.models.chat import ChatRequest
from src.services.agent_service import textbook_agent
from typing import Optional

router = APIRouter()


@router.post("/chat", summary="Handle a chat message and stream response", dependencies=[Depends(get_api_key)])
async def chat_endpoint(
    request: ChatRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_current_page: Optional[str] = Header(None, alias="X-Current-Page")
):
    """
    Handles a user chat message using OpenAI Agents SDK with proper RAG and user context.
    Retrieves relevant content from vector database and personalizes based on user background.
    """
    async def generate_content():
        async for chunk in textbook_agent.chat_stream(
            request.message, 
            request.history,
            request.selected_text,
            x_user_id,
            x_current_page
        ):
            yield {"data": chunk}

    return EventSourceResponse(generate_content())