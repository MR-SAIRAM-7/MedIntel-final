from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone
from twilio.rest import Client
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.responses import PlainTextResponse
import os
import logging
import base64
import tempfile
import re
from PyPDF2 import PdfReader
import asyncio
import time

# ---------------------------
# Optional: Google Generative AI
# ---------------------------
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False

# ---------------------------
# Load environment
# ---------------------------
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# ---------------------------
# Twilio Setup
# ---------------------------
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
twilio_client = Client(account_sid, auth_token)

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("medintel.server")

# ---------------------------
# Env vars
# ---------------------------
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "medintel_db")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not MONGO_URL:
    raise RuntimeError("MONGO_URL is required")

# ---------------------------
# MongoDB
# ---------------------------
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ---------------------------
# FastAPI
# ---------------------------
app = FastAPI(title="MedIntel AI Health Assistant", description="AI-powered medical report analyzer")
api_router = APIRouter(prefix="/api")
active_connections: Dict[str, List[WebSocket]] = {}

# ---------------------------
# Models
# ---------------------------
class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    language: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str  # 'user' or 'assistant'
    content: str
    file_info: Optional[dict] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatSessionCreate(BaseModel):
    user_id: str
    language: Optional[str] = None

class SendMessageRequest(BaseModel):
    session_id: str
    message: str
    language: Optional[str] = None

class ImageContent:
    def __init__(self, image_base64: str, mime_type: str = "image/jpeg"):
        self.image_base64 = image_base64
        self.mime_type = mime_type

# ---------------------------
# Languages
# ---------------------------
SUPPORTED_LANGUAGES = [
    "english","hindi","spanish","tamil","telugu","kannada","malayalam",
    "punjabi","gujarati","marathi","bengali","odia","assamese",
    "urdu","chinese","arabic","japanese"
]

