"""
Main server module for MedIntel AI Health Assistant.
Modular FastAPI application with proper separation of concerns.
"""
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import logging

from app.config import config
from app.database import Database
from app.routes import chat, whatsapp
from app.websocket import handle_websocket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("medintel.server")

# Initialize FastAPI app
app = FastAPI(
    title="MedIntel AI Health Assistant",
    description="AI-powered medical report analyzer with multilingual support",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
async def startup():
    """Initialize services on startup."""
    try:
        # Validate configuration
        config.validate()
        
        # Connect to database
        Database.connect()
        
        logger.info("✅ MedIntel server started successfully")
        logger.info(f"📊 Database: {config.DB_NAME}")
        logger.info(f"🌐 CORS origins: {config.CORS_ORIGINS}")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    try:
        Database.close()
        logger.info("✅ MedIntel server shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Root endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "MedIntel AI Health Assistant API",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "message": "MedIntel AI Health Assistant API is running",
        "version": "2.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "MedIntel AI Health Assistant",
        "version": "2.0.0"
    }


# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    await handle_websocket(websocket, session_id)


# Include routers
app.include_router(chat.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.RELOAD
    )
