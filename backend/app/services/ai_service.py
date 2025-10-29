"""
AI service for generating responses using Google Generative AI.
"""
import asyncio
import logging
from typing import Optional
from fastapi import HTTPException

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False

from app.config import config
from app.models.chat import ImageContent
from app.database import Database

logger = logging.getLogger("medintel.services.ai")


class AIService:
    """Service for AI-powered medical assistance."""
    
    def __init__(self):
        """Initialize AI service."""
        if not GENAI_AVAILABLE:
            raise RuntimeError("Google Generative AI library not available")
        if not config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")
        
        genai.configure(api_key=config.GEMINI_API_KEY)
    
    def _get_system_instruction(self, language: str) -> str:
        """
        Generate system instruction for AI model.
        
        Args:
            language: Target language for response
            
        Returns:
            System instruction string
        """
        return f"""
You are Dr. MedIntel, a highly experienced and compassionate AI physician assistant.
CRITICAL: You MUST respond in {language.upper()} language only.
- Use the appropriate script for the language.
- Translate medical terms where possible, provide English in parentheses if needed.
- Simplify complex medical terminology.
- Structure responses with: Summary, Key Findings, Recommendations, Disclaimers.
- Always include: "⚠️ This is not medical advice. Please consult a real doctor for professional medical advice."
"""
    
    async def _load_chat_history(self, session_id: str) -> list:
        """
        Load chat history from database.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of chat history messages
        """
        db = Database.get_db()
        history_docs = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(100)
        
        history = []
        for m in history_docs:
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [m["content"]]})
        
        return history
    
    async def generate_response(
        self,
        session_id: str,
        user_message: str,
        file_content: Optional[ImageContent] = None,
        language: str = "english"
    ) -> str:
        """
        Generate AI response for user message.
        
        Args:
            session_id: Session identifier
            user_message: User's input message
            file_content: Optional image content
            language: Target language for response
            
        Returns:
            AI-generated response text
            
        Raises:
            HTTPException: If AI generation fails
        """
        try:
            # Load conversation history
            history = await self._load_chat_history(session_id)
            
            # Get system instruction
            system_instruction = self._get_system_instruction(language)
            
            # Try different models
            last_error = None
            for model_name in config.AI_MODEL_NAMES:
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction,
                        generation_config=genai.GenerationConfig(
                            temperature=config.AI_TEMPERATURE,
                            max_output_tokens=config.AI_MAX_OUTPUT_TOKENS
                        ),
                        safety_settings={
                            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        }
                    )
                    
                    chat = model.start_chat(history=history)
                    
                    # Prepare content with optional image
                    content = [user_message]
                    if file_content:
                        content.append({
                            "mime_type": file_content.mime_type,
                            "data": file_content.image_base64
                        })
                    
                    # Send message with retry logic
                    for attempt in range(config.AI_MAX_RETRIES):
                        try:
                            response = await asyncio.to_thread(chat.send_message, content)
                            return response.text.strip()
                        
                        except genai.types.generation_types.BlockedPromptException as e:
                            logger.error(f"Blocked prompt: {str(e)}")
                            raise HTTPException(
                                status_code=400,
                                detail="Content blocked due to safety filters"
                            )
                        
                        except Exception as e:
                            # Handle rate limiting
                            if "429" in str(e) or "quota" in str(e).lower():
                                if attempt < config.AI_MAX_RETRIES - 1:
                                    wait_time = 2 ** attempt
                                    logger.warning(f"Rate limit hit, retrying in {wait_time}s...")
                                    await asyncio.sleep(wait_time)
                                    continue
                            last_error = e
                            break
                
                except Exception as e:
                    last_error = e
                    logger.warning(f"Model {model_name} failed: {str(e)}")
                    continue
            
            # All models failed
            logger.error(f"AI response failed: {str(last_error)}")
            raise HTTPException(
                status_code=503,
                detail=f"AI service unavailable: {str(last_error)}"
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in AI service: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}"
            )


# Create global AI service instance
ai_service = AIService() if GENAI_AVAILABLE else None
