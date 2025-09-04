from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import uuid
from datetime import datetime

from app.routers.auth import get_current_user
from app.ai.orchestrator import OrchestratorAgent


# AI SDK 5 compatible message part model
class MessagePart(BaseModel):
    """AI SDK 5 message part structure."""
    type: str = Field(..., description="Part type: text, image, etc.")
    text: str = Field(..., description="Text content for text parts")

# AI SDK 5 compatible message model
class ClientMessage(BaseModel):
    """AI SDK 5 ClientMessage structure."""
    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role: user, assistant, or system")
    parts: List[MessagePart] = Field(..., description="Message parts array")
    
    @property
    def content(self) -> str:
        """Extract text content from parts array for backwards compatibility."""
        text_parts = [part.text for part in self.parts if part.type == "text" and part.text]
        return " ".join(text_parts)

# AI SDK compatible request model
class ConversationRequest(BaseModel):
    """AI SDK compatible request model for conversation messages."""
    messages: List[ClientMessage] = Field(..., min_length=1, description="Array of conversation messages")
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
    # Validate messages array
    if not request.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Messages array cannot be empty"
        )
    
    # Get the last user message from the messages array
    last_message = None
    for message in reversed(request.messages):
        if message.role == "user":
            last_message = message
            break
    
    if not last_message or not last_message.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid user message found"
        )
    
    # Generate consistent session ID using same pattern as orchestrator
    session_id = request.session_id or f"session_{current_user}"
    
    try:
        # Process message through orchestrator
        ai_response = orchestrator.process_message(
            user_message=last_message.content.strip(),
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
            message_id = str(uuid.uuid4())
            text_id = str(uuid.uuid4())
            
            # Send message start
            yield f'data: {json.dumps({"type": "start", "messageId": message_id})}\n\n'
            
            # Send text start
            yield f'data: {json.dumps({"type": "text-start", "id": text_id})}\n\n'
            
            # Send text content as delta
            content = ai_response["content"]
            yield f'data: {json.dumps({"type": "text-delta", "id": text_id, "delta": content})}\n\n'
            
            # Send text end
            yield f'data: {json.dumps({"type": "text-end", "id": text_id})}\n\n'
            
            # Send stream termination
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
                "x-vercel-ai-data-stream": "v1"  # AI SDK required header
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
    # Validate messages array
    if not request.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Messages array cannot be empty"
        )
    
    # Get the last user message from the messages array
    last_message = None
    for message in reversed(request.messages):
        if message.role == "user":
            last_message = message
            break
    
    if not last_message or not last_message.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid user message found"
        )
    
    # Generate consistent session ID using same pattern as orchestrator
    session_id = request.session_id or f"session_{current_user}"
    
    try:
        # Process message through orchestrator
        ai_response = orchestrator.process_message(
            user_message=last_message.content.strip(),
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