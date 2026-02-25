"""
Vista del Asistente Virtual - VERSIÓN OPTIMIZADA PARA ACCESIBILIDAD
Diseñada específicamente para usuarios de 50-70 años con visión reducida
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser,
    QLineEdit, QLabel
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QTextCursor, QIcon, QFont
from datetime import datetime
import logging
import re
import time
import string
from functools import wraps
from typing import Optional
from unidecode import unidecode

from app.presentation.components.avatar_widget import AvatarWidget
from app.infrastructure.product_repository import ProductRepository
from app.services.groq_service import GroqService
from app.services.tts_service import TTSService
from app.services.voice_service import VoiceService
from app.services.instruction_formatter import InstructionFormatter
from app.services.conversation_service import ConversationService  # ✅ NUEVO

logger = logging.getLogger(__name__)


# ============================================================================
# DECORADOR PARA LOGGING ESTRUCTURADO
# ============================================================================
def log_operation(operation_name: str):
    """
    Decorador para logging estructurado con métricas de tiempo.
    Registra inicio, fin, duración y errores de operaciones críticas.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.info(f"🔄 [{operation_name}] Iniciando...")

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"✅ [{operation_name}] Completado en {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"❌ [{operation_name}] Error después de {duration:.2f}s: "
                    f"{type(e).__name__}: {str(e)}"
                )
                raise
        return wrapper
    return decorator


# ============================================================================
# WORKER PARA RECONOCIMIENTO DE VOZ
# ============================================================================
class VoiceWorker(QThread):
    """Worker para reconocimiento de voz en hilo separado con manejo robusto de errores"""
    texto_reconocido = pyqtSignal(str)
    error_reconocimiento = pyqtSignal(str, str)  # (mensaje_usuario, tipo_error)
    fin_escucha = pyqtSignal()

    def __init__(self, voice_service):
        super().__init__()
        self.voice_service = voice_service

    @log_operation("Reconocimiento de Voz")
    def run(self):
        try:
            texto = self.voice_service.listen(timeout=5, phrase_time_limit=10)
            if texto:
                self.texto_reconocido.emit(texto)
            else:
                self.error_reconocimiento.emit(
                    "No escuché nada. Por favor, intenta de nuevo.",
                    "NO_SPEECH"
                )
        except TimeoutError:
            self.error_reconocimiento.emit(
                "Tiempo de espera agotado. Presiona el micrófono e intenta de nuevo.",
                "TIMEOUT"
            )
        except ConnectionError:
            self.error_reconocimiento.emit(
                "Sin conexión a internet. Verifica tu red.",
                "CONNECTION"
            )
        except Exception as e:
            logger.error(f"Error inesperado en reconocimiento de voz: {e}")
            self.error_reconocimiento.emit(
                "Hubo un problema con el micrófono. Intenta de nuevo.",
                "UNKNOWN"
            )
        finally:
            self.fin_escucha.emit()


