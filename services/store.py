from dataclasses import dataclass

@dataclass
class Session:
    o_filename: str
    result_bytes: bytes | None
    has_errors: bool


_sessions: dict[str, Session] = {}

def save(session_id: str, session: Session) -> None:
    _sessions[session_id] = session

def pop(session_id: str) -> Session | None:
    return _sessions.pop(session_id, None)