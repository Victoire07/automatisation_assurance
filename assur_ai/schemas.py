from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default=None)
    message: str = Field(..., min_length=1)

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: Optional[str] = None
    handoff_recommended: bool = False
    lead_suggested: bool = False
    next_questions: List[str] = Field(default_factory=list)
    extracted: Dict[str, Any] = Field(default_factory=dict)
