"""
Servicio de IA usando Groq - VERSIÓN CORREGIDA
Usa SYSTEM_PROMPT de settings.py y control de longitud adaptativo
"""
import logging
import re
from typing import List, Dict, Optional
from groq import Groq
from app.config.settings import GroqConfig

logger = logging.getLogger(__name__)


class GroqService:
    """Servicio Groq con prompt correcto y control de longitud"""

    def __init__(self):
        self.api_key = GroqConfig.API_KEY
        self.model_name = GroqConfig.MODEL
        self.max_tokens = GroqConfig.MAX_TOKENS
        self.temperature = GroqConfig.TEMPERATURE
        self.top_p = GroqConfig.TOP_P

        self.conversation_history: List[Dict[str, str]] = []
        self.client = None

        if self.api_key and self.api_key != "your-api-key-here":
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info(f"✅ Groq inicializado - Modelo: {self.model_name}")
            except Exception as e:
                logger.error(f"❌ Error al inicializar Groq: {e}")
                self.client = None
        else:
            logger.warning("⚠️ API key de Groq no configurada")

    def is_available(self) -> bool:
        return self.client is not None

    def _detect_question_type(self, user_message: str) -> str:
        """Detecta tipo de pregunta para ajustar max_tokens"""
        user_lower = user_message.lower()

        # Productos específicos
        if any(word in user_lower for word in ['tienen', 'buscar', 'stock', 'precio', 'disponible']):
            return 'product'

        # Instrucciones
        if any(word in user_lower for word in ['como', 'instalar', 'reparar', 'pasos', 'instrucciones', 'pegar', 'instruccion', 'instruccione']):
            return 'instruction'

        # Fuera de tema
        if any(word in user_lower for word in ['quien es', 'elon musk', 'sam altman', 'que hora', 'internet', 'inventó']):
            return 'offtopic'

        return 'general'

    def _clean_response(self, response: str, question_type: str) -> str:
        """Limpia y formatea respuesta"""

        # 1. Corregir palabras pegadas comunes
        response = response.replace('Herramientasmateriales', 'Herramientas/materiales')
        response = response.replace('Herramientas materiales', 'Herramientas/materiales')
        response = response.replace('Materialesnecesarios', 'Materiales necesarios')

        # 2. Para instrucciones, delegar a InstructionFormatter
        if question_type == 'instruction':
            # ✅ NUEVO: Usar InstructionFormatter en lugar de regex frágil
            from app.services.instruction_formatter import InstructionFormatter
            logger.info("📋 Delegando formato de instrucciones a InstructionFormatter")
            response = InstructionFormatter.force_correction(response)

        # 3. Truncar si es demasiado largo
        if question_type == 'product' and len(response) > 200:
            response = response[:197] + "..."
            logger.warning(f"⚠️ Respuesta de producto truncada ({len(response)} chars)")
        elif question_type == 'offtopic' and len(response) > 300:
            # Agregar redirección
            response = response[:250] + "... ¿En qué más puedo ayudarte con ferretería?"
            logger.warning(f"⚠️ Respuesta fuera de tema truncada y redirigida")

        return response

    def chat_with_context(self, user_message: str, inventory_context: Optional[str] = None) -> str:
        """Procesa mensajes usando SYSTEM_PROMPT correcto"""
        if not self.is_available():
            return "Lo siento, el servicio de IA no está disponible en este momento."

        logger.info(f"📤 Pregunta: {user_message}")

        # Detectar tipo de pregunta
        question_type = self._detect_question_type(user_message)
        logger.info(f"🔍 Tipo detectado: {question_type}")

        # Ajustar max_tokens según tipo
        max_tokens_map = {
            'product': 50,      # ~20 palabras, 1-2 oraciones
            'instruction': 300, # ~100 palabras, 4-5 pasos
            'offtopic': 100,    # ✅ AUMENTADO: ~40 palabras, 3-4 oraciones (era 50)
            'general': 100      # ~40 palabras, 2-3 oraciones
        }
        max_tokens = max_tokens_map.get(question_type, 150)
        logger.info(f"🎯 Max tokens: {max_tokens}")

        try:
            # ✅ USAR SYSTEM_PROMPT DE SETTINGS.PY
            messages = [
                {"role": "system", "content": GroqConfig.SYSTEM_PROMPT}
            ]

            # Agregar historial (últimos 5 mensajes)
            for msg in self.conversation_history[-5:]:
                messages.append(msg)

            # Agregar contexto de inventario si existe
            if inventory_context:
                user_message_with_context = f"[Contexto: {inventory_context}]\n\n{user_message}"
            else:
                user_message_with_context = user_message

            # Agregar mensaje actual
            messages.append({"role": "user", "content": user_message_with_context})

            # Llamar a Groq
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens,  # ✅ ADAPTATIVO
                top_p=self.top_p
            )

            raw_response = response.choices[0].message.content
            logger.info(f"📥 Respuesta cruda ({len(raw_response)} chars): {raw_response[:100]}...")

            # ✅ POST-PROCESAMIENTO OBLIGATORIO
            final_response = self._clean_response(raw_response, question_type)
            logger.info(f"✅ Respuesta limpia ({len(final_response)} chars)")

            # Guardar en historial
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": final_response})

            return final_response

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return "Lo siento, hubo un error. Por favor, intenta de nuevo."

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Obtiene el historial de la conversación"""
        return self.conversation_history

    def clear_history(self):
        """Limpia historial de conversación"""
        self.conversation_history = []
        logger.info("🗑️ Historial limpiado")

    def get_product_recommendation(self, need: str, available_products: List[str]) -> str:
        """
        Obtiene recomendaciones de productos según una necesidad.

        Args:
            need: Necesidad del cliente
            available_products: Lista de productos disponibles

        Returns:
            Recomendación de Groq
        """
        if not self.is_available():
            raise Exception("Servicio de Groq no disponible")

        products_text = ", ".join(available_products[:10])  # Limitar a 10 productos

        prompt = f"""El cliente necesita: {need}

Productos disponibles en inventario: {products_text}

Recomienda el producto más adecuado y explica brevemente por qué (máximo 2 líneas)."""

        try:
            messages = [
                {"role": "system", "content": GroqConfig.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=200  # Respuestas cortas para recomendaciones
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"❌ Error al obtener recomendación: {e}")
            raise


# Instancia global
_groq_service = None


def get_groq_service() -> GroqService:
    """Obtiene la instancia global del servicio de Groq"""
    global _groq_service
    if _groq_service is None:
        _groq_service = GroqService()
    return _groq_service