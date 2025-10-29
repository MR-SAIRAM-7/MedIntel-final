"""
Chat routes for MedIntel application.
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import List, Optional
from datetime import datetime, timezone
import tempfile
import os
import base64
import logging

from app.models.chat import (
    ChatSession, ChatMessage, ChatSessionCreate, 
    SendMessageRequest, ImageContent
)
from app.database import Database
from app.constants import (
    SUPPORTED_LANGUAGES, CONFIRMATION_MESSAGES, LANGUAGE_PROMPT
)
from app.utils.helpers import prepare_for_mongo, detect_language_preference
from app.utils.file_processor import extract_text_from_pdf, validate_file_size
from app.services.ai_service import ai_service
from app.config import config

logger = logging.getLogger("medintel.routes.chat")

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/session", response_model=ChatSession)
async def create_chat_session(data: ChatSessionCreate):
    """Create a new chat session."""
    try:
        session = ChatSession(**data.dict())
        db = Database.get_db()
        await db.chat_sessions.insert_one(prepare_for_mongo(session.dict()))
        logger.info(f"Created chat session: {session.id}")
        return session
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("/session/{session_id}", response_model=ChatSession)
async def get_chat_session(session_id: str):
    """Get a specific chat session."""
    try:
        db = Database.get_db()
        session = await db.chat_sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return ChatSession(**session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session")


@router.get("/session/{session_id}/messages", response_model=List[ChatMessage])
async def get_chat_messages(session_id: str):
    """Get all messages for a session."""
    try:
        db = Database.get_db()
        messages = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(1000)
        return [ChatMessage(**msg) for msg in messages]
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")


@router.post("/message")
async def send_message(req: SendMessageRequest):
    """Send a message in a chat session."""
    try:
        db = Database.get_db()
        session = await db.chat_sessions.find_one({"id": req.session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        lang = req.language or session.get("language")
        
        # Check for language preference change
        detected = detect_language_preference(req.message)
        if detected and detected in SUPPORTED_LANGUAGES:
            await db.chat_sessions.update_one(
                {"id": req.session_id},
                {"$set": {
                    "language": detected,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            reply = CONFIRMATION_MESSAGES.get(
                detected,
                f"Language changed to {detected.capitalize()}."
            )
            
            # Save user message
            user_msg = ChatMessage(
                session_id=req.session_id,
                role="user",
                content=req.message
            )
            await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))
            
            # Save assistant message
            assistant_msg = ChatMessage(
                session_id=req.session_id,
                role="assistant",
                content=reply
            )
            await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))
            
            return {"user_message": user_msg, "assistant_message": assistant_msg}
        
        # If no language set, prompt for language
        if lang is None:
            reply = LANGUAGE_PROMPT
            
            user_msg = ChatMessage(
                session_id=req.session_id,
                role="user",
                content=req.message
            )
            await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))
            
            assistant_msg = ChatMessage(
                session_id=req.session_id,
                role="assistant",
                content=reply
            )
            await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))
            
            return {"user_message": user_msg, "assistant_message": assistant_msg}
        
        # Save user message
        user_msg = ChatMessage(
            session_id=req.session_id,
            role="user",
            content=req.message
        )
        await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))
        
        # Generate AI response
        if not ai_service:
            raise HTTPException(
                status_code=503,
                detail="AI service is not available"
            )
        
        ai_reply = await ai_service.generate_response(
            req.session_id,
            req.message,
            None,
            lang
        )
        
        # Save assistant message
        assistant_msg = ChatMessage(
            session_id=req.session_id,
            role="assistant",
            content=ai_reply
        )
        await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))
        
        return {"user_message": user_msg, "assistant_message": assistant_msg}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/upload")
async def upload_and_analyze_file(
    session_id: str = Form(...),
    message: str = Form("Please analyze this medical report/image and provide insights."),
    language: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    """Upload and analyze a file (image, PDF, or text)."""
    try:
        db = Database.get_db()
        session = await db.chat_sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        lang = language or session.get("language", "english")
        
        # Read file
        file_bytes = await file.read()
        
        # Validate file size
        if not validate_file_size(len(file_bytes), config.MAX_FILE_SIZE):
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum {config.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        file_info = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_bytes)
        }
        
        # Save user message
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=f"{message} [Uploaded file: {file.filename}]",
            file_info=file_info
        )
        await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))
        
        # Process file based on type
        file_content = None
        processed_message = message
        
        if file.content_type == "application/pdf":
            # Extract text from PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(file_bytes)
                temp_path = temp_file.name
            
            try:
                pdf_text = extract_text_from_pdf(temp_path)
                processed_message = f"{message}\n\nMedical Report Content:\n{pdf_text}"
            finally:
                os.unlink(temp_path)
        
        elif file.content_type.startswith("image/"):
            # Encode image for AI
            base64_data = base64.b64encode(file_bytes).decode("utf-8")
            file_content = ImageContent(
                image_base64=base64_data,
                mime_type=file.content_type
            )
            processed_message = f"{message}\n\nAnalyze this medical image for findings, abnormalities, or insights."
        
        elif file.content_type.startswith("text/"):
            # Process text file
            try:
                text_content = file_bytes.decode("utf-8")
                processed_message = f"{message}\n\nMedical Document Content:\n{text_content}"
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Cannot decode text file")
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload PDF, image, or text files."
            )
        
        # Generate AI response
        if not ai_service:
            raise HTTPException(
                status_code=503,
                detail="AI service is not available"
            )
        
        ai_reply = await ai_service.generate_response(
            session_id,
            processed_message,
            file_content,
            lang
        )
        
        # Save assistant message
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=ai_reply
        )
        await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))
        
        return {"user_message": user_msg, "assistant_message": assistant_msg}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session and all its messages."""
    try:
        db = Database.get_db()
        
        # Delete messages
        await db.chat_messages.delete_many({"session_id": session_id})
        
        # Delete session
        result = await db.chat_sessions.delete_one({"id": session_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        logger.info(f"Deleted chat session: {session_id}")
        return {"message": "Chat session deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")


@router.get("/sessions/{user_id}", response_model=List[ChatSession])
async def get_user_sessions(user_id: str):
    """Get all sessions for a user."""
    try:
        db = Database.get_db()
        sessions = await db.chat_sessions.find(
            {"user_id": user_id}
        ).sort("updated_at", -1).to_list(100)
        return [ChatSession(**s) for s in sessions]
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sessions")


@router.post("/language/{session_id}")
async def change_language(session_id: str, language: str):
    """Change language for a session."""
    try:
        if language.lower() not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language. Supported: {', '.join(SUPPORTED_LANGUAGES)}"
            )
        
        db = Database.get_db()
        session = await db.chat_sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        await db.chat_sessions.update_one(
            {"id": session_id},
            {"$set": {
                "language": language.lower(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        reply = CONFIRMATION_MESSAGES.get(
            language.lower(),
            f"Language changed to {language.capitalize()}."
        )
        
        return {"message": reply, "language": language.lower()}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing language: {e}")
        raise HTTPException(status_code=500, detail="Failed to change language")