CONFIRMATION_MESSAGES = {
    "english": "Language has been changed to English. You can now talk to me in English. Do you have any health-related questions?",
    "hindi": "भाषा हिंदी में बदल दी गई है। अब आप मुझसे हिंदी में बात कर सकते हैं। आपका कोई स्वास्थ्य संबंधी प्रश्न है?",
    "spanish": "El idioma se ha cambiado a español. Ahora puede hablar conmigo en español. ¿Tiene alguna pregunta relacionada con la salud?",
    "tamil": "மொழி தமிழுக்கு மாற்றப்பட்டது. இப்போது நீங்கள் என்னுடன் தமிழில் பேசலாம். உங்கள் உடல்நலம் தொடர்பான கேள்விகள் உள்ளனவா?",
    "telugu": "భాష తెలుగుకు మార్చబడింది. ఇప్పుడు మీరు నాతో తెలుగులో మాట్లాడవచ్చు. మీ ఆరోగ్య సంబంధిత ప్రశ్నలు ఉన్నాయా?",
    "kannada": "ಭಾಷೆಯನ್ನು ಕನ್ನಡಕ್ಕೆ ಬದಲಾಯಿಸಲಾಗಿದೆ. ಈಗ ನೀವು ನನ್ನೊಂದಿಗೆ ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಬಹುದು. ನಿಮ್ಮ ಆರೋಗ್ಯ ಸಂಬಂಧಿತ ಪ್ರಶ್ನೆಗಳಿವೆಯೇ?",
    "malayalam": "ഭാഷ മലയാളത്തിലേക്ക് മാറ്റി. ഇപ്പോൾ നിങ്ങൾക്ക് എന്നോട് മലയാളത്തിൽ സംസാരിക്കാം. നിങ്ങളുടെ ആരോഗ്യ സംബന്ധമായ ചോദ്യങ്ങൾ ഉണ്ടോ?",
    "punjabi": "ਭਾਸ਼ਾ ਨੂੰ ਪੰਜਾਬੀ ਵਿੱਚ ਬਦਲ ਦਿੱਤਾ ਗਿਆ ਹੈ। ਹੁਣ ਤੁਸੀਂ ਮੇਰੇ ਨਾਲ ਪੰਜਾਬੀ ਵਿੱਚ ਗੱਲ ਕਰ ਸਕਦੇ ਹੋ। ਕੀ ਤੁਹਾਡੇ ਕੋਲ ਕੋਈ ਸਿਹਤ ਸੰਬੰਧੀ ਸਵਾਲ ਹਨ?",
    "gujarati": "ભાષા ગુજરાતીમાં બદલી દીધી છે। હવે તમે મારી સાથે ગુજરાતીમાં વાત કરી શકો છો. તમારા આરોગ્ય સંબંધિત કોઈ પ્રશ્નો છે?",
    "marathi": "भाषा मराठीत बदलली आहे। आता तुम्ही माझ्याशी मराठीत बोलू शकता. तुमचे आरोग्याशी संबंधित काही प्रश्न आहेत का?",
    "bengali": "ভাষা বাংলায় পরিবর্তন করা হয়েছে। এখন আপনি আমার সাথে বাংলায় কথা বলতে পারেন। আপনার স্বাস্থ্য সম্পর্কিত কোনো প্রশ্ন আছে?",
    "odia": "ଭାଷା ଓଡ଼ିଆରେ ବଦଳାଇ ଦିଆଗଲା। ଏବେ ଆପଣ ମୋ ସହିତ ଓଡ଼ିଆରେ କଥାବାର୍ତ୍ତା କରିପାରିବେ। ଆପଣଙ୍କର ସ୍ୱାସ୍ଥ୍ୟ ସମ୍ବନ୍ଧୀୟ କୌଣସି ପ୍ରଶ୍ନ ଅଛି କି?",
    "assamese": "ভাষা অসমীয়ালৈ সলনি কৰা হৈছে। এতিয়া আপুনি মোৰ লগত অসমীয়াত কথা পাতিব পাৰে। আপোনাৰ স্বাস্থ্য সম্পৰ্কীয় কোনো প্ৰশ্ন আছে নেকি?",
    "urdu": "زبان اردو میں تبدیل کر دی گئی ہے۔ اب آپ مجھ سے اردو میں بات کر سکتے ہیں۔ کیا آپ کے پاس کوئی صحت سے متعلق سوال ہے؟",
    "chinese": "语言已更改为中文。现在您可以用中文与我交谈。您有任何与健康相关的问题吗？",
    "arabic": "تم تغيير اللغة إلى العربية. الآن يمكنك التحدث معي بالعربية. هل لديك أي أسئلة متعلقة بالصحة؟",
    "japanese": "言語が日本語に変更されました。今、あなたは日本語で私と話すことができます。健康に関する質問はありますか？"
}

LANGUAGE_PROMPT = f"Hello! To provide the best assistance, what is your preferred language? Examples: {', '.join([l.capitalize() for l in SUPPORTED_LANGUAGES])}."

# ---------------------------
# Helpers
# ---------------------------
def prepare_for_mongo(data: dict) -> dict:
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, dict):
                data[key] = prepare_for_mongo(value)
    return data

def extract_text_from_pdf(path: str) -> str:
    try:
        reader = PdfReader(path)
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return text
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to extract text from PDF")

