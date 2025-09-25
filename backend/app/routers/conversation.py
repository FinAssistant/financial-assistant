from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import uuid
import asyncio
from datetime import datetime

from app.routers.auth import get_current_user
from app.ai.conversation_handler import ConversationHandler


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


class ConversationMessage(BaseModel):
    """Individual conversation message model."""
    id: str
    content: str
    role: str = "assistant"
    agent: str
    message_type: str = "ai_response"


class ConversationResponse(BaseModel):
    """Response model for conversation messages - supports multiple messages."""
    messages: List[ConversationMessage]
    session_id: str
    user_id: str
    created_at: str


class ConversationHealthResponse(BaseModel):
    """Response model for conversation health check."""
    status: str
    graph_initialized: bool
    llm_available: bool
    test_response_received: bool
    error: Optional[str] = None


# Create router
router = APIRouter(prefix="/conversation", tags=["conversation"])

# Global conversation handler instance - lazy loaded
conversation_handler = None

def get_conversation_handler() -> ConversationHandler:
    """Get or create the global conversation handler instance."""
    global conversation_handler
    if conversation_handler is None:
        conversation_handler = ConversationHandler()
    return conversation_handler


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
    
    # Generate consistent session ID using same pattern as conversation handler
    session_id = request.session_id or f"session_{current_user}"
    
    try:
        # Create AI-SDK compatible streaming response
        async def generate_real_stream():
            """Generate AI-SDK compatible streaming response with real LangGraph streaming."""
            message_id = str(uuid.uuid4())

            # Send message start
            yield f'data: {json.dumps({"type": "start", "messageId": message_id})}\n\n'

            try:
                # Get response from conversation handler
                ai_response = await get_conversation_handler().process_message(
                    user_message=last_message.content.strip(),
                    user_id=current_user,
                    session_id=session_id
                )

                # Stream multiple messages
                for msg in ai_response["messages"]:
                    # Generate unique text_id for each message
                    current_text_id = str(uuid.uuid4())

                    # Send text start for this message
                    yield f'data: {json.dumps({"type": "text-start", "id": current_text_id})}\n\n'

                    # Stream message content in chunks
                    content = msg["content"]
                    if content:
                        # Chunk content by words, targeting 50-80 characters per chunk
                        words = content.split()
                        current_chunk = ""

                        for word in words:
                            # Add word if chunk won't be too long, otherwise send current chunk
                            if len(current_chunk) + len(word) + 1 <= 80:  # +1 for space
                                current_chunk += (" " if current_chunk else "") + word
                            else:
                                # Send current chunk
                                if current_chunk:
                                    yield f'data: {json.dumps({"type": "text-delta", "id": current_text_id, "delta": current_chunk})}\n\n'
                                    # Add small delay for natural typing effect
                                    await asyncio.sleep(0.05)  # 50ms delay
                                # Start new chunk with current word
                                current_chunk = word

                        # Send remaining chunk
                        if current_chunk:
                            yield f'data: {json.dumps({"type": "text-delta", "id": current_text_id, "delta": current_chunk})}\n\n'

                    # Send text end for this message
                    yield f'data: {json.dumps({"type": "text-end", "id": current_text_id})}\n\n'
                
            except Exception:
                # Send error as content with its own text block
                error_text_id = str(uuid.uuid4())
                error_msg = "I apologize, but I'm having trouble processing your message right now. Please try again."

                yield f'data: {json.dumps({"type": "text-start", "id": error_text_id})}\n\n'
                yield f'data: {json.dumps({"type": "text-delta", "id": error_text_id, "delta": error_msg})}\n\n'
                yield f'data: {json.dumps({"type": "text-end", "id": error_text_id})}\n\n'
            
            # Send stream termination
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_real_stream(),
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
    
    # Generate consistent session ID using same pattern as conversation handler
    session_id = request.session_id or f"session_{current_user}"
    
    try:
        # Process message through conversation handler
        ai_response = await get_conversation_handler().process_message(
            user_message=last_message.content.strip(),
            user_id=current_user,
            session_id=session_id
        )
        
        # Check for processing errors
        # Only raise HTTP error for truly broken system, not for LLM unavailability
        if ai_response.get("error") and "LLM not available" not in str(ai_response.get("error")):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI processing error: {ai_response['error']}"
            )

        # Convert messages array to ConversationMessage objects
        conversation_messages = []
        for msg in ai_response["messages"]:
            conversation_messages.append(ConversationMessage(
                id=str(uuid.uuid4()),
                content=msg["content"],
                role="assistant",
                agent=msg["agent"],
                message_type=msg["message_type"]
            ))

        return ConversationResponse(
            messages=conversation_messages,
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
        health_result = await get_conversation_handler().health_check()
        
        return ConversationHealthResponse(
            status=health_result["status"],
            graph_initialized=health_result["graph_initialized"],
            llm_available=health_result["llm_available"],
            test_response_received=health_result["test_response_received"],
            error=health_result.get("error")
        )
        
    except Exception as e:
        return ConversationHealthResponse(
            status="unhealthy",
            graph_initialized=False,
            llm_available=False,
            test_response_received=False,
            error=str(e)
        )