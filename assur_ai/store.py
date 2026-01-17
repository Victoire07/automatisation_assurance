import uuid
from typing import Dict, List

SESSIONS: Dict[str, List[dict]] = {}

def new_session_id() -> str:
    return str(uuid.uuid4())

def get_history(session_id: str) -> List[dict]:
    return SESSIONS.get(session_id, [])

def append_message(session_id: str, role: str, content: str):
    SESSIONS.setdefault(session_id, []).append({"role": role, "content": content})
