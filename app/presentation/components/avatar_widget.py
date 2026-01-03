"""
Widget del Avatar para el asistente virtual.
Muestra una representación visual del asistente con diferentes estados.
"""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from pathlib import Path


class AvatarWidget(QWidget):
    """
    Widget que muestra el avatar del asistente con diferentes estados visuales.
    Estados: idle, listening, thinking, speaking
    """

    # Señales
    state_changed = pyqtSignal(str)  # Emite cuando cambia el estado

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_state = "idle"
        self.animation_frame = 0
        self.setup_ui()
        self.setup_animation()

    def setup_ui(self):
        """Configura la interfaz del widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Avatar visual (círculo con inicial o imagen)
        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("avatarWidget")
        self.avatar_label.setFixedSize(200, 200)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setScaledContents(False)

        # Estado del avatar
        self.state_label = QLabel("Listo para ayudarte")
        self.state_label.setAlignment(Qt.AlignCenter)
        self.state_label.setStyleSheet("font-size: 11pt; color: #6b6b65;")

        layout.addWidget(self.avatar_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.state_label, alignment=Qt.AlignCenter)

        # Cargar imagen del avatar si existe, sino crear uno por defecto
        self.load_avatar_image()

    def load_avatar_image(self):
        """Carga la imagen del avatar o crea uno por defecto"""
        avatar_path = Path("app/assets/avatar/default.png")

        if avatar_path.exists():
            pixmap = QPixmap(str(avatar_path))
            scaled_pixmap = pixmap.scaled(
                180, 180,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.avatar_label.setPixmap(scaled_pixmap)
        else:
            # Crear avatar por defecto (círculo con letra)
            self.create_default_avatar()

    def create_default_avatar(self):
        """Crea un avatar por defecto con el nombre 'Gabo'"""
        pixmap = QPixmap(180, 180)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dibujar círculo de fondo según el estado
        color = self.get_state_color()
        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 180, 180)

        # Dibujar letra "G" de Gabo
        painter.setPen(QColor("#ffffff"))
        font = QFont("Segoe UI", 72, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "G")

        painter.end()
        self.avatar_label.setPixmap(pixmap)

    def get_state_color(self):
        """Retorna el color según el estado actual"""
        colors = {
            "idle": "#cc785c",      # Naranja
            "listening": "#6ba56a",  # Verde
            "thinking": "#d68a6e",   # Naranja claro
            "speaking": "#b86a50",   # Naranja oscuro
        }
        return colors.get(self.current_state, "#cc785c")

    def setup_animation(self):
        """Configura el timer para animaciones"""
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(100)  # 10 FPS

    def animate(self):
        """Actualiza la animación del avatar"""
        self.animation_frame = (self.animation_frame + 1) % 30

        # Efecto de pulsación sutil
        if self.current_state in ["listening", "thinking", "speaking"]:
            self.create_default_avatar()

    def set_state(self, state: str):
        """
        Cambia el estado del avatar.

        Args:
            state: Nuevo estado ("idle", "listening", "thinking", "speaking")
        """
        if state not in ["idle", "listening", "thinking", "speaking"]:
            return

        self.current_state = state
        self.update_state_display()
        self.create_default_avatar()
        self.state_changed.emit(state)

    def update_state_display(self):
        """Actualiza el texto del estado"""
        state_texts = {
            "idle": "Listo para ayudarte",
            "listening": "Escuchando...",
            "thinking": "Procesando...",
            "speaking": "Respondiendo...",
        }
        self.state_label.setText(state_texts.get(self.current_state, "Listo para ayudarte"))

    def get_state(self) -> str:
        """Retorna el estado actual del avatar"""
        return self.current_state

    def start_listening(self):
        """Inicia el estado de escucha"""
        self.set_state("listening")

    def start_thinking(self):
        """Inicia el estado de pensamiento"""
        self.set_state("thinking")

    def start_speaking(self):
        """Inicia el estado de habla"""
        self.set_state("speaking")

    def stop(self):
        """Detiene la animación y vuelve a idle"""
        self.set_state("idle")
