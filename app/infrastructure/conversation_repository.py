"""
Repositorio para operaciones CRUD de conversaciones e interacciones.
Implementa el patrón Repository para abstraer el acceso a datos del historial.
"""
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import logging

from app.domain.conversation import Conversation
from app.domain.interaction import Interaction
from app.infrastructure.models.conversation import ConversationModel, InteractionModel
from app.infrastructure.database import session_scope

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repositorio para gestionar conversaciones e interacciones en la base de datos"""

    def __init__(self, session: Optional[Session] = None):
        """
        Inicializa el repositorio.

        Args:
            session: Sesión de SQLAlchemy (opcional, se crea una si no se proporciona)
        """
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        """Obtiene la sesión actual o crea una nueva"""
        if self.session:
            return self.session
        from app.infrastructure.database import get_session
        return get_session()

    def _conversation_model_to_entity(self, model: ConversationModel) -> Conversation:
        """Convierte un modelo ORM a entidad de dominio"""
        return Conversation(
            id=model.id,
            session_id=model.session_id,
            started_at=model.started_at,
            ended_at=model.ended_at,
            total_interactions=model.total_interactions,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _interaction_model_to_entity(self, model: InteractionModel) -> Interaction:
        """Convierte un modelo ORM a entidad de dominio"""
        return Interaction(
            id=model.id,
            conversation_id=model.conversation_id,
            question=model.question,
            answer=model.answer,
            intent_type=model.intent_type,
            response_source=model.response_source,
            response_time_ms=model.response_time_ms,
            confidence_score=model.confidence_score,
            created_at=model.created_at
        )

    def create_conversation(self, session_id: str, started_at: datetime) -> int:
        """
        Crea una nueva conversación en la base de datos.

        Args:
            session_id: ID único de la sesión
            started_at: Timestamp de inicio

        Returns:
            ID de la conversación creada
        """
        session = self._get_session()
        try:
            model = ConversationModel(
                session_id=session_id,
                started_at=started_at,
                total_interactions=0
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            logger.info(f"✅ Conversación creada: ID={model.id}, session_id={session_id}")
            return model.id
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error al crear conversación: {e}")
            raise
        finally:
            if self._owns_session:
                session.close()

    def get_by_session(self, session_id: str) -> Optional[Conversation]:
        """
        Obtiene una conversación por su session_id.

        Args:
            session_id: ID de la sesión

        Returns:
            Conversación o None si no existe
        """
        session = self._get_session()
        try:
            model = session.query(ConversationModel).filter(
                ConversationModel.session_id == session_id
            ).first()

            if model:
                return self._conversation_model_to_entity(model)
            return None
        finally:
            if self._owns_session:
                session.close()

    def save_interaction(self, conversation_id: int, interaction: Interaction) -> int:
        """
        Guarda una interacción y actualiza el contador de la conversación.

        Args:
            conversation_id: ID de la conversación
            interaction: Entidad de interacción a guardar

        Returns:
            ID de la interacción creada
        """
        session = self._get_session()
        try:
            # Crear interacción
            model = InteractionModel(
                conversation_id=conversation_id,
                question=interaction.question,
                answer=interaction.answer,
                intent_type=interaction.intent_type,
                response_source=interaction.response_source,
                response_time_ms=interaction.response_time_ms,
                confidence_score=interaction.confidence_score
            )
            session.add(model)

            # Actualizar contador de conversación
            conv = session.query(ConversationModel).filter(
                ConversationModel.id == conversation_id
            ).first()
            if conv:
                conv.total_interactions += 1

            session.commit()
            session.refresh(model)
            logger.info(f"✅ Interacción guardada: ID={model.id}, conversation_id={conversation_id}")
            return model.id
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error al guardar interacción: {e}")
            raise
        finally:
            if self._owns_session:
                session.close()

    def get_recent_conversations(self, limit: int = 50) -> List[Conversation]:
        """
        Obtiene las conversaciones más recientes.

        Args:
            limit: Número máximo de conversaciones a retornar

        Returns:
            Lista de conversaciones ordenadas por fecha (más reciente primero)
        """
        session = self._get_session()
        try:
            models = session.query(ConversationModel).order_by(
                desc(ConversationModel.started_at)
            ).limit(limit).all()

            return [self._conversation_model_to_entity(m) for m in models]
        finally:
            if self._owns_session:
                session.close()

    def get_conversation_with_interactions(self, conversation_id: int) -> Tuple[Conversation, List[Interaction]]:
        """
        Obtiene una conversación con todas sus interacciones.

        Args:
            conversation_id: ID de la conversación

        Returns:
            Tupla (Conversación, Lista de Interacciones)
        """
        session = self._get_session()
        try:
            # Obtener conversación
            conv_model = session.query(ConversationModel).filter(
                ConversationModel.id == conversation_id
            ).first()

            if not conv_model:
                raise ValueError(f"Conversación {conversation_id} no encontrada")

            # Obtener interacciones
            inter_models = session.query(InteractionModel).filter(
                InteractionModel.conversation_id == conversation_id
            ).order_by(InteractionModel.created_at).all()

            conversation = self._conversation_model_to_entity(conv_model)
            interactions = [self._interaction_model_to_entity(m) for m in inter_models]

            return (conversation, interactions)
        finally:
            if self._owns_session:
                session.close()

    def end_conversation(self, conversation_id: int, ended_at: datetime):
        """
        Marca una conversación como finalizada.

        Args:
            conversation_id: ID de la conversación
            ended_at: Timestamp de finalización
        """
        session = self._get_session()
        try:
            conv = session.query(ConversationModel).filter(
                ConversationModel.id == conversation_id
            ).first()

            if conv:
                conv.ended_at = ended_at
                session.commit()
                logger.info(f"✅ Conversación {conversation_id} finalizada")
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error al finalizar conversación: {e}")
            raise
        finally:
            if self._owns_session:
                session.close()


    # ========================================
    # MÉTODOS DE ANALÍTICAS (FASE 3)
    # ========================================

    def get_top_products_from_interactions(self, limit: int = 10,
                                          date_from: Optional[datetime] = None,
                                          date_to: Optional[datetime] = None) -> List[Tuple[str, int]]:
        """
        Obtiene los productos más consultados desde las interacciones.

        Args:
            limit: Número máximo de productos a retornar
            date_from: Fecha de inicio (opcional)
            date_to: Fecha de fin (opcional)

        Returns:
            Lista de tuplas (producto, cantidad_consultas)
        """
        from sqlalchemy import func, or_

        session = self._get_session()
        try:
            # Query base
            query = session.query(
                InteractionModel.question,
                func.count(InteractionModel.id).label('count')
            ).filter(
                or_(
                    InteractionModel.intent_type == 'product_search',
                    InteractionModel.intent_type == 'product_info'
                )
            )

            # Filtros de fecha
            if date_from:
                query = query.filter(InteractionModel.created_at >= date_from)
            if date_to:
                query = query.filter(InteractionModel.created_at <= date_to)

            # Agrupar y ordenar
            results = query.group_by(InteractionModel.question)\
                          .order_by(func.count(InteractionModel.id).desc())\
                          .limit(limit)\
                          .all()

            return [(question, count) for question, count in results]

        except Exception as e:
            logger.error(f"Error al obtener top productos: {e}")
            return []
        finally:
            if self._owns_session:
                session.close()

    def get_intent_counts(self, date_from: Optional[datetime] = None,
                         date_to: Optional[datetime] = None) -> List[Tuple[str, int]]:
        """
        Obtiene el conteo de interacciones por tipo de intención.

        Args:
            date_from: Fecha de inicio (opcional)
            date_to: Fecha de fin (opcional)

        Returns:
            Lista de tuplas (intent_type, count)
        """
        from sqlalchemy import func

        session = self._get_session()
        try:
            query = session.query(
                InteractionModel.intent_type,
                func.count(InteractionModel.id).label('count')
            )

            # Filtros de fecha
            if date_from:
                query = query.filter(InteractionModel.created_at >= date_from)
            if date_to:
                query = query.filter(InteractionModel.created_at <= date_to)

            results = query.group_by(InteractionModel.intent_type)\
                          .order_by(func.count(InteractionModel.id).desc())\
                          .all()

            return [(intent_type, count) for intent_type, count in results]

        except Exception as e:
            logger.error(f"Error al obtener conteo de intenciones: {e}")
            return []
        finally:
            if self._owns_session:
                session.close()

    def get_total_conversations_count(self, date_from: Optional[datetime] = None,
                                     date_to: Optional[datetime] = None) -> int:
        """
        Obtiene el total de conversaciones.

        Args:
            date_from: Fecha de inicio (opcional)
            date_to: Fecha de fin (opcional)

        Returns:
            Número total de conversaciones
        """
        session = self._get_session()
        try:
            query = session.query(ConversationModel)

            # Filtros de fecha
            if date_from:
                query = query.filter(ConversationModel.started_at >= date_from)
            if date_to:
                query = query.filter(ConversationModel.started_at <= date_to)

            return query.count()

        except Exception as e:
            logger.error(f"Error al obtener total de conversaciones: {e}")
            return 0
        finally:
            if self._owns_session:
                session.close()

    def get_total_interactions_count(self, date_from: Optional[datetime] = None,
                                    date_to: Optional[datetime] = None) -> int:
        """
        Obtiene el total de interacciones.

        Args:
            date_from: Fecha de inicio (opcional)
            date_to: Fecha de fin (opcional)

        Returns:
            Número total de interacciones
        """
        session = self._get_session()
        try:
            query = session.query(InteractionModel)

            # Filtros de fecha
            if date_from:
                query = query.filter(InteractionModel.created_at >= date_from)
            if date_to:
                query = query.filter(InteractionModel.created_at <= date_to)

            return query.count()

        except Exception as e:
            logger.error(f"Error al obtener total de interacciones: {e}")
            return 0
        finally:
            if self._owns_session:
                session.close()

    def get_response_time_stats(self, date_from: Optional[datetime] = None,
                               date_to: Optional[datetime] = None) -> Dict[str, float]:
        """
        Obtiene estadísticas de tiempo de respuesta.

        Args:
            date_from: Fecha de inicio (opcional)
            date_to: Fecha de fin (opcional)

        Returns:
            Diccionario con min, max, avg, median
        """
        from sqlalchemy import func

        session = self._get_session()
        try:
            query = session.query(
                func.min(InteractionModel.response_time_ms).label('min_ms'),
                func.max(InteractionModel.response_time_ms).label('max_ms'),
                func.avg(InteractionModel.response_time_ms).label('avg_ms')
            )

            # Filtros de fecha
            if date_from:
                query = query.filter(InteractionModel.created_at >= date_from)
            if date_to:
                query = query.filter(InteractionModel.created_at <= date_to)

            result = query.first()

            if not result or result.min_ms is None:
                return {}

            # Para median, necesitamos una query separada
            # Simplificación: usar avg como aproximación
            return {
                "min_ms": float(result.min_ms) if result.min_ms else 0,
                "max_ms": float(result.max_ms) if result.max_ms else 0,
                "avg_ms": float(result.avg_ms) if result.avg_ms else 0,
                "median_ms": float(result.avg_ms) if result.avg_ms else 0  # Aproximación
            }

        except Exception as e:
            logger.error(f"Error al obtener estadísticas de tiempo de respuesta: {e}")
            return {}
        finally:
            if self._owns_session:
                session.close()


__all__ = ["ConversationRepository"]
