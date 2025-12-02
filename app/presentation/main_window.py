"""
Ventana principal de la aplicación - Diseño moderno pastel minimalista.
Inspirado en interfaces modernas de chat IA con autenticación para inventario.
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStackedWidget, QLabel, QMenuBar, QMenu, QAction, QStatusBar,
    QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
import logging

from app.presentation.inventario_view import InventarioView
from app.presentation.asistente_view import AsistenteView
from app.presentation.login_dialog import LoginDialog
from app.presentation.styles import get_stylesheet
from app.config.settings import AppConfig

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación con diseño moderno"""

    def __init__(self):
        super().__init__()
        self.authenticated_user = None
        self.setup_window()
        self.setup_ui()
        self.setup_menu()
        self.setup_statusbar()

        # Aplicar estilos Claude
        self.setStyleSheet(get_stylesheet("claude"))

        logger.info("Ventana principal inicializada con tema pastel")

    def setup_window(self):
        """Configura las propiedades de la ventana"""
        self.setWindowTitle(f"Gabo - {AppConfig.NAME}")
        self.setMinimumSize(AppConfig.WINDOW_WIDTH, AppConfig.WINDOW_HEIGHT)

        # Centrar ventana
        screen = self.screen().geometry()
        x = (screen.width() - AppConfig.WINDOW_WIDTH) // 2
        y = (screen.height() - AppConfig.WINDOW_HEIGHT) // 2
        self.setGeometry(x, y, AppConfig.WINDOW_WIDTH, AppConfig.WINDOW_HEIGHT)

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header moderno
        header = self.create_header()
        main_layout.addWidget(header)

        # Contenido principal
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Stack de vistas (sin panel lateral, estilo moderno)
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget, stretch=1)

        main_layout.addLayout(content_layout)

        # Crear vistas
        self.create_views()

    def create_header(self):
        """Crea el header moderno estilo ChatGPT"""
        header = QWidget()
        header.setObjectName("sidePanel")
        header.setStyleSheet("""
            QWidget#sidePanel {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
            }
        """)
        header.setFixedHeight(70)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        # Logo/Título
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        logo_label = QLabel("G")
        logo_label.setStyleSheet("""
            background-color: #cc785c;
            color: #ffffff;
            font-size: 20pt;
            font-weight: bold;
            border-radius: 20px;
            padding: 8px 15px;
        """)
        title_layout.addWidget(logo_label)

        title = QLabel("Gabo")
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #2b2825;")
        title_layout.addWidget(title)

        subtitle = QLabel("Ferretería Disensa")
        subtitle.setStyleSheet("color: #6b6b65; font-size: 10pt;")
        title_layout.addWidget(subtitle)

        title_layout.addStretch()
        layout.addWidget(title_container)

        layout.addStretch()

        # Botones de navegación modernos
        self.nav_buttons = []

        # Botón Asistente
        btn_asistente = self.create_modern_nav_button("💬 Chat", 0, True)
        layout.addWidget(btn_asistente)
        self.nav_buttons.append(btn_asistente)

        # Botón Inventario (con icono de candado)
        btn_inventario = self.create_modern_nav_button("🔐 Inventario", 1, False)
        layout.addWidget(btn_inventario)
        self.nav_buttons.append(btn_inventario)

        return header

    def create_modern_nav_button(self, text, index, is_default=False):
        """Crea un botón de navegación moderno"""
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(is_default)
        btn.setMinimumWidth(120)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4a5568;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: 500;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #f7fafc;
            }
            QPushButton:checked {
                background-color: #cc785c;
                color: #ffffff;
                font-weight: 600;
            }
        """)
        btn.clicked.connect(lambda: self.cambiar_vista(index))
        return btn

    def create_views(self):
        """Crea las vistas de la aplicación"""
        # Vista del Asistente (siempre accesible)
        self.asistente_view = AsistenteView()
        self.stacked_widget.addWidget(self.asistente_view)

        # Vista de Inventario (requiere autenticación)
        self.inventario_view = InventarioView()
        self.stacked_widget.addWidget(self.inventario_view)

        # Mostrar vista del asistente por defecto
        self.cambiar_vista(0)

    def cambiar_vista(self, index):
        """Cambia la vista actual con autenticación para inventario"""
        # Si intenta acceder al inventario (index 1), verificar autenticación
        if index == 1:
            if not self.authenticated_user:
                # Mostrar diálogo de login
                login_dialog = LoginDialog(self)
                if login_dialog.exec_() == login_dialog.Accepted:
                    if login_dialog.is_authenticated():
                        self.authenticated_user = login_dialog.get_username()
                        logger.info(f"Usuario autenticado: {self.authenticated_user}")
                        self.mostrar_vista_inventario(index)
                    else:
                        # Volver a la vista del asistente
                        self.cambiar_vista(0)
                        return
                else:
                    # Usuario canceló, volver al asistente
                    self.cambiar_vista(0)
                    return
            else:
                self.mostrar_vista_inventario(index)
        else:
            # Vista del asistente, siempre accesible
            self.stacked_widget.setCurrentIndex(index)
            self.actualizar_botones_navegacion(index)
            self.statusBar().showMessage("Vista: Chat con Gabo")

    def mostrar_vista_inventario(self, index):
        """Muestra la vista de inventario después de autenticación"""
        self.stacked_widget.setCurrentIndex(index)
        self.actualizar_botones_navegacion(index)
        self.statusBar().showMessage(f"Vista: Gestión de Inventario | Usuario: {self.authenticated_user}")

    def actualizar_botones_navegacion(self, index):
        """Actualiza el estado de los botones de navegación"""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def setup_menu(self):
        """Configura el menú de la aplicación"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
                padding: 4px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #f7fafc;
            }
        """)

        # Menú Archivo
        menu_archivo = menubar.addMenu("&Archivo")

        action_refrescar = QAction("🔄 Refrescar", self)
        action_refrescar.setShortcut("F5")
        action_refrescar.triggered.connect(self.refrescar_datos)
        menu_archivo.addAction(action_refrescar)

        action_cerrar_sesion = QAction("🚪 Cerrar Sesión Inventario", self)
        action_cerrar_sesion.triggered.connect(self.cerrar_sesion)
        menu_archivo.addAction(action_cerrar_sesion)

        menu_archivo.addSeparator()

        action_salir = QAction("❌ Salir", self)
        action_salir.setShortcut("Ctrl+Q")
        action_salir.triggered.connect(self.close)
        menu_archivo.addAction(action_salir)

        # Menú Ver
        menu_ver = menubar.addMenu("&Ver")

        action_asistente = QAction("💬 Chat con Gabo", self)
        action_asistente.setShortcut("Ctrl+1")
        action_asistente.triggered.connect(lambda: self.cambiar_vista(0))
        menu_ver.addAction(action_asistente)

        action_inventario = QAction("🔐 Inventario", self)
        action_inventario.setShortcut("Ctrl+2")
        action_inventario.triggered.connect(lambda: self.cambiar_vista(1))
        menu_ver.addAction(action_inventario)

        # Menú Ayuda
        menu_ayuda = menubar.addMenu("&Ayuda")

        action_acerca = QAction("ℹ️ Acerca de", self)
        action_acerca.triggered.connect(self.mostrar_acerca_de)
        menu_ayuda.addAction(action_acerca)

    def setup_statusbar(self):
        """Configura la barra de estado"""
        statusbar = QStatusBar()
        statusbar.setStyleSheet("""
            QStatusBar {
                background-color: #ffffff;
                color: #718096;
                border-top: 1px solid #e2e8f0;
                padding: 4px;
            }
        """)
        self.setStatusBar(statusbar)
        statusbar.showMessage("Listo")

    def refrescar_datos(self):
        """Refresca los datos de la vista actual"""
        index = self.stacked_widget.currentIndex()

        if index == 1:  # Vista de inventario
            self.inventario_view.cargar_datos()
            self.statusBar().showMessage("✓ Datos actualizados", 3000)
        else:
            self.statusBar().showMessage("Vista actualizada", 3000)

    def cerrar_sesion(self):
        """Cierra la sesión del inventario"""
        if self.authenticated_user:
            respuesta = QMessageBox.question(
                self,
                "Cerrar Sesión",
                f"¿Desea cerrar la sesión de {self.authenticated_user}?",
                QMessageBox.Yes | QMessageBox.No
            )

            if respuesta == QMessageBox.Yes:
                self.authenticated_user = None
                self.cambiar_vista(0)  # Volver al asistente
                QMessageBox.information(self, "Sesión Cerrada", "Sesión cerrada correctamente")
                logger.info("Sesión de inventario cerrada")
        else:
            QMessageBox.information(self, "Sin Sesión", "No hay ninguna sesión activa")

    def mostrar_acerca_de(self):
        """Muestra el diálogo Acerca de"""
        mensaje = f"""
        <div style='text-align: center;'>
            <h2 style='color: #2d3748;'>Gabo - Asistente Virtual</h2>
            <p style='color: #4a5568;'><b>Versión:</b> {AppConfig.VERSION}</p>
            <p style='color: #718096;'>Sistema de gestión de inventario con asistente virtual<br>
            para la Ferretería Disensa de Pomasqui.</p>
            <br>
            <div style='text-align: left; padding: 0 20px;'>
                <p style='color: #2d3748;'><b>Características:</b></p>
                <ul style='color: #4a5568;'>
                    <li>💬 Chat con Gabo, tu asistente virtual</li>
                    <li>📦 Gestión completa de inventario (requiere autenticación)</li>
                    <li>⚠️ Alertas de stock bajo</li>
                    <li>🎨 Interfaz moderna y minimalista</li>
                </ul>
            </div>
            <br>
            <p style='color: #7eb8f5;'><b>Estado:</b> Versión funcional con tema pastel</p>
            <p style='color: #dd6b20; font-size: 9pt;'>
                ⚠️ Funcionalidades de IA y voz pendientes de configuración
            </p>
        </div>
        """

        QMessageBox.about(self, "Acerca de Gabo", mensaje)

    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana"""
        respuesta = QMessageBox.question(
            self,
            "Confirmar salida",
            "¿Está seguro de que desea salir de la aplicación?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            logger.info("Aplicación cerrada por el usuario")
            event.accept()
        else:
            event.ignore()
