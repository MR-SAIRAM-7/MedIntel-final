"""
WebSocket handler for real-time chat communication.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
from datetime import datetime, timezone
import logging

from app.models.chat import ChatMessage
from app.database import Database
from app.constants import SUPPORTED_LANGUAGES, CONFIRMATION_MESSAGES, LANGUAGE_PROMPT
from app.utils.helpers import prepare_for_mongo, detect_language_preference
from app.services.ai_service import ai_service

logger = logging.getLogger("medintel.websocket")


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        """Add a new WebSocket connection."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"WebSocket connected for session: {session_id}")
    
    def disconnect(self, session_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket disconnected for session: {session_id}")
    
    async def broadcast(self, session_id: str, message: str):
        """Broadcast message to all connections in a session."""
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id][:]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Broadcast error: {str(e)}")
                    self.active_connections[session_id].remove(connection)
            
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]


# Global connection manager
manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket, session_id: str):
    """Handle WebSocket connection and messages."""
    await manager.connect(session_id, websocket)
    db = Database.get_db()
    
    try:
        while True:
            msg = await websocket.receive_text()
            
            # Get session
            session = await db.chat_sessions.find_one({"id": session_id})
            if not session:
                await websocket.send_text("Session not found")
                continue
            
            lang = session.get("language")
            
            # Check for language preference
            detected = detect_language_preference(msg)
            if detected and detected in SUPPORTED_LANGUAGES:
                await db.chat_sessions.update_one(
                    {"id": session_id},
                    {"$set": {
                        "language": detected,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                reply = CONFIRMATION_MESSAGES.get(
                    detected,
                    f"Language changed to {detected.capitalize()}."
                )
                
                # Save messages
                user_msg = ChatMessage(
                    session_id=session_id,
                    role="user",
                    content=msg
                )
                await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))
                
                assistant_msg = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=reply
                )
                await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))
                
                await manager.broadcast(session_id, reply)
                continue
            
            # If no language set, prompt
            if lang is None:
                reply = LANGUAGE_PROMPT
                
                user_msg = ChatMessage(
                    session_id=session_id,
                    role="user",
                    content=msg
                )
                await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))
                
                assistant_msg = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=reply
                )
                await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))
                
                await manager.broadcast(session_id, reply)
                continue
            
            # Save user message
            user_msg = ChatMessage(
                session_id=session_id,
                role="user",
                content=msg
            )
            await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))
            
            # Generate AI response
            if not ai_service:
                await websocket.send_text("AI service is not available")
                continue
            
            ai_reply = await ai_service.generate_response(
                session_id,
                msg,
                None,
                lang
            )
            
            # Save assistant message
            assistant_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=ai_reply
            )
            await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))
            
            # Broadcast to all connections
            await manager.broadcast(session_id, ai_reply)
    
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(session_id, websocket)
