"""
Servicio de Analíticas para el Sistema de Historial.
Proporciona estadísticas básicas sobre conversaciones e interacciones.
"""
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta

from app.infrastructure.conversation_repository import ConversationRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Servicio para generar estadísticas y analíticas del historial"""

    def __init__(self):
        self.repository = ConversationRepository()

    def get_top_products(self, limit: int = 10, date_from: Optional[datetime] = None,
                        date_to: Optional[datetime] = None) -> List[Tuple[str, int]]:
        """
        Obtiene los productos más consultados.

        Args:
            limit: Número máximo de productos a retornar
            date_from: Fecha de inicio (opcional)
            date_to: Fecha de fin (opcional)

        Returns:
            Lista de tuplas (producto, cantidad_consultas)
        """
        try:
            results = self.repository.get_top_products_from_interactions(
                limit=limit,
                date_from=date_from,
                date_to=date_to
            )
            return results if results else []
        except Exception as e:
            logger.error(f"Error al obtener top productos: {e}")
            return []

    def get_intent_distribution(self, date_from: Optional[datetime] = None,
                                date_to: Optional[datetime] = None) -> Dict[str, Dict[str, int]]:
        """
        Obtiene la distribución de tipos de intenciones.

        Args:
            date_from: Fecha de inicio (opcional)
            date_to: Fecha de fin (opcional)

        Returns:
            Diccionario con {tipo_intencion: {"count": N, "percentage": X}}
        """
        try:
            counts = self.repository.get_intent_counts(date_from=date_from, date_to=date_to)

            if not counts:
                return {}

            # Calcular total
            total = sum(count for _, count in counts)

            if total == 0:
                return {}

            # Calcular porcentajes
            distribution = {}
            for intent_type, count in counts:
                percentage = round((count / total) * 100, 1)
                distribution[intent_type] = {
                    "count": count,
                    "percentage": percentage
                }

            return distribution

        except Exception as e:
            logger.error(f"Error al obtener distribución de intenciones: {e}")
            return {}

    def get_daily_stats(self, date_from: Optional[datetime] = None,
                       date_to: Optional[datetime] = None) -> Dict[str, any]:
        """
        Obtiene estadísticas diarias generales.

        Args:
            date_from: Fecha de inicio (opcional)
            date_to: Fecha de fin (opcional)

        Returns:
            Diccionario con estadísticas generales
        """
        try:
            # Obtener total de conversaciones
            total_conversations = self.repository.get_total_conversations_count(
                date_from=date_from,
                date_to=date_to
            )

            # Obtener total de interacciones
            total_interactions = self.repository.get_total_interactions_count(
                date_from=date_from,
                date_to=date_to
            )

            # Calcular promedio por día
            if date_from and date_to:
                days_diff = (date_to - date_from).days + 1
            else:
                # Usar últimos 7 días por defecto
                days_diff = 7

            avg_conversations_per_day = round(total_conversations / days_diff, 1) if days_diff > 0 else 0
            avg_interactions_per_day = round(total_interactions / days_diff, 1) if days_diff > 0 else 0

            return {
                "total_conversations": total_conversations,
                "total_interactions": total_interactions,
                "avg_conversations_per_day": avg_conversations_per_day,
                "avg_interactions_per_day": avg_interactions_per_day,
                "days_analyzed": days_diff
            }

        except Exception as e:
            logger.error(f"Error al obtener estadísticas diarias: {e}")
            return {
                "total_conversations": 0,
                "total_interactions": 0,
                "avg_conversations_per_day": 0,
                "avg_interactions_per_day": 0,
                "days_analyzed": 0
            }

    def get_response_time_stats(self, date_from: Optional[datetime] = None,
                                date_to: Optional[datetime] = None) -> Dict[str, float]:
        """
        Obtiene estadísticas de tiempo de respuesta.

        Args:
            date_from: Fecha de inicio (opcional)
            date_to: Fecha de fin (opcional)

        Returns:
            Diccionario con estadísticas de tiempo de respuesta
        """
        try:
            stats = self.repository.get_response_time_stats(
                date_from=date_from,
                date_to=date_to
            )

            if not stats:
                return {
                    "min_ms": 0,
                    "max_ms": 0,
                    "avg_ms": 0,
                    "median_ms": 0
                }

            # Convertir a segundos para mejor legibilidad
            return {
                "min_ms": stats.get("min_ms", 0),
                "max_ms": stats.get("max_ms", 0),
                "avg_ms": stats.get("avg_ms", 0),
                "median_ms": stats.get("median_ms", 0),
                "min_s": round(stats.get("min_ms", 0) / 1000, 2),
                "max_s": round(stats.get("max_ms", 0) / 1000, 2),
                "avg_s": round(stats.get("avg_ms", 0) / 1000, 2),
                "median_s": round(stats.get("median_ms", 0) / 1000, 2)
            }

        except Exception as e:
            logger.error(f"Error al obtener estadísticas de tiempo de respuesta: {e}")
            return {
                "min_ms": 0,
                "max_ms": 0,
                "avg_ms": 0,
                "median_ms": 0,
                "min_s": 0,
                "max_s": 0,
                "avg_s": 0,
                "median_s": 0
            }

    def get_complete_summary(self, date_from: Optional[datetime] = None,
                            date_to: Optional[datetime] = None) -> Dict[str, any]:
        """
        Obtiene un resumen completo de todas las estadísticas.

        Args:
            date_from: Fecha de inicio (opcional)
            date_to: Fecha de fin (opcional)

        Returns:
            Diccionario con todas las estadísticas
        """
        try:
            return {
                "daily_stats": self.get_daily_stats(date_from, date_to),
                "top_products": self.get_top_products(limit=10, date_from=date_from, date_to=date_to),
                "intent_distribution": self.get_intent_distribution(date_from, date_to),
                "response_time_stats": self.get_response_time_stats(date_from, date_to)
            }
        except Exception as e:
            logger.error(f"Error al obtener resumen completo: {e}")
            return {
                "daily_stats": {},
                "top_products": [],
                "intent_distribution": {},
                "response_time_stats": {}
            }


__all__ = ["AnalyticsService"]