# ============================================================================
# VISTA PRINCIPAL DEL ASISTENTE
# ============================================================================
class AsistenteView(QWidget):
    """
    Vista principal del asistente optimizada para accesibilidad.

    Mejoras clave:
    - Botones grandes (60x60px) para usuarios mayores
    - Fuentes legibles (12-14pt) para visión reducida
    - Respuestas concisas (máx 150 palabras)
    - Manejo específico de errores con mensajes claros
    - Logging estructurado para debugging
    """

    mensaje_enviado = pyqtSignal(str)

    # Constantes de accesibilidad - AJUSTADAS PARA MEJOR BALANCE VISUAL
    BUTTON_SIZE_LARGE = 50  # Botón micrófono (reducido de 60px)
    BUTTON_SIZE_MEDIUM = 80  # Botón enviar (reducido de 100px)
    BUTTON_HEIGHT = 45  # Altura de botones (nuevo)
    FONT_SIZE_NORMAL = 11  # Tamaño base de fuente (reducido de 12pt)
    FONT_SIZE_LARGE = 13  # Tamaño para elementos importantes (reducido de 14pt)
    FONT_SIZE_BUTTON = 13  # Tamaño de fuente en botones (nuevo)
    MAX_RESPONSE_WORDS = 150  # Límite de palabras en respuestas
    MAX_LIST_ITEMS = 3  # Máximo de items en listas

    def __init__(self, parent=None):
        super().__init__(parent)

        # Servicios
        self.producto_repo = ProductRepository()
        self.groq_service = GroqService()
        self.tts_service = TTSService()
        self.voice_service = VoiceService()
        self.conversation_service = ConversationService()  # ✅ NUEVO

        # Estado
        self.voice_worker = None
        self.is_processing = False
        self.is_speaking = False

        # ✅ NUEVO: Tracking para historial
        self.last_detected_intent = None
        self.last_response_source = None

        self.setup_ui()
        self.connect_signals()
        self.mostrar_bienvenida()

        logger.info("✅ AsistenteView inicializado (modo accesibilidad)")

    def setup_ui(self):
        """Configura la interfaz con elementos accesibles"""
        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Panel izquierdo: Avatar
        left_panel = self.create_avatar_panel()
        layout.addWidget(left_panel, stretch=1)

        # Panel derecho: Chat
        right_panel = self.create_chat_panel()
        layout.addWidget(right_panel, stretch=2)

    def create_avatar_panel(self):
        """Crea el panel del avatar con elementos accesibles"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)

        # Título - Fuente grande y legible
        title = QLabel("Gabo")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 36pt; font-weight: 700; color: #2d3748;"
        )
        layout.addWidget(title)

        subtitle = QLabel("Tu asistente virtual")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            f"font-size: {self.FONT_SIZE_LARGE}pt; color: #718096; margin-bottom: 10px;"
        )
        layout.addWidget(subtitle)

        # Avatar
        self.avatar = AvatarWidget()
        layout.addWidget(self.avatar, alignment=Qt.AlignCenter)

        # Información de estado - Fuente legible y contraste alto
        self.info_label = QLabel("¿En qué puedo ayudarte hoy?")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet(
            f"color: #2d3748; font-size: {self.FONT_SIZE_LARGE}pt; "
            f"font-weight: 600; padding: 10px; background-color: #f7f7f5; "
            f"border-radius: 8px;"
        )
        layout.addWidget(self.info_label)

        layout.addStretch()

        # Nota sobre IA - DISCRETO Y PEQUEÑO
        if self.groq_service.is_available():
            note = QLabel("🤖 IA Activa")
            note.setStyleSheet(
                f"color: #4a5568; font-size: 9pt; "
                f"font-weight: 500; padding: 6px 10px; background-color: #e6f4ea; "
                f"border-radius: 6px; border: 1px solid #9fc5a8;"
            )
        else:
            note = QLabel("⚙️ Modo Básico")
            note.setStyleSheet(
                f"color: #4a5568; font-size: 9pt; "
                f"font-weight: 500; padding: 6px 10px; background-color: #fef3e0; "
                f"border-radius: 6px; border: 1px solid #e8c4a0;"
            )
        note.setAlignment(Qt.AlignCenter)
        layout.addWidget(note)

        return panel

    def create_chat_panel(self):
        """Crea el panel de chat con fuentes legibles"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Título
        title = QLabel("Conversación")
        title.setObjectName("sectionTitle")
        title.setStyleSheet(
            f"font-size: 20pt; font-weight: 600; color: #2d3748; margin-bottom: 10px;"
        )
        layout.addWidget(title)

        # Área de chat con fuente legible
        self.chat_display = QTextBrowser()
        self.chat_display.setObjectName("chatDisplay")
        # Establecer fuente base más grande
        font = QFont()
        font.setPointSize(self.FONT_SIZE_NORMAL)
        self.chat_display.setFont(font)
        layout.addWidget(self.chat_display)

        # Área de entrada
        input_layout = self.create_input_area()
        layout.addLayout(input_layout)

        # Sugerencias
        suggestions_layout = self.create_suggestions()
        layout.addLayout(suggestions_layout)

        return panel

    def create_input_area(self):
        """Crea el área de entrada con botones grandes y accesibles"""
        layout = QHBoxLayout()

        # Campo de texto - Fuente más grande
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Escribe tu pregunta aquí...")
        self.message_input.returnPressed.connect(self.enviar_mensaje)
        self.message_input.setMinimumHeight(50)  # Más alto para mejor visibilidad
        font = QFont()
        font.setPointSize(self.FONT_SIZE_LARGE)
        self.message_input.setFont(font)
        layout.addWidget(self.message_input, stretch=4)

        # Botón de voz - TAMAÑO EQUILIBRADO (50x45px)
        self.btn_voz = QPushButton("")
        self.btn_voz.setIcon(QIcon("app/assets/icons/microphone.png"))
        self.btn_voz.setIconSize(QSize(28, 28))  # Icono proporcional
        self.btn_voz.setToolTip("Presiona para hablar con Gabo")
        self.btn_voz.setFixedSize(self.BUTTON_SIZE_LARGE, self.BUTTON_HEIGHT)
        self.btn_voz.setFocusPolicy(Qt.NoFocus)
        self.btn_voz.setAutoDefault(False)
        self.btn_voz.setDefault(False)
        self.btn_voz.setStyleSheet(f"""
            QPushButton {{
                background-color: #cc785c;
                border: none;
                border-radius: 8px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: #b86a4d;
                border: 2px solid #2d3748;
            }}
            QPushButton:pressed {{
                background-color: #a85c42;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                opacity: 0.5;
            }}
        """)

        if self.voice_service.is_available():
            self.btn_voz.clicked.connect(self.iniciar_escucha)
        else:
            self.btn_voz.setEnabled(False)
            self.btn_voz.setToolTip("Micrófono no disponible")

        layout.addWidget(self.btn_voz)

        # Botón enviar/stop - TAMAÑO EQUILIBRADO (80x45px) con fuente legible
        self.btn_enviar = QPushButton("Enviar")
        self.btn_enviar.setObjectName("primaryButton")
        self.btn_enviar.setFixedSize(self.BUTTON_SIZE_MEDIUM, self.BUTTON_HEIGHT)
        font_btn = QFont()
        font_btn.setPointSize(self.FONT_SIZE_BUTTON)  # Fuente más grande para el botón
        font_btn.setBold(True)
        self.btn_enviar.setFont(font_btn)
        self.btn_enviar.clicked.connect(self.toggle_enviar_stop)
        layout.addWidget(self.btn_enviar)

        return layout

    def create_suggestions(self):
        """Crea botones de sugerencias con tamaño accesible"""
        layout = QHBoxLayout()

        label = QLabel("Sugerencias:")
        label.setStyleSheet(
            f"color: #2d3748; font-size: {self.FONT_SIZE_NORMAL}pt; font-weight: 600;"
        )
        layout.addWidget(label)

        suggestions = [
            "¿Qué productos tienes?",
            "Stock bajo",
            "Buscar martillo",
            "Categorías"
        ]

        for suggestion in suggestions:
            btn = QPushButton(suggestion)
            btn.setMinimumHeight(40)  # Más alto para mejor accesibilidad
            font = QFont()
            font.setPointSize(self.FONT_SIZE_NORMAL)
            btn.setFont(font)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f7f7f5;
                    border: 2px solid #d4d4ce;
                    border-radius: 12px;
                    padding: 8px 14px;
                }
                QPushButton:hover {
                    background-color: #e8e8e3;
                    border: 2px solid #2d3748;
                }
            """)
            btn.clicked.connect(lambda checked, s=suggestion: self.usar_sugerencia(s))
            layout.addWidget(btn)

        layout.addStretch()
        return layout

    def connect_signals(self):
        """Conecta todas las señales"""
        logger.info("Conectando señales TTS → Avatar...")
        self.tts_service.speaking_started.connect(self.on_speaking_started)
        self.tts_service.speaking_finished.connect(self.on_speaking_finished)
        logger.info("✅ Señales conectadas correctamente")

    def on_speaking_started(self):
        """Callback cuando empieza a hablar"""
        logger.info("🔊 Avatar → Speaking")
        self.is_speaking = True
        self.cambiar_boton_a_stop()
        self.avatar.start_speaking()
        self.actualizar_estado_visual("Hablando...")

    def on_speaking_finished(self):
        """Callback cuando termina de hablar"""
        logger.info("🔇 Avatar → Idle")
        self.avatar.stop()
        self.is_speaking = False
        self.is_processing = False
        self.cambiar_boton_a_enviar()
        self.actualizar_estado_visual("¿En qué puedo ayudarte hoy?")

    def actualizar_estado_visual(self, mensaje: str):
        """
        Actualiza el indicador visual de estado con mensaje claro.
        Mejora la retroalimentación para usuarios mayores.
        """
        self.info_label.setText(mensaje)

        # Cambiar color según el estado
        if "Escuchando" in mensaje:
            bg_color = "#d4edda"
            text_color = "#2d5016"
        elif "Procesando" in mensaje or "Pensando" in mensaje:
            bg_color = "#fff3cd"
            text_color = "#856404"
        elif "Hablando" in mensaje:
            bg_color = "#cce5ff"
            text_color = "#004085"
        else:
            bg_color = "#f7f7f5"
            text_color = "#2d3748"

        self.info_label.setStyleSheet(
            f"color: {text_color}; font-size: {self.FONT_SIZE_LARGE}pt; "
            f"font-weight: 600; padding: 10px; background-color: {bg_color}; "
            f"border-radius: 8px; border: 2px solid {text_color};"
        )

    def mostrar_bienvenida(self):
        """Muestra mensaje de bienvenida conciso y claro"""
        mensaje = f"""
        <div style='text-align: center; padding: 20px;'>
            <p style='font-size: {self.FONT_SIZE_LARGE + 2}pt; color: #2d3748;'>
                👋 <b>¡Hola! Soy Gabo</b>
            </p>
            <p style='font-size: {self.FONT_SIZE_NORMAL}pt; color: #6b6b65;'>
                Tu asistente de Ferretería Disensa.<br>
                Pregúntame sobre productos, stock o categorías.
            </p>
        </div>
        """
        self.chat_display.append(mensaje)

    def agregar_mensaje_usuario(self, texto: str):
        """Agrega mensaje del usuario con fuente legible"""
        timestamp = datetime.now().strftime("%H:%M")
        html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
            <tr>
                <td align="right">
                    <table border="0" cellpadding="14" cellspacing="0" bgcolor="#cc785c"
                           style="border-radius: 15px; margin: 5px;">
                        <tr>
                            <td>
                                <font color="#ffffff" size="4" face="Arial, sans-serif">
                                    <b>{texto}</b>
                                </font><br>
                                <div align="right">
                                    <font color="#e0e0e0" size="3">{timestamp}</font>
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        <br>
        """
        self.chat_display.append(html)
        self.chat_display.moveCursor(QTextCursor.End)

    def agregar_mensaje_asistente(self, texto: str):
        """Agrega mensaje del asistente con fuente legible y contraste alto"""
        timestamp = datetime.now().strftime("%H:%M")
        html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
            <tr>
                <td align="left">
                    <table border="0" cellpadding="14" cellspacing="0" bgcolor="#ffffff"
                           style="border-radius: 15px; border: 2px solid #2d3748; margin: 5px;">
                        <tr>
                            <td>
                                <font color="#2b2825" size="4" face="Arial, sans-serif">
                                    {texto}
                                </font><br>
                                <font color="#6b6b65" size="3">{timestamp}</font>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        <br>
        """
        self.chat_display.append(html)
        self.chat_display.moveCursor(QTextCursor.End)

    def usar_sugerencia(self, sugerencia: str):
        """Usa una sugerencia"""
        self.message_input.setText(sugerencia)
        self.enviar_mensaje()

    def toggle_enviar_stop(self):
        """Alterna entre enviar mensaje y detener procesamiento"""
        if self.is_processing or self.is_speaking:
            self.detener_procesamiento()
        else:
            self.enviar_mensaje()

    def cambiar_boton_a_stop(self):
        """Cambia el botón a modo Stop con estilo elegante"""
        self.btn_enviar.setText("Detener")  # Sin mayúsculas sostenidas
        self.btn_enviar.setIcon(QIcon("app/assets/icons/stop.png"))
        self.btn_enviar.setIconSize(QSize(18, 18))  # Icono más pequeño

        if not hasattr(self, 'original_btn_style'):
            self.original_btn_style = self.btn_enviar.styleSheet()

        # Estilo más suave y profesional
        self.btn_enviar.setStyleSheet(f"""
            QPushButton {{
                background-color: #e85d4a;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: {self.FONT_SIZE_BUTTON}pt;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: #d14836;
                border: 2px solid #2d3748;
            }}
        """)

    def cambiar_boton_a_enviar(self):
        """Cambia el botón a modo Enviar"""
        self.btn_enviar.setText("Enviar")
        self.btn_enviar.setIcon(QIcon())
        style = getattr(self, 'original_btn_style', "")
        self.btn_enviar.setStyleSheet(style)
        self.btn_enviar.setObjectName("primaryButton")

    @log_operation("Detener Procesamiento")
    def detener_procesamiento(self):
        """Detiene el procesamiento actual y la reproducción de audio"""
        # 1. Detener TTS inmediatamente
        if hasattr(self, 'tts_service'):
            try:
                self.tts_service.stop()
            except Exception as e:
                logger.error(f"Error al detener TTS: {e}")

        # 2. Actualizar estados internos
        self.is_processing = False
        self.is_speaking = False

        # 3. Volver avatar a idle
        if hasattr(self, 'avatar'):
            self.avatar.stop()

        # 4. Cambiar botón a enviar
        self.cambiar_boton_a_enviar()

        # 5. Actualizar estado visual
        self.actualizar_estado_visual("Detenido. ¿En qué puedo ayudarte?")

    @log_operation("Enviar Mensaje")
    def enviar_mensaje(self):
        """Envía un mensaje con validación y feedback mejorado"""
        mensaje = self.message_input.text().strip()
        if not mensaje:
            return

        # Limpiar input
        self.message_input.clear()

        # Mostrar mensaje del usuario
        self.agregar_mensaje_usuario(mensaje)

        # Marcar como procesando
        self.is_processing = True
        self.cambiar_boton_a_stop()
        self.actualizar_estado_visual("Procesando tu pregunta...")
        self.avatar.start_thinking()

        # ✅ NUEVO: Iniciar timer para medir tiempo de respuesta
        start_time = time.time()

        # Procesar y obtener respuesta
        respuesta = self.procesar_mensaje(mensaje)

        # Verificar si fue detenido
        if not self.is_processing:
            logger.info("⏹️ Procesamiento cancelado por el usuario")
            return

        # ✅ NUEVO: Calcular tiempo de respuesta
        response_time_ms = int((time.time() - start_time) * 1000)

        # Limpiar y limitar respuesta
        respuesta_final = self.preparar_respuesta(respuesta)

        # Mostrar respuesta
        self.agregar_mensaje_asistente(respuesta_final)

        # ✅ NUEVO: Guardar en historial (NO BLOQUEANTE - si falla, el chat continúa)
        try:
            self.conversation_service.save_interaction(
                question=mensaje,
                answer=respuesta_final,
                intent=self.last_detected_intent or "unknown",
                response_source=self.last_response_source or "unknown",
                response_time_ms=response_time_ms,
                confidence=None
            )
            logger.info(f"💾 Interacción guardada en historial (tiempo: {response_time_ms}ms)")
        except Exception as e:
            logger.error(f"❌ Error al guardar historial: {e}")
            # NO ROMPER el flujo si falla el guardado

        # Hablar respuesta
        self.tts_service.speak(respuesta_final)

        # Emitir señal
        self.mensaje_enviado.emit(mensaje)

    def preparar_respuesta(self, respuesta: str) -> str:
        """
        Prepara la respuesta para mostrar en la GUI.
        NUEVO: Solo trunca respuestas no-instructivas para preservar formato.

        Mejoras:
        - Elimina emojis
        - Detecta instrucciones estructuradas
        - Preserva formato completo de instrucciones
        - Limita longitud solo en respuestas generales
        """
        # Eliminar emojis y caracteres especiales (PRESERVAR /)
        respuesta_limpia = re.sub(
            r'[^a-zA-Z0-9\s.,!?¡¿áéíóúÁÉÍÓÚñÑüÜ:;()\-/]',
            '',
            respuesta
        )
        respuesta_limpia = re.sub(r'\s+', ' ', respuesta_limpia).strip()

        # ✅ NUEVO: Detectar si es instrucción (tiene formato estructurado)
        es_instruccion = (
            "Herramientas/materiales necesarios:" in respuesta_limpia or
            "Materiales necesarios:" in respuesta_limpia or
            "Precaución:" in respuesta_limpia or
            any(f"{i}." in respuesta_limpia for i in range(1, 10))
        )

        # ✅ NUEVO: Solo truncar si NO es instrucción
        if not es_instruccion:
            palabras = respuesta_limpia.split()
            if len(palabras) > self.MAX_RESPONSE_WORDS:
                # ✅ MEJORADO: Truncar en punto final, no en medio de frase
                texto_limitado = ' '.join(palabras[:self.MAX_RESPONSE_WORDS])
                ultimo_punto = texto_limitado.rfind('.')

                # Si hay punto en el último 70% del texto, cortar ahí
                if ultimo_punto > len(texto_limitado) * 0.7:
                    respuesta_limpia = texto_limitado[:ultimo_punto + 1]
                else:
                    respuesta_limpia = texto_limitado + "..."

                logger.info(f"⚠️ Respuesta truncada a {self.MAX_RESPONSE_WORDS} palabras")
        else:
            logger.info(f"✅ Instrucción detectada, NO se trunca")

        return respuesta_limpia if respuesta_limpia else respuesta

    def extraer_entidad_producto(self, texto: str) -> Optional[str]:
        """
        Extrae entidad de producto del texto del usuario.

        Estrategia:
        1. Normaliza texto (minúsculas, sin acentos, sin puntuación)
        2. Obtiene lista blanca dinámica de productos en BD
        3. Busca coincidencia exacta o fuzzy (threshold 85%)
        4. Maneja plurales comunes

        Args:
            texto: Pregunta del usuario

        Returns:
            Entidad limpia (ej: "martillo") o None si no se identifica

        Ejemplos:
            "cuantos martillos tienes?" → "martillo"
            "CLAVOS!!!" → "clavo"
            "necesito palas para jardín" → "pala"
            "enumera materiales" → None (no es producto específico)
        """
        import re

        # 1. Normalización agresiva
        texto_limpio = unidecode(texto.lower())
        texto_limpio = re.sub(r'[^\w\s]', '', texto_limpio)  # Quitar puntuación
        texto_limpio = texto_limpio.strip()

        # 2. Obtener lista blanca dinámica de productos
        try:
            productos_bd = self.producto_repo.get_all_product_names()
            productos_bd_lower = [unidecode(p.lower()) for p in productos_bd]
        except Exception as e:
            logger.error(f"Error al obtener lista de productos: {e}")
            return None

        # 3. Diccionario de plurales conocidos (extendido)
        plurales = {
            'martillos': 'martillo', 'clavos': 'clavo', 'tornillos': 'tornillo',
            'taladros': 'taladro', 'serruchos': 'serrucho', 'palas': 'pala',
            'picos': 'pico', 'llaves': 'llave', 'destornilladores': 'destornillador',
            'alicates': 'alicate', 'pinzas': 'pinza', 'cables': 'cable',
            'tubos': 'tubo', 'codos': 'codo', 'grifos': 'grifo',
            'baldosas': 'baldosa', 'ladrillos': 'ladrillo', 'bloques': 'bloque',
            'pinturas': 'pintura', 'brochas': 'brocha', 'rodillos': 'rodillo',
            'lijas': 'lija', 'adhesivos': 'adhesivo', 'siliconas': 'silicona'
        }

        # 4. Buscar coincidencia exacta en cada palabra del texto
        palabras = texto_limpio.split()
        for palabra in palabras:
            # Intentar con palabra original
            if palabra in productos_bd_lower:
                idx = productos_bd_lower.index(palabra)
                logger.info(f"✅ Entidad exacta encontrada: '{palabra}' → '{productos_bd[idx]}'")
                return productos_bd[idx].lower()

            # Intentar con singular si está en diccionario
            if palabra in plurales:
                singular = plurales[palabra]
                if singular in productos_bd_lower:
                    idx = productos_bd_lower.index(singular)
                    logger.info(f"✅ Plural normalizado: '{palabra}' → '{productos_bd[idx]}'")
                    return productos_bd[idx].lower()

            # Regla simple: quitar 's' final si tiene más de 3 letras
            if palabra.endswith('s') and len(palabra) > 3:
                singular_simple = palabra[:-1]
                if singular_simple in productos_bd_lower:
                    idx = productos_bd_lower.index(singular_simple)
                    logger.info(f"✅ Plural detectado: '{palabra}' → '{productos_bd[idx]}'")
                    return productos_bd[idx].lower()

        # 5. Fuzzy matching como fallback
        try:
            from rapidfuzz import fuzz, process

            # Buscar mejor match en toda la frase
            mejor_match = process.extractOne(
                texto_limpio,
                productos_bd_lower,
                scorer=fuzz.partial_ratio
            )

            if mejor_match and mejor_match[1] >= 85:  # Threshold 85%
                idx = productos_bd_lower.index(mejor_match[0])
                logger.info(f"✅ Fuzzy match: '{texto_limpio}' → '{productos_bd[idx]}' (confianza: {mejor_match[1]}%)")
                return productos_bd[idx].lower()
            else:
                logger.info(f"❌ No se encontró entidad clara en: '{texto_limpio}'")
                return None

        except ImportError:
            logger.warning("rapidfuzz no disponible, saltando fuzzy matching")
            return None
        except Exception as e:
            logger.error(f"Error en fuzzy matching: {e}")
            return None

    def detectar_intencion(self, mensaje: str) -> str:
        """
        Detecta la intención del usuario para decidir cómo procesar.

        Returns:
            'product_search': Búsqueda de producto específico
            'product_info': Info de stock/precio
            'instruction': Instrucciones de instalación/reparación
            'general': Pregunta general
            'offtopic': Fuera de tema
        """
        mensaje_lower = mensaje.lower()

        # 1. BÚSQUEDA DE PRODUCTO
        palabras_producto = ['tienen', 'hay', 'buscar', 'busco', 'venden', 'encuentro']
        if any(palabra in mensaje_lower for palabra in palabras_producto):
            logger.info("🔍 Intención detectada: BÚSQUEDA DE PRODUCTO")
            self.last_detected_intent = 'product_search'  # ✅ NUEVO
            return 'product_search'

        # 2. INFO DE STOCK/PRECIO
        palabras_info = ['stock', 'precio', 'cuanto cuesta', 'cuánto cuesta', 'disponible', 'cuantos', 'cuántos']
        if any(palabra in mensaje_lower for palabra in palabras_info):
            logger.info("🔍 Intención detectada: INFO DE PRODUCTO")
            self.last_detected_intent = 'product_info'  # ✅ NUEVO
            return 'product_info'

        # 3. INSTRUCCIONES
        palabras_instruccion = ['como', 'cómo', 'instalar', 'reparar', 'pasos', 'instrucciones', 'instruccion', 'pegar', 'colocar', 'montar']
        if any(palabra in mensaje_lower for palabra in palabras_instruccion):
            logger.info("🔍 Intención detectada: INSTRUCCIÓN")
            self.last_detected_intent = 'instruction'  # ✅ NUEVO
            return 'instruction'

        # 4. FUERA DE TEMA
        palabras_offtopic = ['quien es', 'quién es', 'elon musk', 'sam altman', 'que hora', 'qué hora', 'internet']
        if any(palabra in mensaje_lower for palabra in palabras_offtopic):
            logger.info("🔍 Intención detectada: FUERA DE TEMA")
            self.last_detected_intent = 'offtopic'  # ✅ NUEVO
            return 'offtopic'

        # 5. GENERAL (por defecto)
        logger.info("🔍 Intención detectada: GENERAL")
        intencion = 'general'

        # ✅ NUEVO: Guardar intención para historial
        self.last_detected_intent = intencion
        return intencion

    def normalizar_termino(self, termino: str) -> str:
        """
        Normaliza un término de búsqueda para mejorar coincidencias.

        Aplica:
        - Eliminación de puntuación
        - Eliminación de acentos
        - Conversión a minúsculas
        - Normalización de plurales comunes

        Ejemplos:
            "martillos?" → "martillo"
            "clavos!" → "clavo"
            "cemento" → "cemento"
        """
        # 1. Quitar puntuación
        termino = termino.translate(str.maketrans('', '', string.punctuation))

        # 2. Quitar acentos
        termino = unidecode(termino)

        # 3. Convertir a minúsculas y limpiar espacios
        termino = termino.lower().strip()

        # 4. Normalizar plurales comunes (regla simple)
        # Diccionario de plurales conocidos
        plurales_conocidos = {
            'martillos': 'martillo',
            'clavos': 'clavo',
            'tornillos': 'tornillo',
            'taladros': 'taladro',
            'destornilladores': 'destornillador',
            'alicates': 'alicate',
            'llaves': 'llave',
            'tuercas': 'tuerca',
            'pernos': 'perno',
            'brocas': 'broca',
            'sierras': 'sierra',
            'cinceles': 'cincel',
            'limas': 'lima',
            'escuadras': 'escuadra',
            'niveles': 'nivel',
            'metros': 'metro',
            'cables': 'cable',
            'enchufes': 'enchufe',
            'interruptores': 'interruptor',
            'focos': 'foco',
            'tubos': 'tubo',
            'codos': 'codo',
            'llaves': 'llave',
            'grifos': 'grifo',
            'baldosas': 'baldosa',
            'azulejos': 'azulejo',
            'ladrillos': 'ladrillo',
            'bloques': 'bloque',
            'pinturas': 'pintura',
            'brochas': 'brocha',
            'rodillos': 'rodillo',
            'lijas': 'lija',
            'adhesivos': 'adhesivo',
            'selladores': 'sellador',
            'siliconas': 'silicona',
        }

        # Buscar en diccionario primero
        if termino in plurales_conocidos:
            termino_normalizado = plurales_conocidos[termino]
            logger.info(f"📝 Plural normalizado: '{termino}' → '{termino_normalizado}'")
            return termino_normalizado

        # Regla simple: si termina en 's' y tiene más de 3 letras, intentar singular
        if termino.endswith('s') and len(termino) > 3:
            termino_singular = termino[:-1]
            # Verificar si el singular existe en DB
            try:
                productos = self.producto_repo.search(termino_singular, solo_activos=True)
                if productos:
                    logger.info(f"📝 Plural detectado: '{termino}' → '{termino_singular}'")
                    return termino_singular
            except Exception as e:
                logger.warning(f"Error al verificar singular: {e}")

        return termino

    def extraer_termino_busqueda(self, mensaje: str) -> str:
        """
        Extrae el término de búsqueda del mensaje.

        Ejemplos:
            "tienen martillo?" → "martillo"
            "busco cemento gris" → "cemento gris"
            "hay clavos de 2 pulgadas?" → "clavo 2 pulgadas"
        """
        mensaje_lower = mensaje.lower()

        # Palabras a ignorar
        palabras_ignorar = [
            'tienen', 'hay', 'buscar', 'busco', 'venden', 'necesito',
            'quiero', 'encuentro', '?', '¿', 'de', 'el', 'la', 'los', 'las'
        ]

        # Dividir en palabras
        palabras = mensaje_lower.split()

        # Filtrar palabras ignoradas
        termino_palabras = [p for p in palabras if p not in palabras_ignorar]

        # Unir y limpiar
        termino = ' '.join(termino_palabras).strip()

        logger.info(f"📝 Término extraído: '{termino}' de '{mensaje}'")

        # ✅ NUEVO: Normalizar término (plurales, puntuación, acentos)
        termino_normalizado = self.normalizar_termino(termino)

        if termino != termino_normalizado:
            logger.info(f"✅ Término normalizado: '{termino}' → '{termino_normalizado}'")

        return termino_normalizado

    def _calculate_confidence(self, query: str, product_name: str) -> float:
        """
        Calcula confianza de match fuzzy con penalización por términos excluyentes.

        Args:
            query: Término de búsqueda
            product_name: Nombre del producto encontrado

        Returns:
            Score de confianza (0.0-1.0)
        """
        from difflib import SequenceMatcher

        query_lower = query.lower()
        product_lower = product_name.lower()

        # Similitud de caracteres
        char_similarity = SequenceMatcher(None, query_lower, product_lower).ratio()

        # Coincidencia de palabras clave
        query_words = set(query_lower.split())
        product_words = set(product_lower.split())
        word_overlap = len(query_words & product_words) / max(len(query_words), 1)

        # ✅ NUEVO: Diccionario de términos excluyentes
        exclusiones = {
            'mate': ['látex', 'latex', 'satinado', 'brillante', 'esmalte'],
            'látex': ['mate', 'esmalte', 'óleo', 'oleo', 'acrílico', 'acrilico'],
            'latex': ['mate', 'esmalte', 'óleo', 'oleo', 'acrílico', 'acrilico'],
            'carretilla': ['cerradura', 'candado', 'llave', 'chapa'],
            'cerradura': ['carretilla', 'carreta', 'carro'],
        }

        # Penalizar si hay términos excluyentes
        exclusion_penalty = 0.0
        for query_word in query_words:
            if query_word in exclusiones:
                excluded_terms = exclusiones[query_word]
                if any(term in product_lower for term in excluded_terms):
                    exclusion_penalty = 0.5  # Penalización fuerte
                    logger.info(f"⚠️ Término excluyente detectado: '{query_word}' vs '{product_name}'")
                    break

        # Score combinado
        confidence = (char_similarity * 0.6) + (word_overlap * 0.4) - exclusion_penalty
        confidence = max(0.0, min(1.0, confidence))  # Limitar a [0, 1]

        logger.info(f"📊 Confianza: {confidence:.2f} (char:{char_similarity:.2f}, word:{word_overlap:.2f}, penalty:{exclusion_penalty:.2f})")

        return confidence

    def _pluralizar_unidad(self, cantidad: int, unidad: str) -> str:
        """Pluraliza unidad de medida según cantidad"""
        if cantidad == 1:
            return unidad

        # Reglas de pluralización en español
        plurales = {
            'unidad': 'unidades',
            'galón': 'galones',
            'galon': 'galones',
            'metro': 'metros',
            'kilogramo': 'kilogramos',
            'litro': 'litros',
            'pieza': 'piezas',
            'caja': 'cajas',
            'paquete': 'paquetes',
            'rollo': 'rollos',
            'saco': 'sacos',
            'bolsa': 'bolsas',
        }

        return plurales.get(unidad.lower(), unidad + 's')

    @log_operation("Procesar Mensaje")
    def procesar_mensaje(self, mensaje: str) -> str:
        """Procesa el mensaje con manejo robusto de errores"""
        try:
            if self.groq_service.is_available():
                return self.procesar_con_groq(mensaje)
            else:
                return self.procesar_modo_basico(mensaje)
        except ConnectionError:
            return "No hay conexión a internet. Verifica tu red e intenta de nuevo."
        except TimeoutError:
            return "La consulta tardó demasiado. Por favor, intenta de nuevo."
        except Exception as e:
            logger.error(f"Error inesperado al procesar mensaje: {e}")
            return "Hubo un problema. Por favor, intenta de nuevo o reformula tu pregunta."

    @log_operation("Procesar con Groq")
    def procesar_con_groq(self, mensaje: str) -> str:
        """
        Procesa con sistema híbrido inteligente: DB + Groq según intención.

        Flujo:
        1. Detecta intención del usuario
        2. Para productos: consulta DB primero
        3. Para instrucciones: usa Groq con SYSTEM_PROMPT
        4. Para fuera de tema: respuesta breve y redirige
        """
        try:
            # ✅ PASO 1: Detectar intención
            intencion = self.detectar_intencion(mensaje)

            # ✅ PASO 2: Procesar según intención

            # CASO A: BÚSQUEDA DE PRODUCTO
            if intencion == 'product_search':
                termino = self.extraer_termino_busqueda(mensaje)

                if not termino:
                    return "No entendí qué producto buscas. ¿Puedes ser más específico?"

                # ✅ OPTIMIZADO: Usar método search() del repositorio
                productos_encontrados = self.producto_repo.search(termino, solo_activos=True)

                # ✅ MEJORADO: Si no encuentra, intentar búsqueda fuzzy con validación de confianza
                if not productos_encontrados:
                    logger.info(f"🔍 Búsqueda exacta no encontró resultados, intentando fuzzy...")
                    productos_fuzzy = self.producto_repo.search_fuzzy(termino, threshold=0.75, solo_activos=True)

                    if productos_fuzzy:
                        # Validar confianza del mejor match
                        best_match = productos_fuzzy[0]
                        confidence = self._calculate_confidence(termino, best_match.nombre)

                        if confidence >= 0.80:
                            # Alta confianza - usar resultado
                            productos_encontrados = productos_fuzzy
                            logger.info(f"✅ Fuzzy encontró match con confianza {confidence:.2f}")
                        else:
                            # Baja confianza - NO usar
                            logger.info(f"⚠️ Fuzzy encontró '{best_match.nombre}' pero confianza baja ({confidence:.2f})")
                            productos_encontrados = []

                if productos_encontrados:
                    # Construir contexto de inventario
                    productos_info = []
                    for p in productos_encontrados[:3]:  # Máximo 3
                        productos_info.append(
                            f"{p.nombre} (Stock: {p.stock} {p.unidad_medida}, Precio: ${p.precio})"
                        )

                    inventory_context = f"Productos encontrados en inventario: {', '.join(productos_info)}"
                    logger.info(f"📦 Contexto: {inventory_context}")

                    # Pasar contexto a Groq para respuesta enriquecida
                    respuesta = self.groq_service.chat_with_context(
                        mensaje,
                        inventory_context=inventory_context
                    )
                    self.last_response_source = "groq+database"  # ✅ NUEVO
                else:
                    # No existe en inventario
                    respuesta = f"No encontré '{termino}' en nuestro inventario actual. ¿Puedo ayudarte con algo más?"
                    self.last_response_source = "database"  # ✅ NUEVO

            # CASO B: INFO DE STOCK/PRECIO
            elif intencion == 'product_info':
                # ✅ CRÍTICO: Extraer entidad ANTES de buscar en BD
                entidad = self.extraer_entidad_producto(mensaje)

                if entidad:
                    # Buscar en BD con término limpio
                    productos = self.producto_repo.search(entidad, solo_activos=True)

                    if productos:
                        # Construir contexto estructurado
                        p = productos[0]  # Tomar primer resultado
                        inventory_context = (
                            f"Producto encontrado: {p.nombre} "
                            f"(Stock: {p.stock} {p.unidad_medida}, Precio: ${p.precio})"
                        )
                        logger.info(f"📦 Contexto: {inventory_context}")

                        # Pasar a Groq con contexto real
                        respuesta = self.groq_service.chat_with_context(
                            mensaje,
                            inventory_context=inventory_context
                        )
                        self.last_response_source = "groq+database"
                    else:
                        # Entidad válida pero no en stock
                        respuesta = f"No tenemos {entidad} en stock actualmente. Consulta en tienda para disponibilidad."
                        self.last_response_source = "database"
                else:
                    # No se pudo extraer entidad clara
                    # Casos: "enumera materiales", "qué productos tienes"
                    if any(palabra in mensaje.lower() for palabra in ['enumera', 'lista', 'materiales', 'productos', 'categorias', 'categorías']):
                        respuesta = (
                            "Tenemos estas categorías: herramientas manuales, ferretería básica, "
                            "electricidad, fontanería. ¿Necesitas detalles de alguna?"
                        )
                    else:
                        respuesta = "No entendí qué producto necesitas. ¿Puedes especificar?"
                    self.last_response_source = "groq"

            # CASO C: INSTRUCCIONES
            elif intencion == 'instruction':
                # ✅ NUEVO: Usar InstructionFormatter para formato garantizado
                logger.info("📋 Usando InstructionFormatter para formato consistente")

                # Opción 1: Intentar usar base de conocimientos
                respuesta_formatter = InstructionFormatter.format_response(mensaje)

                # Si hay respuesta de la base de conocimientos, usarla
                if respuesta_formatter and respuesta_formatter != "¿En qué puedo ayudarte hoy?":
                    logger.info("✅ Usando respuesta de base de conocimientos")
                    respuesta = respuesta_formatter
                    self.last_response_source = "knowledge_base"  # ✅ NUEVO
                else:
                    # Opción 2: Usar Groq y forzar corrección de formato
                    logger.info("🤖 Usando Groq + corrección de formato")
                    groq_response = self.groq_service.chat_with_context(mensaje)
                    # Forzar corrección de formato
                    respuesta = InstructionFormatter.force_correction(groq_response)
                    self.last_response_source = "groq"  # ✅ NUEVO

            # CASO D: FUERA DE TEMA
            elif intencion == 'offtopic':
                # Groq con límite de tokens bajo
                respuesta = self.groq_service.chat_with_context(mensaje)
                # Truncar si es muy largo
                if len(respuesta) > 300:
                    respuesta = respuesta[:250] + "... ¿En qué más puedo ayudarte con ferretería?"
                self.last_response_source = "groq"  # ✅ NUEVO

            # CASO E: GENERAL
            else:
                # Groq normal
                respuesta = self.groq_service.chat_with_context(mensaje)
                self.last_response_source = "groq"  # ✅ NUEVO

            return respuesta

        except ConnectionError:
            logger.warning("Error de conexión con Groq, usando modo básico")
            return self.procesar_modo_basico(mensaje)
        except Exception as e:
            logger.error(f"Error en procesar_con_groq: {e}")
            return self.procesar_modo_basico(mensaje)

    def procesar_modo_basico(self, mensaje: str) -> str:
        """
        Modo básico sin IA con respuestas concisas.
        Limita resultados a MAX_LIST_ITEMS para evitar abrumar al usuario.
        """
        mensaje_lower = mensaje.lower()

        try:
            if "stock bajo" in mensaje_lower:
                productos = self.producto_repo.get_stock_bajo()
                if not productos:
                    return "No hay productos con stock bajo."

                # Limitar a MAX_LIST_ITEMS
                productos_limitados = productos[:self.MAX_LIST_ITEMS]
                total_bajo_stock = len(productos)

                # ✅ CORREGIDO: Pluralización correcta
                respuesta = f"Hay {total_bajo_stock} productos con stock bajo:<br><br>"
                for p in productos_limitados:
                    unidad_plural = self._pluralizar_unidad(p.stock, p.unidad_medida)
                    respuesta += f"• {p.nombre}: {p.stock} {unidad_plural}<br>"

                if total_bajo_stock > self.MAX_LIST_ITEMS:
                    respuesta += f"<br>(Y {total_bajo_stock - self.MAX_LIST_ITEMS} más...)"

                return respuesta

            elif "categoría" in mensaje_lower or "categorias" in mensaje_lower:
                from app.infrastructure.product_repository import CategoriaRepository
                cat_repo = CategoriaRepository()
                categorias = cat_repo.get_all()[:self.MAX_LIST_ITEMS]

                respuesta = f"Tenemos estas categorías:<br><br>"
                for cat in categorias:
                    respuesta += f"• {cat.nombre}<br>"

                total = len(cat_repo.get_all())
                if total > self.MAX_LIST_ITEMS:
                    respuesta += f"<br>(Y {total - self.MAX_LIST_ITEMS} más...)"

                return respuesta

            elif any(palabra in mensaje_lower for palabra in ["qué productos", "productos tienes", "total"]):
                # ✅ MEJORADO: Consultar BD en lugar de respuesta genérica
                total = self.producto_repo.count_active_products()
                return f"Tenemos {total} productos activos en inventario. ¿Buscas algo específico?"

            else:
                # Búsqueda general - Limitar resultados
                productos = self.producto_repo.search(mensaje)
                if not productos:
                    return f"No encontré productos con '{mensaje}'. Intenta con otro término."

                productos = productos[:self.MAX_LIST_ITEMS]
                respuesta = f"Encontré {len(productos)} producto(s):<br><br>"
                for p in productos:
                    respuesta += f"• {p.nombre} - ${p.precio}<br>"

                total = len(self.producto_repo.search(mensaje))
                if total > self.MAX_LIST_ITEMS:
                    respuesta += f"<br>(Y {total - self.MAX_LIST_ITEMS} más...)"

                return respuesta

        except Exception as e:
            logger.error(f"Error en modo básico: {e}")
            return "Hubo un problema al buscar. Por favor, intenta de nuevo."

    @log_operation("Iniciar Escucha")
    def iniciar_escucha(self, checked=False):
        """Inicia escucha de voz con feedback visual mejorado"""
        # Detener cualquier audio en curso
        self.detener_procesamiento()

        self.btn_voz.setEnabled(False)
        self.actualizar_estado_visual("Escuchando... Habla ahora")
        self.avatar.start_listening()

        self.voice_worker = VoiceWorker(self.voice_service)
        self.voice_worker.texto_reconocido.connect(self.procesar_voz)
        self.voice_worker.error_reconocimiento.connect(self.error_voz)
        self.voice_worker.fin_escucha.connect(self.fin_escucha)
        self.voice_worker.start()

    def procesar_voz(self, texto: str):
        """Procesa texto reconocido"""
        logger.info(f"✅ Voz reconocida: {texto}")
        self.message_input.setText(texto)
        self.enviar_mensaje()

    def error_voz(self, mensaje_usuario: str, tipo_error: str):
        """
        Maneja errores de voz con mensajes específicos y claros.

        Args:
            mensaje_usuario: Mensaje amigable para mostrar al usuario
            tipo_error: Tipo de error para logging (NO_SPEECH, TIMEOUT, CONNECTION, UNKNOWN)
        """
        logger.warning(f"Error de voz ({tipo_error}): {mensaje_usuario}")
        self.actualizar_estado_visual(mensaje_usuario)

        # Mostrar mensaje en el chat para mayor claridad
        self.agregar_mensaje_asistente(f"⚠️ {mensaje_usuario}")

    def fin_escucha(self):
        """Finaliza escucha"""
        self.btn_voz.setEnabled(True)
        self.actualizar_estado_visual("¿En qué puedo ayudarte hoy?")
        self.avatar.stop()

    def limpiar_historial(self):
        """Limpia el historial de chat"""
        self.chat_display.clear()
        self.groq_service.clear_history()
        self.mostrar_bienvenida()
        logger.info("🗑️ Historial limpiado")
