import uuid

from eaia.schemas import EmailData


def conversation_id_for_email(email: EmailData) -> str:
    """Derive a stable LangGraph thread/conversation id for one Gmail message."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"gmail-message:{email['id']}"))
