"""
Vista del Asistente Virtual - VERSIÓN CORREGIDA
Incluye integración completa de voz y avatar
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser,
    QLineEdit, QLabel, QPushButton
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor
from datetime import datetime
import logging

from app.presentation.components.avatar_widget import AvatarWidget
from app.infrastructure.product_repository import ProductRepository
from app.services.groq_service import GroqService
from app.services.tts_service import TTSService
from app.services.voice_service import VoiceService

logger = logging.getLogger(__name__)


class VoiceWorker(QThread):
    """Worker para reconocimiento de voz en hilo separado"""
    texto_reconocido = pyqtSignal(str)
    error_reconocimiento = pyqtSignal(str)
    fin_escucha = pyqtSignal()

    def __init__(self, voice_service):
        super().__init__()
        self.voice_service = voice_service

    def run(self):
        try:
            texto = self.voice_service.listen(timeout=5, phrase_time_limit=10)
            if texto:
                self.texto_reconocido.emit(texto)
            else:
                self.error_reconocimiento.emit("No se detectó voz o no se entendió")
        except Exception as e:
            self.error_reconocimiento.emit(f"Error: {str(e)}")
        finally:
            self.fin_escucha.emit()


class AsistenteView(QWidget):
    """Vista principal del asistente con voz y avatar"""

    mensaje_enviado = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Servicios
        self.producto_repo = ProductRepository()
        self.groq_service = GroqService()
        self.tts_service = TTSService()
        self.voice_service = VoiceService()

        # Estado
        self.voice_worker = None

        self.setup_ui()
        self.connect_signals()

        # Mensaje de bienvenida
        self.mostrar_bienvenida()

        logger.info("AsistenteView inicializado correctamente")

    def setup_ui(self):
        """Configura la interfaz"""
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
        """Crea el panel del avatar"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)

        # Título
        title = QLabel("Gabo")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32pt; font-weight: 700; color: #2d3748;")
        layout.addWidget(title)

        subtitle = QLabel("Tu asistente virtual")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 12pt; color: #718096; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        # Avatar
        self.avatar = AvatarWidget()
        layout.addWidget(self.avatar, alignment=Qt.AlignCenter)

        # Información
        self.info_label = QLabel("¿En qué puedo ayudarte hoy?")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #6b6b65; font-size: 11pt;")
        layout.addWidget(self.info_label)

        layout.addStretch()

        # Nota sobre IA
        if self.groq_service.is_available():
            note = QLabel("🤖 IA Activa (Groq)")
            note.setStyleSheet("color: #6ba56a; font-size: 9pt; padding: 8px; background-color: #f0faf0; border-radius: 8px;")
        else:
            note = QLabel("ℹ️ Modo básico")
            note.setStyleSheet("color: #d68a6e; font-size: 9pt; padding: 8px; background-color: #fef5f1; border-radius: 8px;")
        note.setAlignment(Qt.AlignCenter)
        layout.addWidget(note)

        return panel

    def create_chat_panel(self):
        """Crea el panel de chat"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Título
        title = QLabel("Conversación")
        title.setObjectName("sectionTitle")
        title.setStyleSheet("font-size: 18pt; font-weight: 600; color: #2d3748; margin-bottom: 10px;")
        layout.addWidget(title)

        # Área de chat
        self.chat_display = QTextBrowser()
        self.chat_display.setObjectName("chatDisplay")
        layout.addWidget(self.chat_display)

        # Área de entrada
        input_layout = self.create_input_area()
        layout.addLayout(input_layout)

        # Sugerencias
        suggestions_layout = self.create_suggestions()
        layout.addLayout(suggestions_layout)

        return panel

    def create_input_area(self):
        """Crea el área de entrada de mensajes"""
        layout = QHBoxLayout()

        # Campo de texto
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Escribe tu pregunta aquí...")
        self.message_input.returnPressed.connect(self.enviar_mensaje)
        layout.addWidget(self.message_input, stretch=4)

        # Botón de voz
        self.btn_voz = QPushButton("🎤")
        self.btn_voz.setToolTip("Hablar con Gabo")
        self.btn_voz.setMaximumWidth(50)
        self.btn_voz.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 25px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)

        if self.voice_service.is_available():
            self.btn_voz.clicked.connect(self.iniciar_escucha)
        else:
            self.btn_voz.setEnabled(False)
            self.btn_voz.setToolTip("Micrófono no disponible")

        layout.addWidget(self.btn_voz)

        # Botón enviar
        self.btn_enviar = QPushButton("Enviar")
        self.btn_enviar.setObjectName("primaryButton")
        self.btn_enviar.clicked.connect(self.enviar_mensaje)
        layout.addWidget(self.btn_enviar)

        return layout

    def create_suggestions(self):
        """Crea botones de sugerencias"""
        layout = QHBoxLayout()

        label = QLabel("Sugerencias:")
        label.setStyleSheet("color: #718096; font-size: 10pt; font-weight: 600;")
        layout.addWidget(label)

        suggestions = [
            "¿Qué productos tienes?",
            "Productos con stock bajo",
            "Buscar martillo",
            "Categorías disponibles"
        ]

        for suggestion in suggestions:
            btn = QPushButton(suggestion)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f7f7f5;
                    border: 1px solid #d4d4ce;
                    border-radius: 12px;
                    padding: 6px 12px;
                    font-size: 9pt;
                }
                QPushButton:hover {
                    background-color: #e8e8e3;
                }
            """)
            btn.clicked.connect(lambda checked, s=suggestion: self.usar_sugerencia(s))
            layout.addWidget(btn)

        layout.addStretch()
        return layout

    def connect_signals(self):
        """Conecta todas las señales"""
        logger.info("Conectando señales TTS → Avatar...")

        # CRÍTICO: Conectar señales del TTS al avatar
        self.tts_service.speaking_started.connect(self.on_speaking_started)
        self.tts_service.speaking_finished.connect(self.on_speaking_finished)

        logger.info("✅ Señales conectadas correctamente")

    def on_speaking_started(self):
        """Callback cuando empieza a hablar"""
        logger.info("🔊 Avatar → Speaking")
        self.avatar.start_speaking()

    def on_speaking_finished(self):
        """Callback cuando termina de hablar"""
        logger.info("🔇 Avatar → Idle")
        self.avatar.stop()

    def mostrar_bienvenida(self):
        """Muestra mensaje de bienvenida"""
        mensaje = """
        <div style='text-align: center; padding: 20px;'>
            <p style='font-size: 14pt; color: #2d3748;'>
                👋 <b>¡Hola! Soy Gabo, tu asistente virtual de Ferretería Disensa.</b>
            </p>
            <p style='color: #6b6b65;'>
                Puedo ayudarte a buscar productos, consultar disponibilidad y brindarte información sobre nuestros artículos.
            </p>
        </div>
        """
        self.chat_display.append(mensaje)

    def agregar_mensaje_usuario(self, texto):
        """Agrega mensaje del usuario"""
        timestamp = datetime.now().strftime("%H:%M")
        html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
            <tr>
                <td align="right">
                    <table border="0" cellpadding="12" cellspacing="0" bgcolor="#cc785c" style="border-radius: 15px; margin: 5px;">
                        <tr>
                            <td>
                                <font color="#ffffff" size="4">{texto}</font><br>
                                <div align="right"><font color="#e0e0e0" size="2">{timestamp}</font></div>
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

    def agregar_mensaje_asistente(self, texto):
        """Agrega mensaje del asistente"""
        timestamp = datetime.now().strftime("%H:%M")
        html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
            <tr>
                <td align="left">
                    <table border="0" cellpadding="12" cellspacing="0" bgcolor="#fafaf8" style="border-radius: 15px; border: 1px solid #d4d4ce; margin: 5px;">
                        <tr>
                            <td>
                                <font color="#2b2825" size="4">{texto}</font><br>
                                <font color="#6b6b65" size="2">{timestamp}</font>
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

    def usar_sugerencia(self, sugerencia):
        """Usa una sugerencia"""
        self.message_input.setText(sugerencia)
        self.enviar_mensaje()

    def enviar_mensaje(self):
        """Envía un mensaje"""
        mensaje = self.message_input.text().strip()
        if not mensaje:
            return

        logger.info(f"📤 Enviando mensaje: {mensaje}")

        # Limpiar input
        self.message_input.clear()

        # Mostrar mensaje del usuario
        self.agregar_mensaje_usuario(mensaje)

        # Cambiar avatar a "thinking"
        logger.info("🤔 Avatar → Thinking")
        self.avatar.start_thinking()

        # Procesar y obtener respuesta
        respuesta = self.procesar_mensaje(mensaje)

        # Mostrar respuesta
        self.agregar_mensaje_asistente(respuesta)

        # Hablar respuesta
        logger.info(f"🗣️ Llamando a TTS.speak()")
        self.tts_service.speak(respuesta)

        # Emitir señal
        self.mensaje_enviado.emit(mensaje)

    def procesar_mensaje(self, mensaje):
        """Procesa el mensaje y genera respuesta"""
        try:
            if self.groq_service.is_available():
                return self.procesar_con_groq(mensaje)
            else:
                return self.procesar_modo_basico(mensaje)
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {e}")
            return "Lo siento, ocurrió un error al procesar tu mensaje."

    def procesar_con_groq(self, mensaje):
        """Procesa con IA de Groq"""
        try:
            respuesta = self.groq_service.chat_with_context(mensaje)
            return respuesta
        except Exception as e:
            logger.error(f"Error con Groq: {e}")
            return self.procesar_modo_basico(mensaje)

    def procesar_modo_basico(self, mensaje):
        """Modo básico sin IA"""
        mensaje_lower = mensaje.lower()

        try:
            if "stock bajo" in mensaje_lower:
                productos = self.producto_repo.get_stock_bajo()
                if not productos:
                    return "✅ No hay productos con stock bajo."

                respuesta = f"⚠️ Hay {len(productos)} productos con stock bajo:<br><br>"
                for p in productos[:5]:
                    respuesta += f"• <b>{p.nombre}</b>: {p.stock} {p.unidad_medida}<br>"
                return respuesta

            elif "categoría" in mensaje_lower or "categorias" in mensaje_lower:
                from app.infrastructure.product_repository import CategoriaRepository
                cat_repo = CategoriaRepository()
                categorias = cat_repo.get_all()

                respuesta = f"📁 Tenemos {len(categorias)} categorías:<br><br>"
                for cat in categorias:
                    respuesta += f"• {cat.nombre}<br>"
                return respuesta

            elif any(palabra in mensaje_lower for palabra in ["qué productos", "productos tienes", "total"]):
                productos = self.producto_repo.get_all()
                return f"📦 Tenemos {len(productos)} productos en total en nuestro inventario."

            else:
                # Búsqueda general
                productos = self.producto_repo.search(mensaje)
                if not productos:
                    return f"Lo siento, no encontré productos relacionados con '{mensaje}'."

                respuesta = f"Encontré {len(productos)} producto(s):<br><br>"
                for p in productos[:5]:
                    respuesta += f"• <b>{p.nombre}</b> - ${p.precio}<br>"
                return respuesta

        except Exception as e:
            logger.error(f"Error en modo básico: {e}")
            return "Lo siento, ocurrió un error al buscar."

    def iniciar_escucha(self):
        """Inicia escucha de voz"""
        logger.info("🎤 Iniciando escucha de voz...")

        self.btn_voz.setEnabled(False)
        self.btn_voz.setStyleSheet("background-color: #ffcccc; border-radius: 25px;")
        self.info_label.setText("Escuchando... 👂")
        self.avatar.start_listening()

        self.voice_worker = VoiceWorker(self.voice_service)
        self.voice_worker.texto_reconocido.connect(self.procesar_voz)
        self.voice_worker.error_reconocimiento.connect(self.error_voz)
        self.voice_worker.fin_escucha.connect(self.fin_escucha)
        self.voice_worker.start()

    def procesar_voz(self, texto):
        """Procesa texto reconocido"""
        logger.info(f"✅ Voz reconocida: {texto}")
        self.message_input.setText(texto)
        self.enviar_mensaje()

    def error_voz(self, error):
        """Maneja error de voz"""
        logger.warning(f"⚠️ Error de voz: {error}")
        self.info_label.setText(error)

    def fin_escucha(self):
        """Finaliza escucha"""
        self.btn_voz.setEnabled(True)
        self.btn_voz.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 25px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.info_label.setText("¿En qué puedo ayudarte hoy?")
        self.avatar.stop()

    def limpiar_historial(self):
        """Limpia el historial de chat"""
        self.chat_display.clear()
        self.groq_service.clear_history()
        self.mostrar_bienvenida()
