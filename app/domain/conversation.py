"""
Entidad de dominio para Conversación.
Representa una sesión de chat con el asistente.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Conversation:
    """Entidad de dominio para una conversación"""
    id: Optional[int]
    session_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    total_interactions: int
    created_at: datetime
    updated_at: datetime
