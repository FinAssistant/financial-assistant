from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import uuid
from datetime import datetime

from app.routers.auth import get_current_user
from app.ai.orchestrator import OrchestratorAgent


# Pydantic models for request/response
class ConversationRequest(BaseModel):
    """Request model for conversation messages."""
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    session_id: Optional[str] = Field(None, description="Optional conversation session ID")


class ConversationResponse(BaseModel):
    """Response model for conversation messages."""
    id: str
    content: str
    role: str
    agent: str
    session_id: str
    user_id: str
    created_at: str


class ConversationHealthResponse(BaseModel):
    """Response model for conversation health check."""
    status: str
    graph_initialized: bool
    test_response_received: bool
    error: Optional[str] = None


# Create router
router = APIRouter(prefix="/conversation", tags=["conversation"])

# Global orchestrator instance
orchestrator = OrchestratorAgent()


@router.post("/send", response_class=StreamingResponse)
async def send_message(
    request: ConversationRequest,
    current_user: str = Depends(get_current_user)
) -> StreamingResponse:
    """
    Send a message to the AI conversation system with streaming response.
    Compatible with AI-SDK format for frontend integration.
    Requires authentication.
    """
    # Validate message content
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )
    
    # Generate consistent session ID using same pattern as orchestrator
    session_id = request.session_id or f"session_{current_user}"
    
    try:
        # Process message through orchestrator
        ai_response = orchestrator.process_message(
            user_message=request.message.strip(),
            user_id=current_user,
            session_id=session_id
        )
        
        # Check for processing errors
        if ai_response.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI processing error: {ai_response['error']}"
            )
        
        # Create AI-SDK compatible streaming response
        def generate_stream():
            """Generate AI-SDK compatible streaming response."""
            # Send the AI response as a streaming format
            response_data = {
                "id": str(uuid.uuid4()),
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": "orchestrator",
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "content": ai_response["content"]
                    },
                    "finish_reason": None
                }]
            }
            
            # Send data chunk
            yield f"data: {json.dumps(response_data)}\n\n"
            
            # Send final chunk
            final_response = {
                "id": str(uuid.uuid4()),
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": "orchestrator",
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final_response)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation processing failed: {str(e)}"
        )


@router.post("/message", response_model=ConversationResponse)
async def send_message_non_streaming(
    request: ConversationRequest,
    current_user: str = Depends(get_current_user)
) -> ConversationResponse:
    """
    Send a message to the AI conversation system (non-streaming version).
    Alternative endpoint for non-streaming clients.
    Requires authentication.
    """
    # Validate message content
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )
    
    # Generate consistent session ID using same pattern as orchestrator
    session_id = request.session_id or f"session_{current_user}"
    
    try:
        # Process message through orchestrator
        ai_response = orchestrator.process_message(
            user_message=request.message.strip(),
            user_id=current_user,
            session_id=session_id
        )
        
        # Check for processing errors
        if ai_response.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI processing error: {ai_response['error']}"
            )
        
        return ConversationResponse(
            id=str(uuid.uuid4()),
            content=ai_response["content"],
            role="assistant",
            agent=ai_response["agent"],
            session_id=session_id,
            user_id=current_user,
            created_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation processing failed: {str(e)}"
        )


@router.get("/health", response_model=ConversationHealthResponse)
async def health_check(
    current_user: str = Depends(get_current_user)
) -> ConversationHealthResponse:
    """
    Health check endpoint for the conversation system.
    Requires authentication to prevent abuse.
    """
    try:
        health_result = orchestrator.health_check()
        
        return ConversationHealthResponse(
            status=health_result["status"],
            graph_initialized=health_result["graph_initialized"],
            test_response_received=health_result["test_response_received"],
            error=health_result.get("error")
        )
        
    except Exception as e:
        return ConversationHealthResponse(
            status="unhealthy",
            graph_initialized=False,
            test_response_received=False,
            error=str(e)
        )