def detect_language_preference(msg: str) -> Optional[str]:
    if not msg:
        return None
    message_lower = msg.lower()
    
    language_patterns = {
        'english': [
            r'\b(english|अंग्रेजी|ஆங்கிலம்|తెలుగు|ಕನ್ನಡ|മലയാളം|ਅੰਗਰੇਜ਼ੀ|અંગ્રેજી|मराठी|বাংলা|ଇଂରାଜୀ|অসমীয়া|اردو|中文|عربية|日本語)\b',
            r'\b(talk in english|speak english|use english)\b'
        ],
        'hindi': [
            r'\b(hindi|हिंदी|हिन्दी|ஹிந்தி|హిందీ|ಹಿಂದಿ|ഹിന്ദി|ਹਿੰਦੀ|હિંદી|हिंदी|হিন্দি|ହିନ୍ଦୀ|হিন্দি)\b',
            r'\b(talk in hindi|speak hindi|use hindi)\b',
            r'\b(मुझसे हिंदी में बात करो|हिंदी में बोलो)\b'
        ],
        'spanish': [
            r'\b(spanish|español|espanol)\b',
            r'\b(talk in spanish|speak spanish|use spanish)\b',
            r'\b(habla español|en español)\b'
        ],
        'tamil': [
            r'\b(tamil|தமிழ்)\b',
            r'\b(talk in tamil|speak tamil|use tamil)\b',
            r'\b(தமிழில் பேசு|தமிழில் பேசவும்)\b'
        ],
        'telugu': [
            r'\b(telugu|తెలుగు)\b',
            r'\b(talk in telugu|speak telugu|use telugu)\b',
            r'\b(తెలుగులో మాట్లాడు|తెలుగులో మాట్లాడండి)\b'
        ],
        'kannada': [
            r'\b(kannada|ಕನ್ನಡ)\b',
            r'\b(talk in kannada|speak kannada|use kannada)\b',
            r'\b(ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ|ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ)\b'
        ],
        'malayalam': [
            r'\b(malayalam|മലയാളം)\b',
            r'\b(talk in malayalam|speak malayalam|use malayalam)\b',
            r'\b(മലയാളത്തിൽ സംസാരിക്കുക|മലയാളത്തിൽ സംസാരിക്കൂ)\b'
        ],
        'punjabi': [
            r'\b(punjabi|ਪੰਜਾਬੀ)\b',
            r'\b(talk in punjabi|speak punjabi|use punjabi)\b',
            r'\b(ਪੰਜਾਬੀ ਵਿੱਚ ਗੱਲ ਕਰੋ|ਪੰਜਾਬੀ ਵਿੱਚ ਗੱਲ ਕਰੋ)\b'
        ],
        'gujarati': [
            r'\b(gujarati|ગુજરાતી)\b',
            r'\b(talk in gujarati|speak gujarati|use gujarati)\b',
            r'\b(ગુજરાતીમાં વાત કરો|ગુજરાતીમાં વાત કરો)\b'
        ],
        'marathi': [
            r'\b(marathi|मराठी)\b',
            r'\b(talk in marathi|speak marathi|use marathi)\b',
            r'\b(मराठीत बोल|मराठीत बोल)\b'
        ],
        'bengali': [
            r'\b(bengali|বাংলা)\b',
            r'\b(talk in bengali|speak bengali|use bengali)\b',
            r'\b(বাংলায় কথা বলুন|বাংলায় কথা বলুন)\b'
        ],
        'odia': [
            r'\b(odia|ଓଡ଼ିଆ)\b',
            r'\b(talk in odia|speak odia|use odia)\b',
            r'\b(ଓଡ଼ିଆରେ କଥା ହୁଅନ୍ତୁ)\b'
        ],
        'assamese': [
            r'\b(assamese|অসমীয়া)\b',
            r'\b(talk in assamese|speak assamese|use assamese)\b',
            r'\b(অসমীয়াত কথা পাতক)\b'
        ],
        'urdu': [
            r'\b(urdu|اردو)\b',
            r'\b(talk in urdu|speak urdu|use urdu)\b'
        ],
        'chinese': [
            r'\b(chinese|中文)\b',
            r'\b(talk in chinese|speak chinese|use chinese)\b'
        ],
        'arabic': [
            r'\b(arabic|عربية)\b',
            r'\b(talk in arabic|speak arabic|use arabic)\b'
        ],
        'japanese': [
            r'\b(japanese|日本語)\b',
            r'\b(talk in japanese|speak japanese|use japanese)\b'
        ]
    }
    
    for language, patterns in language_patterns.items():
        for pattern in patterns:
            if re.search(pattern, message_lower):
                return language
    
    return None

