import os, json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI

from assur_ai.prompt import SYSTEM_PROMPT
from assur_ai.schemas import ChatRequest, ChatResponse
from assur_ai.store import new_session_id, get_history, append_message

app = FastAPI(title="Automatisation Assurance - MVP", version="1.0")
INTENTS = ["auto", "habitation", "sante", "pro", "emprunteur", "autre"]

@app.on_event("startup")
def startup():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY manquante dans .env (à la racine du repo).")
    app.state.client = OpenAI(api_key=api_key)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        client: OpenAI = app.state.client
        session_id = req.session_id or new_session_id()

        history = get_history(session_id)
        append_message(session_id, "user", req.message)

        meta_prompt = f"""
Réponds au client, puis ajoute à la fin un bloc JSON sur une seule ligne.

Le JSON DOIT contenir exactement ces clés:
intent (one of {INTENTS}),
handoff_recommended (true/false),
lead_suggested (true/false),
next_questions (array of strings),
extracted (object)

Format EXACT:
<réponse client>

JSON: {{"intent":"auto","handoff_recommended":false,"lead_suggested":true,"next_questions":["..."],"extracted":{{...}}}}
""".strip()

        trimmed = history[-12:]

        resp = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": meta_prompt},
                *trimmed,
                {"role": "user", "content": req.message},
            ],
        )

        text = resp.output_text.strip()

        reply = text
        meta = {
            "intent": None,
            "handoff_recommended": False,
            "lead_suggested": False,
            "next_questions": [],
            "extracted": {},
        }

        if "\nJSON:" in text:
            reply_part, json_part = text.rsplit("\nJSON:", 1)
            reply = reply_part.strip()
            try:
                meta = json.loads(json_part.strip())
            except Exception:
                pass

        append_message(session_id, "assistant", reply)

        return ChatResponse(
            session_id=session_id,
            reply=reply,
            intent=meta.get("intent"),
            handoff_recommended=bool(meta.get("handoff_recommended", False)),
            lead_suggested=bool(meta.get("lead_suggested", False)),
            next_questions=list(meta.get("next_questions", []))[:6],
            extracted=dict(meta.get("extracted", {})),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
