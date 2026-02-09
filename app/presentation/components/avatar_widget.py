"""
Widget del Avatar para el asistente virtual.
Muestra una representación visual del asistente con diferentes estados usando sprites animados.
"""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPainterPath
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AvatarWidget(QWidget):
    """
    Widget que muestra el avatar del asistente con diferentes estados visuales.
    Estados: idle, listening, thinking, speaking

    Usa sprites animados (3 frames por estado) ubicados en app/assets/avatar/:
    - inactivo_01.png, inactivo_02.png, inactivo_03.png
    - escuchando_01.png, escuchando_02.png, escuchando_03.png
    - pensando_01.png, pensando_02.png, pensando_03.png
    - hablando_01.png, hablando_02.png, hablando_03.png

    Cada estado tiene un fondo circular de color pastel específico manejado por CSS.
    """

    # Señales
    state_changed = pyqtSignal(str)

    # Colores de fondo por estado (tonos pasteles coherentes con la paleta del programa)
    STATE_COLORS = {
        "idle": "#f5ebe5",      # Beige rosado suave
        "listening": "#d4e8d4",  # Verde pastel suave
        "thinking": "#fce8d8",   # Naranja pastel muy suave
        "speaking": "#ffd4d4",   # Rosa pastel suave
    }

    # Colores de borde por estado (versiones más saturadas para resaltar)
    STATE_BORDER_COLORS = {
        "idle": "#6a85c1",      # Azul más saturado
        "listening": "#6da66d",  # Verde más saturado
        "thinking": "#e09d73",   # Naranja más saturado
        "speaking": "#d15a4c",   # Rojo más saturado
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_state = "idle"
        self.current_frame = 0
        self.sprites = {}  # Cache: {state: [frame1, frame2, frame3]}
        self.use_fallback = False
        self.setup_ui()
        self.load_sprites()
        self.setup_animation()

    def setup_ui(self):
        """Configura la interfaz del widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Avatar visual con fondo de color sólido
        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("avatarWidget")
        self.avatar_label.setFixedSize(200, 200)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setScaledContents(False)

        # CRÍTICO: Forzar fondo opaco para eliminar checkerboard
        self.avatar_label.setAttribute(Qt.WA_OpaquePaintEvent)

        # Estado del avatar
        self.state_label = QLabel("Listo para ayudarte")
        self.state_label.setAlignment(Qt.AlignCenter)
        self.state_label.setStyleSheet("font-size: 11pt; color: #6b6b65;")

        layout.addWidget(self.avatar_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.state_label, alignment=Qt.AlignCenter)

    def load_sprites(self):
        """
        Carga los sprites animados desde el directorio de assets.

        Nombres esperados (3 frames por estado):
        - inactivo_01.png, inactivo_02.png, inactivo_03.png
        - escuchando_01.png, escuchando_02.png, escuchando_03.png
        - pensando_01.png, pensando_02.png, pensando_03.png
        - hablando_01.png, hablando_02.png, hablando_03.png
        """
        sprite_dir = Path("app/assets/avatar")

        state_prefixes = {
            "idle": "inactivo",
            "listening": "escuchando",
            "thinking": "pensando",
            "speaking": "hablando"
        }

        all_loaded = True
        for state, prefix in state_prefixes.items():
            frames = []

            for frame_num in range(1, 4):  # _01, _02, _03
                filename = f"{prefix}_{frame_num:02d}.png"
                sprite_path = sprite_dir / filename

                if sprite_path.exists():
                    try:
                        pixmap = QPixmap(str(sprite_path))
                        if not pixmap.isNull():
                            # Escalar a 180x180 manteniendo aspecto
                            scaled_pixmap = pixmap.scaled(
                                180, 180,
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
                            )
                            # Aplicar máscara circular (sin fondo, solo recorte)
                            scaled_pixmap = self.apply_circular_mask(scaled_pixmap)
                            frames.append(scaled_pixmap)
                            logger.info(f"Sprite cargado: {filename}")
                        else:
                            logger.warning(f"Sprite corrupto: {filename}")
                    except Exception as e:
                        logger.error(f"Error cargando sprite {filename}: {e}")
                else:
                    logger.warning(f"Sprite no encontrado: {sprite_path}")

            if frames:
                self.sprites[state] = frames
                logger.info(f"Estado '{state}' cargado con {len(frames)} frame(s)")
            else:
                all_loaded = False
                logger.warning(f"No se encontraron frames para estado '{state}'")

        if not all_loaded or len(self.sprites) < 4:
            self.use_fallback = True
            logger.info("Usando avatar de fallback (círculo con 'G')")

        self.update_display()

    def apply_circular_mask(self, pixmap):
        """
        Recorta el sprite a un círculo perfecto SIN agregar fondo.
        El fondo de color lo maneja el QLabel mediante CSS.

        Args:
            pixmap: QPixmap a recortar (180x180)

        Returns:
            QPixmap recortado en forma circular
        """
        size = 180
        rounded = QPixmap(size, size)
        # Transparente solo para el área FUERA del círculo
        rounded.fill(Qt.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Crear path circular (178px para evitar bordes pixelados)
        path = QPainterPath()
        path.addEllipse(1, 1, 178, 178)

        # Aplicar el path como región de recorte
        painter.setClipPath(path)

        # Dibujar la imagen original dentro del círculo
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        return rounded

    def update_display(self):
        """
        Actualiza la visualización del avatar según el estado y frame actual.
        El fondo de color se maneja completamente mediante CSS del QLabel.
        """
        # Definir colores de borde locales como solicitado
        BORDER_COLORS = {
            "idle": "#6a85c1",
            "listening": "#6da66d",
            "thinking": "#e09d73",
            "speaking": "#d15a4c"
        }

        # Obtener color de fondo y borde según estado
        bg_color = self.STATE_COLORS.get(self.current_state, "#f5ebe5")
        border_color = BORDER_COLORS.get(self.current_state, "#6a85c1")

        # CRÍTICO: Establecer fondo sólido mediante CSS con borde saturado
        # border-radius: 100px = 200px/2 (círculo perfecto)
        self.avatar_label.setStyleSheet(f"""
            QLabel#avatarWidget {{
                background-color: {bg_color};
                border-radius: 100px;
                border: 2px solid {border_color};
                padding: 0;
            }}
        """)

        if self.use_fallback or self.current_state not in self.sprites:
            self.create_fallback_avatar()
        else:
            # Obtener frames del estado actual
            frames = self.sprites[self.current_state]

            # Asegurar que el frame actual esté dentro del rango
            frame_index = self.current_frame % len(frames)
            sprite = frames[frame_index]

            # Mostrar sprite directamente (el fondo lo maneja el CSS)
            self.avatar_label.setPixmap(sprite)

    def create_fallback_avatar(self):
        """
        Crea un avatar de respaldo con círculo de color y letra 'G'.
        Se usa cuando los sprites no están disponibles.
        SIN transparencia - fondo sólido desde el inicio.
        """
        color = self.STATE_COLORS.get(self.current_state, "#f5ebe5")

        pixmap = QPixmap(200, 200)
        # CRÍTICO: Fondo sólido, NO transparente
        pixmap.fill(QColor(color))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dibujar letra "G" de Gabo
        painter.setPen(QColor("#2b2825"))  # Color de texto del programa
        font = QFont("Segoe UI", 80, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "G")

        painter.end()
        self.avatar_label.setPixmap(pixmap)

    def setup_animation(self):
        """
        Configura el timer para animaciones.
        Cicla a 400ms entre los 3 frames de cada estado (animación suave).
        """
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(400)  # 400ms por frame

    def animate(self):
        """
        Actualiza la animación del avatar ciclando entre frames.
        Solo anima si hay múltiples frames disponibles.
        """
        if not self.use_fallback and self.current_state in self.sprites:
            frames = self.sprites[self.current_state]

            # Solo ciclar si hay más de un frame
            if len(frames) > 1:
                self.current_frame = (self.current_frame + 1) % len(frames)
                self.update_display()

    def set_state(self, state: str):
        """
        Cambia el estado del avatar.

        Args:
            state: Nuevo estado ("idle", "listening", "thinking", "speaking")
        """
        if state not in ["idle", "listening", "thinking", "speaking"]:
            return

        self.current_state = state
        self.current_frame = 0  # Reiniciar animación
        self.update_state_display()
        self.update_display()
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
