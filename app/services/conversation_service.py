"""
Servicio de negocio para gestión de conversaciones.
Maneja la lógica de sesiones y persistencia de interacciones.
"""
from datetime import datetime, timedelta
from typing import Optional
import uuid
import logging

from app.infrastructure.conversation_repository import ConversationRepository
from app.domain.interaction import Interaction

logger = logging.getLogger(__name__)


class ConversationService:
    """Servicio para gestionar conversaciones e interacciones"""

    def __init__(self):
        """Inicializa el servicio"""
        self.repository = ConversationRepository()
        self.current_session_id = None
        self.current_conversation_id = None
        self.session_timeout = timedelta(minutes=30)
        self.last_interaction_time = None

    def get_or_create_session(self) -> int:
        """
        Obtiene la sesión actual o crea una nueva si expiró.

        Returns:
            ID de la conversación activa
        """
        now = datetime.now()

        # Si no hay sesión o expiró, crear nueva
        if (not self.current_session_id or
            not self.last_interaction_time or
            now - self.last_interaction_time > self.session_timeout):

            self.current_session_id = str(uuid.uuid4())
            self.current_conversation_id = self.repository.create_conversation(
                session_id=self.current_session_id,
                started_at=now
            )
            logger.info(f"🆕 Nueva sesión creada: {self.current_session_id}")

        self.last_interaction_time = now
        return self.current_conversation_id

    def save_interaction(
        self,
        question: str,
        answer: str,
        intent: str,
        response_source: str,
        response_time_ms: int,
        confidence: Optional[float] = None
    ) -> int:
        """
        Guarda una interacción en la conversación actual.

        Args:
            question: Pregunta del usuario
            answer: Respuesta del asistente
            intent: Tipo de intención (product_search, instruction, etc.)
            response_source: Fuente de la respuesta (groq, database, etc.)
            response_time_ms: Tiempo de respuesta en milisegundos
            confidence: Score de confianza (opcional)

        Returns:
            ID de la interacción guardada
        """
        # Obtener o crear sesión
        conversation_id = self.get_or_create_session()

        # Crear entidad de interacción
        interaction = Interaction(
            id=None,
            conversation_id=conversation_id,
            question=question,
            answer=answer,
            intent_type=intent,
            response_source=response_source,
            response_time_ms=response_time_ms,
            confidence_score=confidence,
            created_at=datetime.now()
        )

        # Guardar en BD
        interaction_id = self.repository.save_interaction(conversation_id, interaction)
        logger.info(f"💾 Interacción guardada: ID={interaction_id}")

        return interaction_id

    def end_current_session(self):
        """Finaliza la sesión actual"""
        if self.current_conversation_id:
            self.repository.end_conversation(
                self.current_conversation_id,
                datetime.now()
            )
            logger.info(f"🏁 Sesión finalizada: {self.current_session_id}")
            self.current_session_id = None
            self.current_conversation_id = None
            self.last_interaction_time = None


__all__ = ["ConversationService"]
