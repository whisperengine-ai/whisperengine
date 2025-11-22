from fastapi import APIRouter, HTTPException
from src_v2.api.models import ChatRequest, ChatResponse
from src_v2.agents.engine import AgentEngine
from src_v2.config.settings import settings
from src_v2.core.character import character_manager
from datetime import datetime
import time
from loguru import logger

router = APIRouter()
agent_engine = AgentEngine()

@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    start_time = time.time()
    
    # Load character
    bot_name = settings.DISCORD_BOT_NAME
    if not bot_name:
        raise HTTPException(status_code=500, detail="Bot name not configured")
        
    character = character_manager.get_character(bot_name)
    if not character:
        raise HTTPException(status_code=500, detail=f"Character {bot_name} not found")

    try:
        # Generate response
        response_text = await agent_engine.generate_response(
            character=character,
            user_message=request.message,
            user_id=request.user_id,
            context_variables=request.context or {}
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            success=True,
            response=response_text,
            timestamp=datetime.now(),
            bot_name=bot_name,
            processing_time_ms=processing_time,
            memory_stored=True
        )
        
    except Exception as e:
        logger.exception("Error processing chat request")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}
