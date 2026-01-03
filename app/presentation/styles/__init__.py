"""
Estilos QSS (Qt Style Sheets) para la aplicación.
Paleta de colores: crema, beige, naranja.
"""

# Colores principales
CLAUDE_THEME = """
/* ===== ESTILOS GLOBALES ===== */
QWidget {
    background-color: #f5f5f0;
    color: #2b2825;
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
    font-size: 10pt;
}

QMainWindow {
    background-color: #f5f5f0;
}

/* ===== BOTONES ===== */
QPushButton {
    background-color: #ffffff;
    color: #2b2825;
    border: 1px solid #d4d4ce;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: 500;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #fafaf8;
    border-color: #c4c4be;
}

QPushButton:pressed {
    background-color: #f0f0ea;
}

QPushButton:disabled {
    background-color: #fafaf8;
    color: #9b9b95;
    border-color: #e4e4de;
}

/* Botones Primarios */
QPushButton#primaryButton {
    background-color: #cc785c;
    color: #ffffff;
    border: none;
    font-weight: 600;
}

QPushButton#primaryButton:hover {
    background-color: #d68a6e;
}

QPushButton#primaryButton:pressed {
    background-color: #b86a50;
}

/* Botones de Peligro */
QPushButton#dangerButton {
    background-color: #e85d4a;
    color: #ffffff;
    border: none;
}

QPushButton#dangerButton:hover {
    background-color: #f06e5c;
}

/* Botones de Éxito */
QPushButton#successButton {
    background-color: #6ba56a;
    color: #ffffff;
    border: none;
}

QPushButton#successButton:hover {
    background-color: #7bb57a;
}

/* ===== CAMPOS DE TEXTO ===== */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    color: #2b2825;
    border: 1.5px solid #d4d4ce;
    border-radius: 10px;
    padding: 10px 14px;
    selection-background-color: #cc785c;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #cc785c;
    background-color: #fffffe;
}

/* ===== COMBOBOX ===== */
QComboBox {
    background-color: #ffffff;
    color: #2b2825;
    border: 1.5px solid #d4d4ce;
    border-radius: 10px;
    padding: 8px 12px;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #c4c4be;
}

QComboBox::drop-down {
    border: none;
    width: 25px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #6b6b65;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #2b2825;
    selection-background-color: #f5ebe5;
    selection-color: #2b2825;
    border: 1px solid #d4d4ce;
    border-radius: 8px;
    padding: 4px;
}

/* ===== SPINBOX ===== */
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    color: #2b2825;
    border: 1.5px solid #d4d4ce;
    border-radius: 10px;
    padding: 8px 12px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #cc785c;
}

/* ===== TABLAS ===== */
QTableWidget, QTableView {
    background-color: #ffffff;
    alternate-background-color: #fafaf8;
    color: #2b2825;
    gridline-color: #e4e4de;
    border: 1px solid #d4d4ce;
    border-radius: 12px;
    selection-background-color: #f5ebe5;
    selection-color: #2b2825;
}

QTableWidget::item, QTableView::item {
    padding: 12px 8px;
    border-bottom: 1px solid #f0f0ea;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #f5ebe5;
    color: #2b2825;
}

QHeaderView::section {
    background-color: #fafaf8;
    color: #4a4a44;
    padding: 12px 8px;
    border: none;
    border-bottom: 2px solid #e4e4de;
    font-weight: 600;
}

/* ===== SCROLLBARS ===== */
QScrollBar:vertical {
    background-color: #fafaf8;
    width: 10px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background-color: #c4c4be;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #b4b4ae;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #fafaf8;
    height: 10px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background-color: #c4c4be;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #b4b4ae;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ===== LABELS ===== */
QLabel {
    color: #2b2825;
    background-color: transparent;
}

QLabel#titleLabel {
    font-size: 28pt;
    font-weight: 700;
    color: #1a1816;
    letter-spacing: -0.5px;
}

QLabel#subtitleLabel {
    font-size: 14pt;
    font-weight: 500;
    color: #4a4a44;
}

QLabel#warningLabel {
    color: #d68a6e;
    font-weight: 600;
}

QLabel#errorLabel {
    color: #e85d4a;
    font-weight: 600;
}

QLabel#successLabel {
    color: #6ba56a;
    font-weight: 600;
}

/* ===== GROUPBOX ===== */
QGroupBox {
    border: 1.5px solid #d4d4ce;
    border-radius: 12px;
    margin-top: 16px;
    padding-top: 16px;
    font-weight: 600;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 6px 12px;
    color: #4a4a44;
}

/* ===== TABWIDGET ===== */
QTabWidget::pane {
    border: 1px solid #d4d4ce;
    border-radius: 12px;
    background-color: #ffffff;
    padding: 4px;
}

QTabBar::tab {
    background-color: #fafaf8;
    color: #6b6b65;
    padding: 12px 24px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #2b2825;
    font-weight: 600;
    border-bottom: 3px solid #cc785c;
}

QTabBar::tab:hover:!selected {
    background-color: #f0f0ea;
}

/* ===== MENUBAR ===== */
QMenuBar {
    background-color: #ffffff;
    color: #2b2825;
    border-bottom: 1px solid #d4d4ce;
    padding: 4px;
}

QMenuBar::item {
    padding: 8px 16px;
    background-color: transparent;
    border-radius: 6px;
}

QMenuBar::item:selected {
    background-color: #fafaf8;
}

QMenu {
    background-color: #ffffff;
    color: #2b2825;
    border: 1px solid #d4d4ce;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 10px 24px;
    border-radius: 6px;
}

QMenu::item:selected {
    background-color: #f5ebe5;
}

/* ===== STATUSBAR ===== */
QStatusBar {
    background-color: #ffffff;
    color: #6b6b65;
    border-top: 1px solid #d4d4ce;
    padding: 6px;
}

/* ===== PROGRESSBAR ===== */
QProgressBar {
    background-color: #e4e4de;
    border: none;
    border-radius: 10px;
    text-align: center;
    color: #4a4a44;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #cc785c;
    border-radius: 10px;
}

/* ===== CHECKBOX Y RADIOBUTTON ===== */
QCheckBox, QRadioButton {
    color: #2b2825;
    spacing: 8px;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #c4c4be;
    border-radius: 6px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #cc785c;
    border-color: #cc785c;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #d68a6e;
}

/* ===== TOOLTIPS ===== */
QToolTip {
    background-color: #2b2825;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    border-right: 1px solid #d4d4ce;
}
"""


def get_stylesheet(theme="default"):
    """
    Obtiene la hoja de estilos según el tema solicitado.

    Args:
        theme: "default" (por defecto)

    Returns:
        String con los estilos QSS
    """
    return CLAUDE_THEME
