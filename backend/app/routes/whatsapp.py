"""
WhatsApp integration routes for MedIntel application.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import logging

from app.models.chat import WhatsAppMessageRequest, ChatSession
from app.services.whatsapp_service import whatsapp_service
from app.services.ai_service import ai_service
from app.database import Database
from app.utils.helpers import prepare_for_mongo

logger = logging.getLogger("medintel.routes.whatsapp")

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.post("/send")
async def send_whatsapp(request: WhatsAppMessageRequest):
    """Send a WhatsApp message via Twilio."""
    try:
        if not whatsapp_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="WhatsApp service is not configured"
            )
        
        result = await whatsapp_service.send_message(
            request.to,
            request.message
        )
        
        return JSONResponse(result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


@router.post("/incoming")
async def whatsapp_incoming(request: Request):
    """
    Handle incoming WhatsApp messages from Twilio webhook.
    """
    try:
        data = await request.form()
        from_number = data.get("From", "")  # e.g., 'whatsapp:+918712355975'
        body = data.get("Body", "").strip()
        
        logger.info(f"📩 WhatsApp message from {from_number}: {body}")
        
        if not whatsapp_service.is_available():
            logger.error("WhatsApp service not configured")
            return PlainTextResponse("Service unavailable", status_code=503)
        
        if not ai_service:
            logger.error("AI service not available")
            return PlainTextResponse("AI service unavailable", status_code=503)
        
        # Create or find chat session for this WhatsApp user
        session_id = from_number.replace("whatsapp:", "")
        db = Database.get_db()
        session = await db.chat_sessions.find_one({"id": session_id})
        
        if not session:
            # Create a new session
            new_session = ChatSession(
                id=session_id,
                user_id=session_id,
                language="english"
            )
            await db.chat_sessions.insert_one(prepare_for_mongo(new_session.dict()))
            logger.info(f"🆕 New WhatsApp session created for {from_number}")
        
        # Generate AI reply
        ai_reply = await ai_service.generate_response(
            session_id,
            body,
            None,
            "english"
        )
        
        # Send reply back to WhatsApp
        await whatsapp_service.send_message(
            from_number.replace("whatsapp:", ""),
            ai_reply
        )
        
        logger.info(f"✅ Sent AI reply to {from_number}")
        return PlainTextResponse("OK", status_code=200)
    
    except Exception as e:
        logger.error(f"❌ Error in WhatsApp webhook: {e}")
        return PlainTextResponse("Error", status_code=500)
