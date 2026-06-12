from sqlalchemy.orm import Session as DBSession
from backend.db.models import Session, Conversation
from typing import List

def get_conversation_history(db: DBSession, session_id: str, limit: int = 10) -> List[dict]:
    # Fetch last N messages
    msgs = db.query(Conversation).filter(Conversation.session_id == session_id).order_by(Conversation.timestamp.desc()).limit(limit).all()
    # Return in chronological order
    msgs.reverse()
    return [{"role": m.role, "content": m.content} for m in msgs]

def add_message(db: DBSession, session_id: str, role: str, content: str):
    msg = Conversation(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
