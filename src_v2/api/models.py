from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    message: str = Field(..., description="The user's message")
    metadata_level: str = Field(default="standard", description="Detail level of response metadata")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

class ChatResponse(BaseModel):
    success: bool
    response: str
    timestamp: datetime
    bot_name: str
    processing_time_ms: float
    memory_stored: bool = True
    metadata: Optional[Dict[str, Any]] = None
    user_facts: Optional[Dict[str, Any]] = None
    relationship_metrics: Optional[Dict[str, Any]] = None

class BatchChatRequest(BaseModel):
    metadata_level: str = "standard"
    messages: List[ChatRequest]

class BatchChatResponse(BaseModel):
    results: List[ChatResponse]
    total_processed: int
    timestamp: datetime
    bot_name: str
