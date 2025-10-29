"""
Pydantic models for MedIntel application.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid


class ChatSession(BaseModel):
    """Chat session model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    language: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatMessage(BaseModel):
    """Chat message model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str  # 'user' or 'assistant'
    content: str
    file_info: Optional[dict] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatSessionCreate(BaseModel):
    """Request model for creating a chat session."""
    user_id: str
    language: Optional[str] = None


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""
    session_id: str
    message: str
    language: Optional[str] = None


class ImageContent:
    """Image content wrapper for AI processing."""
    def __init__(self, image_base64: str, mime_type: str = "image/jpeg"):
        self.image_base64 = image_base64
        self.mime_type = mime_type


class WhatsAppMessageRequest(BaseModel):
    """Request model for sending WhatsApp message."""
    to: str
    message: str
