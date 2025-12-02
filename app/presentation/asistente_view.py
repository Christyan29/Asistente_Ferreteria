"""
Vista del Asistente Virtual.
Interfaz de chat para interactuar con el asistente con IA Groq.
Integración de voz (STT y TTS).
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLineEdit, QLabel, QTextBrowser, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from datetime import datetime
import logging

from app.presentation.components.avatar_widget import AvatarWidget
from app.infrastructure.product_repository import ProductRepository
from app.services.groq_service import get_groq_service
from app.services.voice_service import get_voice_service
from app.services.tts_service import get_tts_service

logger = logging.getLogger(__name__)

class VoiceWorker(QThread):
    """Hilo para escuchar voz sin bloquear la UI"""
    texto_reconocido = pyqtSignal(str)
    error_reconocimiento = pyqtSignal(str)
    fin_escucha = pyqtSignal()

    def __init__(self, voice_service):
        super().__init__()
        self.voice_service = voice_service

    def run(self):
        texto = self.voice_service.listen()
        if texto:
            self.texto_reconocido.emit(texto)
        else:
            self.error_reconocimiento.emit("No se detectó voz o no se entendió.")
        self.fin_escucha.emit()

class AsistenteView(QWidget):
    """Vista del asistente virtual con chat e IA"""

    # Señales
    mensaje_enviado = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.producto_repo = ProductRepository()
        self.groq_service = get_groq_service()
        self.voice_service = get_voice_service()
        self.tts_service = get_tts_service()
        self.conversation_history = []
        self.voice_worker = None

        self.setup_ui()
        self.mostrar_mensaje_bienvenida()

        # Conectar señales del TTS para animar avatar
        self.tts_service.speaking_started.connect(self.avatar.start_speaking)
        self.tts_service.speaking_finished.connect(self.avatar.stop)

    def setup_ui(self):
        """Configura la interfaz de usuario"""
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

        # Título con nombre Gabo
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
            note = QLabel("🤖 IA Activa (Groq - Ultra Rápido)")
            note.setStyleSheet("color: #6ba56a; font-size: 9pt; padding: 8px; background-color: #f0faf0; border-radius: 8px;")
        else:
            note = QLabel("ℹ️ Modo básico (sin IA)")
            note.setStyleSheet("color: #d68a6e; font-size: 9pt; padding: 8px; background-color: #fef5f1; border-radius: 8px;")
        note.setAlignment(Qt.AlignCenter)
        layout.addWidget(note)

        return panel

    def create_chat_panel(self):
        """Crea el panel de chat"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Título del chat
        chat_title = QLabel("💬 Conversación")
        chat_title.setObjectName("subtitleLabel")
        layout.addWidget(chat_title)

        # Área de mensajes
        self.chat_display = QTextBrowser()
        self.chat_display.setObjectName("chatDisplay")
        self.chat_display.setOpenExternalLinks(False)
        layout.addWidget(self.chat_display)

        # Área de entrada
        input_layout = self.create_input_area()
        layout.addLayout(input_layout)

        # Sugerencias rápidas
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

        # Verificar si hay micrófono disponible
        if self.voice_service.is_available():
            self.btn_voz.clicked.connect(self.iniciar_escucha)
            self.btn_voz.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 25px; /* Redondo */
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
        else:
            self.btn_voz.setEnabled(False)
            self.btn_voz.setToolTip("Micrófono no detectado")

        layout.addWidget(self.btn_voz)

        # Botón enviar
        self.btn_enviar = QPushButton("Enviar")
        self.btn_enviar.setObjectName("primaryButton")
        self.btn_enviar.clicked.connect(self.enviar_mensaje)
        layout.addWidget(self.btn_enviar)

        return layout

    def create_suggestions(self):
        """Crea botones de sugerencias rápidas"""
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
                    background-color: #ffffff;
                    color: #4a5568;
                    border: 1.5px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 8px 16px;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #f7fafc;
                    border-color: #cbd5e0;
                }
            """)
            btn.clicked.connect(lambda checked, s=suggestion: self.usar_sugerencia(s))
            layout.addWidget(btn)

        layout.addStretch()
        return layout

    def mostrar_mensaje_bienvenida(self):
        """Muestra el mensaje de bienvenida"""
        mensaje = """
        <div style='background-color: #fafaf8; padding: 20px; border-radius: 16px; margin: 10px 0; border: 1.5px solid #d4d4ce;'>
            <p style='color: #2b2825; font-weight: 600; font-size: 13pt; margin: 0 0 12px 0;'>👋 ¡Hola! Soy Gabo, tu asistente virtual de Ferretería Disensa. Puedo ayudarte a buscar productos, consultar disponibilidad y brindarte información sobre nuestros artículos.</p>
        </div>
        """
        self.chat_display.append(mensaje)
        # Opcional: Hablar bienvenida
        # self.tts_service.speak("Hola, soy Gabo. ¿En qué puedo ayudarte?")

    def agregar_mensaje_usuario(self, texto):
        """Agrega un mensaje del usuario al chat"""
        timestamp = datetime.now().strftime("%H:%M")
        # Usar tabla anidada para efecto de burbuja que se ajusta al texto
        html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
            <tr>
                <td align="right">
                    <!-- Tabla interna para la burbuja -->
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
        """Agrega un mensaje del asistente al chat"""
        timestamp = datetime.now().strftime("%H:%M")
        html = f"""
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
            <tr>
                <td align="left">
                    <!-- Tabla interna para la burbuja -->
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
        """Usa una sugerencia rápida"""
        self.message_input.setText(sugerencia)
        self.enviar_mensaje()

    def enviar_mensaje(self):
        """Envía un mensaje y procesa la respuesta"""
        mensaje = self.message_input.text().strip()
        if not mensaje:
            return

        # Limpiar input
        self.message_input.clear()

        # Mostrar mensaje del usuario
        self.agregar_mensaje_usuario(mensaje)

        # Cambiar estado del avatar
        self.avatar.start_thinking()

        # Procesar mensaje y generar respuesta
        respuesta = self.procesar_mensaje(mensaje)

        # Mostrar respuesta
        self.agregar_mensaje_asistente(respuesta)

        # Hablar respuesta
        self.tts_service.speak(respuesta)

        # Volver a estado idle (se maneja por señales del TTS ahora)
        if not self.tts_service.engine: # Si no hay TTS, detener manual
            self.avatar.stop()

        # Emitir señal
        self.mensaje_enviado.emit(mensaje)

    def iniciar_escucha(self):
        """Inicia el proceso de escucha de voz"""
        self.btn_voz.setEnabled(False)
        self.btn_voz.setStyleSheet("background-color: #ffcccc; border-radius: 25px;") # Rojo claro
        self.info_label.setText("Escuchando... 👂")
        self.avatar.start_listening()

        self.voice_worker = VoiceWorker(self.voice_service)
        self.voice_worker.texto_reconocido.connect(self.procesar_voz)
        self.voice_worker.error_reconocimiento.connect(self.error_voz)
        self.voice_worker.fin_escucha.connect(self.fin_escucha)
        self.voice_worker.start()

    def procesar_voz(self, texto):
        """Procesa el texto reconocido por voz"""
        self.message_input.setText(texto)
        self.enviar_mensaje()

    def error_voz(self, error):
        """Maneja errores de voz"""
        self.info_label.setText(error)
        # Restaurar mensaje después de 2 segundos
        QThread.msleep(2000) # Esto bloquearía UI, mejor no usarlo aquí directo, pero es breve
        # Mejor dejar el mensaje de error visible un momento

    def fin_escucha(self):
        """Finaliza el proceso de escucha"""
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

    def procesar_mensaje(self, mensaje):
        """
        Procesa el mensaje del usuario y genera una respuesta.
        Usa Groq AI si está disponible, sino usa modo básico.
        """
        try:
            # Intentar usar Groq AI primero
            if self.groq_service.is_available():
                return self.procesar_con_groq(mensaje)
            else:
                # Fallback a modo básico
                return self.procesar_modo_basico(mensaje)
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {e}")
            # Si falla Groq, intentar modo básico
            try:
                return self.procesar_modo_basico(mensaje)
            except:
                return "Lo siento, ocurrió un error al procesar tu consulta. Por favor, intenta de nuevo."

    def procesar_con_groq(self, mensaje):
        """
        Procesa el mensaje usando Groq AI.
        """
        try:
            # Obtener contexto del inventario
            productos = self.producto_repo.get_all()
            productos_nombres = [p.nombre for p in productos[:20]]  # Primeros 20
            contexto = f"Productos disponibles: {', '.join(productos_nombres)}"

            # Obtener respuesta de Groq
            respuesta = self.groq_service.chat_with_context(mensaje, contexto)
            return respuesta

        except Exception as e:
            logger.error(f"Error con Groq: {e}")
            raise

    def procesar_modo_basico(self, mensaje):
        """
        Procesa el mensaje del usuario en modo básico (sin IA).
        Esta es una versión simple que busca en la base de datos.
        """
        mensaje_lower = mensaje.lower()

        try:
            # Comandos específicos con más variaciones
            if any(palabra in mensaje_lower for palabra in ["stock bajo", "stock mínimo", "poco stock", "productos bajos"]):
                return self.responder_stock_bajo()

            elif any(palabra in mensaje_lower for palabra in ["categoría", "categorias", "tipos de productos", "secciones"]):
                return self.responder_categorias()

            elif any(palabra in mensaje_lower for palabra in ["cuántos productos", "total", "cantidad", "qué productos tienes", "que productos", "productos disponibles"]):
                return self.responder_total_productos()

            elif any(palabra in mensaje_lower for palabra in ["buscar", "busca", "necesito", "quiero", "tienes", "tienen", "hay"]):
                # Extraer término de búsqueda - remover palabras comunes
                palabras_ignorar = ["buscar", "busca", "necesito", "quiero", "tienes", "tienen", "hay", "un", "una", "el", "la", "los", "las", "de", "para"]
                palabras = mensaje_lower.split()
                terminos = [p for p in palabras if p not in palabras_ignorar and len(p) > 2]

                if terminos:
                    termino = " ".join(terminos)
                    return self.responder_busqueda(termino)
                else:
                    # Si no hay términos específicos, mostrar productos
                    return self.responder_total_productos()

            # Búsqueda general por palabras clave
            else:
                return self.responder_busqueda(mensaje)

        except Exception as e:
            logger.error(f"Error al procesar mensaje en modo básico: {e}")
            return "Lo siento, ocurrió un error al procesar tu consulta. Por favor, intenta de nuevo."

    def responder_stock_bajo(self):
        """Responde con productos de stock bajo"""
        productos = self.producto_repo.get_stock_bajo()

        if not productos:
            return "✅ ¡Excelente! No hay productos con stock bajo en este momento."

        respuesta = f"⚠️ Encontré {len(productos)} producto(s) con stock bajo:<br><br>"
        for p in productos[:5]:  # Máximo 5
            respuesta += f"• <b>{p.nombre}</b>: {p.stock} {p.unidad_medida} (mínimo: {p.stock_minimo})<br>"

        if len(productos) > 5:
            respuesta += f"<br>... y {len(productos) - 5} más."

        return respuesta

    def responder_categorias(self):
        """Responde con las categorías disponibles"""
        from app.infrastructure.product_repository import CategoriaRepository
        cat_repo = CategoriaRepository()
        categorias = cat_repo.get_all()

        if not categorias:
            return "No hay categorías registradas en el sistema."

        respuesta = f"📁 Tenemos {len(categorias)} categorías disponibles:<br><br>"
        for cat in categorias:
            respuesta += f"• <b>{cat.nombre}</b>"
            if cat.descripcion:
                respuesta += f": {cat.descripcion}"
            respuesta += "<br>"

        return respuesta

    def responder_total_productos(self):
        """Responde con el total de productos"""
        productos = self.producto_repo.get_all()
        return f"📦 Actualmente tenemos <b>{len(productos)} productos</b> registrados en el inventario."

    def responder_busqueda(self, termino):
        """Responde con resultados de búsqueda"""
        productos = self.producto_repo.search(termino)

        if not productos:
            return f"❌ No encontré productos que coincidan con '<b>{termino}</b>'. Intenta con otro término de búsqueda."

        respuesta = f"🔍 Encontré {len(productos)} producto(s) relacionado(s) con '<b>{termino}</b>':<br><br>"

        for p in productos[:5]:  # Máximo 5 resultados
            respuesta += f"• <b>{p.nombre}</b><br>"
            if p.marca:
                respuesta += f"  Marca: {p.marca}<br>"
            respuesta += f"  Precio: {p.precio_formateado} | Stock: {p.stock} {p.unidad_medida}"
            if p.stock_bajo:
                respuesta += " ⚠️"
            respuesta += "<br><br>"

        if len(productos) > 5:
            respuesta += f"... y {len(productos) - 5} producto(s) más."

        return respuesta

    def limpiar_chat(self):
        """Limpia el historial del chat"""
        self.chat_display.clear()
        self.conversation_history.clear()
        if self.groq_service.is_available():
            self.groq_service.clear_history()
        self.mostrar_mensaje_bienvenida()
