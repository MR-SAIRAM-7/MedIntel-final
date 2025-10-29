"""
WhatsApp integration service using Twilio.
"""
import logging
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import config

logger = logging.getLogger("medintel.services.whatsapp")


class WhatsAppService:
    """Service for WhatsApp messaging via Twilio."""
    
    def __init__(self):
        """Initialize WhatsApp service."""
        self.account_sid = config.TWILIO_ACCOUNT_SID
        self.auth_token = config.TWILIO_AUTH_TOKEN
        self.whatsapp_number = config.TWILIO_WHATSAPP_NUMBER
        
        self.client = None
        if all([self.account_sid, self.auth_token, self.whatsapp_number]):
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("WhatsApp service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize WhatsApp service: {e}")
        else:
            logger.warning("WhatsApp service not configured - missing Twilio credentials")
    
    def is_available(self) -> bool:
        """Check if WhatsApp service is available."""
        return self.client is not None
    
    async def send_message(self, to_number: str, message_body: str) -> dict:
        """
        Send WhatsApp message.
        
        Args:
            to_number: Recipient phone number (e.g., "+919876543210")
            message_body: Message content
            
        Returns:
            Dictionary with status and message ID
            
        Raises:
            RuntimeError: If service is not configured
            TwilioRestException: If message sending fails
        """
        if not self.is_available():
            raise RuntimeError("WhatsApp service is not configured")
        
        try:
            message = self.client.messages.create(
                from_=f"whatsapp:{self.whatsapp_number}",
                body=message_body,
                to=f"whatsapp:{to_number}"
            )
            
            logger.info(f"WhatsApp message sent successfully: {message.sid}")
            return {
                "status": "success",
                "sid": message.sid,
                "to": to_number
            }
        
        except TwilioRestException as e:
            logger.error(f"Twilio error sending WhatsApp message: {e}")
            raise
        
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            raise


# Create global WhatsApp service instance
whatsapp_service = WhatsAppService()