async def broadcast_message(session_id: str, text: str):
    if session_id in active_connections:
        for ws in active_connections[session_id][:]:
            try:
                await ws.send_text(text)
            except Exception as e:
                logger.error(f"Broadcast error: {str(e)}")
                active_connections[session_id].remove(ws)
        if not active_connections[session_id]:
            del active_connections[session_id]

# ---------------------------
# AI core
# ---------------------------
async def get_ai_response(session_id: str, user_message: str, file_content: Optional[ImageContent] = None, language: str = "english") -> str:
    if not GENAI_AVAILABLE:
        raise RuntimeError("Google Generative AI library not available")
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    genai.configure(api_key=GEMINI_API_KEY)

    # Load history
    history_docs = await db.chat_messages.find({"session_id": session_id}).sort("timestamp", 1).to_list(100)
    history = []
    for m in history_docs:
        role = "user" if m["role"] == "user" else "model"
        history.append({"role": role, "parts": [m["content"]]})

    system_instruction = f"""
You are Dr. MedIntel, a highly experienced and compassionate AI physician assistant.
CRITICAL: You MUST respond in {language.upper()} language only.
- Use the appropriate script for the language.
- Translate medical terms where possible, provide English in parentheses if needed.
- Simplify complex medical terminology.
- Structure responses with: Summary, Key Findings, Recommendations, Disclaimers.
- Always include: "⚠️ This is not medical advice. Please consult a real doctor for professional medical advice."
"""

    # Use available models
    model_names = ["gemini-2.0-flash", "gemini-1.5-flash"]

    last_error = None
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction,
                generation_config=genai.GenerationConfig(temperature=0.7, max_output_tokens=1500),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            chat = model.start_chat(history=history)

            # Prepare content
            content = [user_message]
            if file_content:
                content.append({
                    "mime_type": file_content.mime_type,
                    "data": file_content.image_base64
                })

            # Send with retry
            for attempt in range(3):
                try:
                    response = await asyncio.to_thread(chat.send_message, content)
                    return response.text.strip()
                except genai.types.generation_types.BlockedPromptException as e:
                    logger.error(f"Blocked prompt: {str(e)}")
                    raise HTTPException(status_code=400, detail="Content blocked due to safety filters")
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        if attempt < 2:
                            wait = 2 ** attempt
                            logger.warning(f"Quota error, retrying in {wait}s...")
                            await asyncio.sleep(wait)
                            continue
                    last_error = e
                    break
        except Exception as e:
            last_error = e
            continue

    logger.error(f"AI response failed: {str(last_error)}")
    raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(last_error)}")

# ---------------------------
# Routes
# ---------------------------
@api_router.get("/")
async def root():
    return {"message": "MedIntel AI Health Assistant API is running"}

@api_router.post("/chat/session", response_model=ChatSession)
async def create_chat_session(data: ChatSessionCreate):
    session = ChatSession(**data.dict())
    await db.chat_sessions.insert_one(prepare_for_mongo(session.dict()))
    return session

@api_router.get("/chat/session/{session_id}", response_model=ChatSession)
async def get_chat_session(session_id: str):
    session = await db.chat_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return ChatSession(**session)

@api_router.get("/chat/session/{session_id}/messages", response_model=List[ChatMessage])
async def get_chat_messages(session_id: str):
    messages = await db.chat_messages.find({"session_id": session_id}).sort("timestamp", 1).to_list(1000)
    return [ChatMessage(**msg) for msg in messages]

