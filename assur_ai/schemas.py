from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Score

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

class LeadRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    consent: bool = Field(..., description="Le prospect accepte d'être recontacté")
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class LeadResponse(BaseModel):
    lead_id: int
    created_at: str
    session_id: str
    intent: Optional[str] = None
    score: Score
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    consent: bool
    summary: Optional[str] = None
    extracted: Dict[str, Any] = Field(default_factory=dict)

class LeadsListResponse(BaseModel):
    leads: List[Dict[str, Any]]
