"""
Sistema de autenticación simple para acceso al inventario.
Solo el personal autorizado puede acceder a la gestión de inventario.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import hashlib


class LoginDialog(QDialog):
    """Diálogo de inicio de sesión para personal de la ferretería"""

    # Credenciales por defecto (en producción deberían estar en BD)
    USERS = {
        "admin": hashlib.sha256("admin123".encode()).hexdigest(),
        "personal": hashlib.sha256("ferreteria2024".encode()).hexdigest(),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.authenticated = False
        self.username = None
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz del diálogo"""
        self.setWindowTitle("Acceso al Inventario")
        self.setModal(True)
        self.setFixedSize(480, 320)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(40, 25, 40, 25)

        # Título
        title = QLabel("🔐 Acceso al Inventario")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont("Segoe UI", 15, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #2b2825; margin-bottom: 4px;")
        layout.addWidget(title)

        # Subtítulo
        subtitle = QLabel("Solo personal autorizado")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #6b6b65; font-size: 10pt; margin-bottom: 8px;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # Campo de usuario
        user_label = QLabel("Usuario:")
        user_label.setStyleSheet("color: #4a4a44; font-weight: 600; font-size: 10pt;")
        layout.addWidget(user_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ingrese su usuario")
        self.username_input.setMinimumHeight(40)
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 11px 14px;
                font-size: 11pt;
                border: 1.5px solid #d4d4ce;
                border-radius: 10px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #cc785c;
            }
        """)
        layout.addWidget(self.username_input)

        layout.addSpacing(6)

        # Campo de contraseña
        password_label = QLabel("Contraseña:")
        password_label.setStyleSheet("color: #4a4a44; font-weight: 600; font-size: 10pt;")
        layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Ingrese su contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 11px 14px;
                font-size: 11pt;
                border: 1.5px solid #d4d4ce;
                border-radius: 10px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #cc785c;
            }
        """)
        self.password_input.returnPressed.connect(self.login)
        layout.addWidget(self.password_input)

        layout.addSpacing(12)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 11px 24px;
                font-size: 11pt;
                background-color: #fafaf8;
                color: #4a4a44;
                border: 1px solid #d4d4ce;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #f0f0ea;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        login_btn = QPushButton("Iniciar Sesión")
        login_btn.setObjectName("primaryButton")
        login_btn.setMinimumHeight(40)
        login_btn.setStyleSheet("""
            QPushButton {
                padding: 11px 24px;
                font-size: 11pt;
                font-weight: 600;
                background-color: #cc785c;
                color: #ffffff;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #d68a6e;
            }
            QPushButton:pressed {
                background-color: #b86a50;
            }
        """)
        login_btn.clicked.connect(self.login)
        buttons_layout.addWidget(login_btn)

        layout.addLayout(buttons_layout)

    def login(self):
        """Valida las credenciales e inicia sesión"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(
                self,
                "Campos vacíos",
                "Por favor ingrese usuario y contraseña"
            )
            return

        # Validar credenciales
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if username in self.USERS and self.USERS[username] == password_hash:
            self.authenticated = True
            self.username = username
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Acceso Denegado",
                "Usuario o contraseña incorrectos"
            )
            self.password_input.clear()
            self.password_input.setFocus()

    def is_authenticated(self):
        """Retorna si el usuario está autenticado"""
        return self.authenticated

    def get_username(self):
        """Retorna el nombre de usuario autenticado"""
        return self.username