@api_router.post("/chat/message")
async def send_message(req: SendMessageRequest):
    session = await db.chat_sessions.find_one({"id": req.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    lang = req.language or session.get("language")

    detected = detect_language_preference(req.message)
    if detected and detected in SUPPORTED_LANGUAGES:
        await db.chat_sessions.update_one(
            {"id": req.session_id},
            {"$set": {"language": detected, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        reply = CONFIRMATION_MESSAGES.get(detected, f"Language changed to {detected.capitalize()}.")
        
        user_msg = ChatMessage(session_id=req.session_id, role="user", content=req.message)
        await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))
        
        assistant_msg = ChatMessage(session_id=req.session_id, role="assistant", content=reply)
        await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))
        
        await broadcast_message(req.session_id, reply)
        
        return {"user_message": user_msg, "assistant_message": assistant_msg}

    if lang is None:
        reply = LANGUAGE_PROMPT
        
        user_msg = ChatMessage(session_id=req.session_id, role="user", content=req.message)
        await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))
        
        assistant_msg = ChatMessage(session_id=req.session_id, role="assistant", content=reply)
        await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))
        
        await broadcast_message(req.session_id, reply)
        
        return {"user_message": user_msg, "assistant_message": assistant_msg}

    user_msg = ChatMessage(session_id=req.session_id, role="user", content=req.message)
    await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))

    ai_reply = await get_ai_response(req.session_id, req.message, None, lang)

    assistant_msg = ChatMessage(session_id=req.session_id, role="assistant", content=ai_reply)
    await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))

    await broadcast_message(req.session_id, ai_reply)

    return {"user_message": user_msg, "assistant_message": assistant_msg}

@api_router.post("/chat/upload")
async def upload_and_analyze_file(
    session_id: str = Form(...),
    message: str = Form("Please analyze this medical report/image and provide insights."),
    language: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    session = await db.chat_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    lang = language or session.get("language", "english")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large. Maximum 10MB")

    file_info = {"filename": file.filename, "content_type": file.content_type, "size": len(file_bytes)}

    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=f"{message} [Uploaded file: {file.filename}]",
        file_info=file_info
    )
    await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))

    file_content = None
    processed_message = message

    if file.content_type == "application/pdf":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name
        try:
            pdf_text = extract_text_from_pdf(temp_path)
            processed_message = f"{message}\n\nMedical Report Content:\n{pdf_text}"
        finally:
            os.unlink(temp_path)
    elif file.content_type.startswith("image/"):
        base64_data = base64.b64encode(file_bytes).decode("utf-8")
        file_content = ImageContent(image_base64=base64_data, mime_type=file.content_type)
        processed_message = f"{message}\n\nAnalyze this medical image for findings, abnormalities, or insights."
    elif file.content_type.startswith("text/"):
        try:
            text_content = file_bytes.decode("utf-8")
            processed_message = f"{message}\n\nMedical Document Content:\n{text_content}"
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Cannot decode text file")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF, image, or text files.")

    ai_reply = await get_ai_response(session_id, processed_message, file_content, lang)

    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_reply
    )
    await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))

    await broadcast_message(session_id, ai_reply)

    return {"user_message": user_msg, "assistant_message": assistant_msg}

