"""
Entidad de dominio para Interacción.
Representa un intercambio pregunta-respuesta en el chat.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Interaction:
    """Entidad de dominio para una interacción (pregunta-respuesta)"""
    id: Optional[int]
    conversation_id: int
    question: str
    answer: str
    intent_type: str  # product_search, instruction, general, offtopic
    response_source: str  # groq, database, groq+database, knowledge_base
    response_time_ms: int
    confidence_score: Optional[float]
    created_at: datetime
