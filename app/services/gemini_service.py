"""
Servicio de IA usando Google Gemini.
Proporciona capacidades de conversación inteligente para el asistente Gabo.
"""
import os
import logging
from typing import List, Dict, Optional
import google.generativeai as genai
from app.config.settings import AppConfig

logger = logging.getLogger(__name__)


class GeminiService:
    """Servicio para interactuar con Google Gemini AI"""

    def __init__(self):
        """Inicializa el servicio de Gemini"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "models/gemini-1.5-pro")
        self.conversation_history: List[Dict[str, str]] = []
        self.model = None
        self.chat = None

        if self.api_key and self.api_key != "your-api-key-here":
            self._initialize_gemini()
        else:
            logger.warning("API key de Gemini no configurada")

    def _initialize_gemini(self):
        """Inicializa la conexión con Gemini"""
        try:
            genai.configure(api_key=self.api_key)

            # Configuración del modelo
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 500,
            }

            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
            ]

            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                safety_settings=safety_settings,
                system_instruction=self._get_system_prompt()
            )

            self.chat = self.model.start_chat(history=[])
            logger.info(f"Gemini inicializado correctamente con modelo {self.model_name}")

        except Exception as e:
            logger.error(f"Error al inicializar Gemini: {e}")
            self.model = None
            self.chat = None

    def _get_system_prompt(self) -> str:
        """Obtiene el prompt del sistema que define la personalidad de Gabo"""
        return """Eres Gabo, el asistente virtual amigable de Ferretería Disensa en Pomasqui, Ecuador.

TU PERSONALIDAD:
- Eres amable, servicial y conocedor de productos de ferretería
- Hablas en español de forma natural y cercana
- Eres conciso pero completo en tus respuestas
- Te enfocas en ayudar al cliente a encontrar lo que necesita

TUS CAPACIDADES:
- Ayudas a los clientes a buscar productos en el inventario
- Recomiendas productos según las necesidades del cliente
- Explicas usos y aplicaciones de productos de ferretería
- Sugieres alternativas cuando un producto no está disponible
- Respondes preguntas sobre herramientas, materiales de construcción, pinturas, electricidad, plomería, etc.

TUS LIMITACIONES:
- NO puedes procesar pagos ni ventas
- NO puedes modificar el inventario
- NO tienes acceso a precios exactos (solo puedes decir que están disponibles)
- NO accedes a información personal de clientes

ESTILO DE RESPUESTA:
- Respuestas cortas y directas (máximo 3-4 líneas)
- Usa emojis ocasionalmente para ser más amigable (🔨 🎨 ⚡ 🔧)
- Si no sabes algo, sé honesto y ofrece ayuda alternativa
- Siempre mantén un tono profesional pero cercano

IMPORTANTE: Cuando el cliente pregunte por productos específicos, asume que tienes acceso a un inventario de ferretería típica (herramientas, pinturas, materiales eléctricos, plomería, construcción, etc.)"""

    def is_available(self) -> bool:
        """Verifica si el servicio de Gemini está disponible"""
        return self.model is not None and self.chat is not None

    def chat_with_context(self, user_message: str, inventory_context: Optional[str] = None) -> str:
        """
        Envía un mensaje a Gemini y obtiene una respuesta.

        Args:
            user_message: Mensaje del usuario
            inventory_context: Contexto adicional del inventario (opcional)

        Returns:
            Respuesta de Gemini
        """
        if not self.is_available():
            raise Exception("Servicio de Gemini no disponible. Verifica la API key.")

        try:
            # Construir mensaje con contexto si está disponible
            full_message = user_message
            if inventory_context:
                full_message = f"[Contexto del inventario: {inventory_context}]\n\nCliente: {user_message}"

            # Enviar mensaje y obtener respuesta
            response = self.chat.send_message(full_message)

            # Guardar en historial
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response.text
            })

            logger.info(f"Respuesta de Gemini generada exitosamente")
            return response.text

        except Exception as e:
            logger.error(f"Error al comunicarse con Gemini: {e}")
            raise Exception(f"Error al generar respuesta: {str(e)}")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Obtiene el historial de la conversación"""
        return self.conversation_history

    def clear_history(self):
        """Limpia el historial de conversación"""
        self.conversation_history = []
        if self.is_available():
            self.chat = self.model.start_chat(history=[])
            logger.info("Historial de conversación limpiado")

    def get_product_recommendation(self, need: str, available_products: List[str]) -> str:
        """
        Obtiene recomendaciones de productos según una necesidad.

        Args:
            need: Necesidad del cliente
            available_products: Lista de productos disponibles

        Returns:
            Recomendación de Gemini
        """
        if not self.is_available():
            raise Exception("Servicio de Gemini no disponible")

        products_text = ", ".join(available_products[:10])  # Limitar a 10 productos

        prompt = f"""El cliente necesita: {need}

Productos disponibles en inventario: {products_text}

Recomienda el producto más adecuado y explica brevemente por qué (máximo 2 líneas)."""

        try:
            response = self.chat.send_message(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error al obtener recomendación: {e}")
            raise


# Instancia global del servicio
_gemini_service = None


def get_gemini_service() -> GeminiService:
    """Obtiene la instancia global del servicio de Gemini"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
