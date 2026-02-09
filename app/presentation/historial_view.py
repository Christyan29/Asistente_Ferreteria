"""
Vista de Historial de Conversaciones.
Muestra el historial de conversaciones pasadas con el asistente.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QTextBrowser, QLabel, QDateEdit, QComboBox, QLineEdit,
    QMessageBox, QListWidgetItem
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from datetime import datetime
import logging

from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class HistorialView(QWidget):
    """Vista para mostrar el historial de conversaciones"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.conversation_service = ConversationService()
        self.setup_ui()
        self.load_conversations()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        title = QLabel("Historial de Conversaciones")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # Panel principal (lista + detalles)
        main_panel = QHBoxLayout()
        main_panel.setSpacing(15)

        # Lista de conversaciones (izquierda)
        self.conversation_list = QListWidget()
        self.conversation_list.setMinimumWidth(300)
        self.conversation_list.itemClicked.connect(self.on_conversation_selected)
        main_panel.addWidget(self.conversation_list, stretch=1)

        # Panel de detalles (derecha)
        self.details_panel = QTextBrowser()
        self.details_panel.setReadOnly(True)
        main_panel.addWidget(self.details_panel, stretch=2)

        layout.addLayout(main_panel)

        # Botones de acción
        button_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Actualizar")
        self.refresh_btn.clicked.connect(self.load_conversations)

        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Aplicar estilos
        self.apply_styles()

    def create_filter_panel(self):
        """Crea el panel de filtros"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Fecha desde
        layout.addWidget(QLabel("Desde:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        layout.addWidget(self.date_from)

        # Fecha hasta
        layout.addWidget(QLabel("Hasta:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        layout.addWidget(self.date_to)

        # Tipo de intención
        layout.addWidget(QLabel("Tipo:"))
        self.intent_filter = QComboBox()
        self.intent_filter.addItems(["Todos", "Productos", "Instrucciones", "General", "Fuera de tema"])
        layout.addWidget(self.intent_filter)

        # Búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar en conversaciones...")
        layout.addWidget(self.search_input)

        layout.addStretch()

        return panel

    def load_conversations(self):
        """Carga conversaciones desde la base de datos"""
        try:
            conversations = self.conversation_service.repository.get_recent_conversations(limit=50)

            self.conversation_list.clear()

            if not conversations:
                item = QListWidgetItem("No hay conversaciones registradas")
                item.setFlags(Qt.NoItemFlags)
                self.conversation_list.addItem(item)
                self.details_panel.setHtml("<p>No hay conversaciones para mostrar.</p>")
                return

            for conv in conversations:
                # Formatear item
                fecha = conv.started_at.strftime('%d/%m/%Y %H:%M')
                item_text = f"{fecha} - {conv.total_interactions} mensajes"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, conv.id)
                self.conversation_list.addItem(item)

            logger.info(f"Cargadas {len(conversations)} conversaciones")

        except Exception as e:
            logger.error(f"Error al cargar conversaciones: {e}")
            QMessageBox.warning(self, "Error", f"No se pudo cargar el historial: {e}")

    def on_conversation_selected(self, item):
        """Muestra detalles de la conversación seleccionada"""
        conversation_id = item.data(Qt.UserRole)

        if not conversation_id:
            return

        try:
            conv, interactions = self.conversation_service.repository.get_conversation_with_interactions(conversation_id)

            # Formatear HTML
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 15px; }}
                    h2 {{ color: #2c3e50; border-bottom: 2px solid #cc785c; padding-bottom: 10px; }}
                    .meta {{ color: #6c757d; font-size: 11pt; margin-bottom: 20px; }}
                    .interaction {{ margin-bottom: 30px; padding: 18px; background: #f8f9fa; border-radius: 8px; border-left: 3px solid #cc785c; }}
                    .question {{ color: #495057; font-weight: 600; margin-bottom: 8px; }}
                    .answer {{ color: #cc785c; margin-bottom: 8px; }}
                    .stats {{ font-size: 9pt; color: #6c757d; }}
                    hr {{ border: none; border-top: 1px solid #dee2e6; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <h2>Conversación del {conv.started_at.strftime('%d/%m/%Y %H:%M')}</h2>
                <div class="meta">
                    <strong>Total de mensajes:</strong> {conv.total_interactions}
                </div>
                <hr>
            """

            for i, inter in enumerate(interactions, 1):
                html += f"""
                <div class="interaction">
                    <div class="question">Usuario: {inter.question}</div>
                    <div class="answer">Gabo: {inter.answer[:200]}{"..." if len(inter.answer) > 200 else ""}</div>
                    <div class="stats">
                        Hora: {inter.created_at.strftime('%H:%M:%S')}
                    </div>
                </div>
                """

            html += """
            </body>
            </html>
            """

            self.details_panel.setHtml(html)

        except Exception as e:
            logger.error(f"Error al cargar detalles: {e}")
            QMessageBox.warning(self, "Error", f"No se pudo cargar los detalles: {e}")

    def refresh_all(self):
        """Actualiza conversaciones"""
        self.load_conversations()

    def apply_styles(self):
        """Aplica estilos a la vista"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                font-size: 11pt;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #e9ecef;
                margin-bottom: 5px;
            }
            QListWidget::item:selected {
                background-color: #cc785c;
                color: white;
                border-left: 4px solid #b86d4f;
            }
            QListWidget::item:hover:!selected {
                background-color: #f8f9fa;
            }
            QTextBrowser {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton {
                background-color: #cc785c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #b86d4f;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
            QDateEdit, QComboBox, QLineEdit {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                font-size: 10pt;
            }
            QLabel {
                font-size: 11pt;
                color: #495057;
            }
        """)