@api_router.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str):
    await db.chat_messages.delete_many({"session_id": session_id})
    result = await db.chat_sessions.delete_one({"id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"message": "Chat session deleted successfully"}

@api_router.get("/chat/sessions/{user_id}", response_model=List[ChatSession])
async def get_user_sessions(user_id: str):
    sessions = await db.chat_sessions.find({"user_id": user_id}).sort("updated_at", -1).to_list(100)
    return [ChatSession(**s) for s in sessions]

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat(), "service": "MedIntel AI Health Assistant"}

@api_router.post("/chat/language/{session_id}")
async def change_language(session_id: str, language: str):
    if language.lower() not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language. Supported: {', '.join(SUPPORTED_LANGUAGES)}")
    
    session = await db.chat_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    await db.chat_sessions.update_one(
        {"id": session_id},
        {"$set": {"language": language.lower(), "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    reply = CONFIRMATION_MESSAGES.get(language.lower(), f"Language changed to {language.capitalize()}.")
    await broadcast_message(session_id, reply)
    
    return {"message": reply, "language": language.lower()}

@api_router.post("/send-whatsapp")
async def send_whatsapp(request: Request):
    try:
        data = await request.json()
        to_number = data.get("to")        # e.g., "+919876543210"
        message_body = data.get("message")

        message = twilio_client.messages.create(
            from_=f"whatsapp:{whatsapp_number}",
            body=message_body,
            to=f"whatsapp:{to_number}"
        )

        return JSONResponse({"status": "success", "sid": message.sid})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@api_router.post("/whatsapp/incoming")
async def whatsapp_incoming(request: Request):
    """
    Handles incoming WhatsApp messages from Twilio and returns an AI-generated reply.
    """
    try:
        data = await request.form()
        from_number = data.get("From")  # e.g. 'whatsapp:+918712355975'
        body = data.get("Body", "").strip()

        print(f"📩 WhatsApp message from {from_number}: {body}")

        # Create or find chat session for this WhatsApp user
        session_id = from_number.replace("whatsapp:", "")
        session = await db.chat_sessions.find_one({"id": session_id})

        if not session:
            # Create a new session if not found
            new_session = ChatSession(
                id=session_id,
                user_id=session_id,
                language="english"
            )
            await db.chat_sessions.insert_one(prepare_for_mongo(new_session.dict()))
            print(f"🆕 New session created for {from_number}")

        # Generate AI reply using your existing logic
        ai_reply = await get_ai_response(session_id, body, None, "english")

        # Send reply back to WhatsApp via Twilio
        twilio_client.messages.create(
            from_=f"whatsapp:{whatsapp_number}",
            body=ai_reply,
            to=from_number
        )

        print(f"✅ Sent AI reply to {from_number}")
        return PlainTextResponse("OK", status_code=200)

    except Exception as e:
        print(f"❌ Error in WhatsApp webhook: {e}")
        return PlainTextResponse("Error", status_code=500)


# ---------------------------
# WebSocket
# ---------------------------
@app.websocket("/ws/{session_id}")
async def ws_endpoint(ws: WebSocket, session_id: str):
    await ws.accept()
    if session_id not in active_connections:
        active_connections[session_id] = []
    active_connections[session_id].append(ws)
    
    try:
        while True:
            msg = await ws.receive_text()
            session = await db.chat_sessions.find_one({"id": session_id})
            if not session:
                await ws.send_text("Session not found")
                continue
            
            lang = session.get("language")
            
            detected = detect_language_preference(msg)
            if detected and detected in SUPPORTED_LANGUAGES:
                await db.chat_sessions.update_one(
                    {"id": session_id},
                    {"$set": {"language": detected, "updated_at": datetime.now(timezone.utc).isoformat()}}
                )
                reply = CONFIRMATION_MESSAGES.get(detected, f"Language changed to {detected.capitalize()}.")
                
                user_msg = ChatMessage(session_id=session_id, role="user", content=msg)
                await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))
                
                assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=reply)
                await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))
                
                await broadcast_message(session_id, reply)
                continue
            
            if lang is None:
                reply = LANGUAGE_PROMPT
                
                user_msg = ChatMessage(session_id=session_id, role="user", content=msg)
                await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))
                
                assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=reply)
                await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))
                
                await broadcast_message(session_id, reply)
                continue
            
            user_msg = ChatMessage(session_id=session_id, role="user", content=msg)
            await db.chat_messages.insert_one(prepare_for_mongo(user_msg.dict()))
            
            ai_reply = await get_ai_response(session_id, msg, None, lang)
            
            assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=ai_reply)
            await db.chat_messages.insert_one(prepare_for_mongo(assistant_msg.dict()))
            
            await broadcast_message(session_id, ai_reply)
    except WebSocketDisconnect:
        if ws in active_connections.get(session_id, []):
            active_connections[session_id].remove(ws)
        if not active_connections.get(session_id):
            del active_connections[session_id]

# ---------------------------
# Mount
# ---------------------------
app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("shutdown")
async def shutdown():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)