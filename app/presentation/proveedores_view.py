"""
Vista de Gestión de Proveedores – pestaña principal de la aplicación.
Reemplaza el antiguo diálogo emergente con una vista completa integrada en el stack.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox, QHeaderView, QLineEdit,
    QComboBox, QFrame, QDialog, QFormLayout, QTextEdit, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
import logging

from app.infrastructure.proveedor_repository import ProveedorRepository, Proveedor

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Estilos globales reutilizados
# ──────────────────────────────────────────────────────────────────────────────
_BTN_PRIMARY = """
    QPushButton {
        background-color: #cc785c;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-size: 10pt;
        font-weight: 600;
    }
    QPushButton:hover  { background-color: #b5634a; }
    QPushButton:pressed{ background-color: #9e5040; }
    QPushButton:disabled{ background-color: #e2b8a8; color: white; }
"""
_BTN_SUCCESS = """
    QPushButton {
        background-color: #38a169;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-size: 10pt;
        font-weight: 600;
    }
    QPushButton:hover  { background-color: #2f8a59; }
    QPushButton:pressed{ background-color: #276749; }
"""
_BTN_DANGER = """
    QPushButton {
        background-color: #e53e3e;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-size: 10pt;
        font-weight: 600;
    }
    QPushButton:hover  { background-color: #c53030; }
    QPushButton:pressed{ background-color: #9b2c2c; }
    QPushButton:disabled{ background-color: #feb2b2; color: white; }
"""
_BTN_SECONDARY = """
    QPushButton {
        background-color: #f7fafc;
        color: #4a5568;
        border: 1px solid #cbd5e0;
        border-radius: 6px;
        padding: 8px 18px;
        font-size: 10pt;
        font-weight: 500;
    }
    QPushButton:hover  { background-color: #edf2f7; }
    QPushButton:pressed{ background-color: #e2e8f0; }
"""
_TABLE_STYLE = """
    QTableWidget {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background-color: white;
        gridline-color: #f0f4f8;
    }
    QTableWidget::item { padding: 10px 8px; }
    QTableWidget::item:selected {
        background-color: #fff5f0;
        color: #2d3748;
    }
    QHeaderView::section {
        background-color: #f7fafc;
        padding: 10px 8px;
        border: none;
        border-bottom: 2px solid #e2e8f0;
        font-weight: 600;
        color: #2d3748;
        font-size: 10pt;
    }
"""


class ProveedoresView(QWidget):
    """Pestaña completa de gestión de proveedores."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.proveedor_repo = ProveedorRepository()
        self.proveedores_todos: list = []      # todos (activos + inactivos)
        self.proveedores_filtrados: list = []  # los que se muestran en la tabla
        self._setup_ui()
        # Defer load to avoid DB hit before window is shown
        QTimer.singleShot(0, self.cargar_proveedores)

    # ─────────────────────────── UI ──────────────────────────────────────────
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(28, 24, 28, 20)

        # ── Encabezado ────────────────────────────────────────────────────
        header = QHBoxLayout()
        col_title = QVBoxLayout()
        col_title.setSpacing(2)

        lbl_title = QLabel("Gestión de Proveedores")
        lbl_title.setStyleSheet(
            "font-size: 22pt; font-weight: 700; color: #2d3748;"
        )
        col_title.addWidget(lbl_title)

        lbl_sub = QLabel(
            "Administra el catálogo de proveedores activos para asignar a productos y pedidos."
        )
        lbl_sub.setStyleSheet("font-size: 10pt; color: #718096;")
        col_title.addWidget(lbl_sub)

        header.addLayout(col_title)
        header.addStretch()

        # Contador badge
        self.lbl_contador = QLabel("0 proveedores")
        self.lbl_contador.setStyleSheet("""
            font-size: 13pt; font-weight: 600; color: #cc785c;
            background-color: #fff5f0;
            padding: 8px 16px; border-radius: 6px;
        """)
        header.addWidget(self.lbl_contador)
        root.addLayout(header)

        # ── Separador ─────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e2e8f0;")
        root.addWidget(sep)

        # ── Barra de búsqueda y filtros ───────────────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre, contacto o email…")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 10pt;
                background-color: white;
            }
            QLineEdit:focus { border-color: #cc785c; }
        """)
        self.search_input.textChanged.connect(self._aplicar_filtro)

        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["Todos", "Activos", "Inactivos"])
        self.combo_estado.setFixedWidth(130)
        self.combo_estado.setStyleSheet("""
            QComboBox {
                border: 1px solid #cbd5e0; border-radius: 6px;
                padding: 7px 10px; font-size: 10pt;
                background-color: white;
            }
            QComboBox::drop-down { border: none; }
            QComboBox:focus { border-color: #cc785c; }
        """)
        self.combo_estado.currentIndexChanged.connect(self._aplicar_filtro)

        btn_refrescar = QPushButton("↺  Actualizar")
        btn_refrescar.setStyleSheet(_BTN_SECONDARY)
        btn_refrescar.clicked.connect(self.cargar_proveedores)

        bar.addWidget(self.search_input, 1)
        bar.addWidget(self.combo_estado)
        bar.addWidget(btn_refrescar)
        root.addLayout(bar)

        # ── Tabla ─────────────────────────────────────────────────────────
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(
            ["Nombre", "Contacto", "Teléfono", "Email", "Notas", "Estado"]
        )
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setStyleSheet(_TABLE_STYLE)

        hdr = self.tabla.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)      # Nombre
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.Stretch)       # Notas
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.tabla.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )
        self.tabla.doubleClicked.connect(self._editar_seleccionado)

        root.addWidget(self.tabla)

        # ── Acciones rápidas (tarjetas informativas) ──────────────────────
        self.info_bar = QLabel("")
        self.info_bar.setStyleSheet(
            "font-size: 9pt; color: #718096; padding: 4px 0;"
        )
        root.addWidget(self.info_bar)

        # ── Botones de acción ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_nuevo = QPushButton("＋  Nuevo Proveedor")
        self.btn_nuevo.setStyleSheet(_BTN_SUCCESS)
        self.btn_nuevo.clicked.connect(self._nuevo_proveedor)

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setStyleSheet(_BTN_PRIMARY)
        self.btn_editar.setEnabled(False)
        self.btn_editar.clicked.connect(self._editar_seleccionado)

        self.btn_toggle_estado = QPushButton("Desactivar")
        self.btn_toggle_estado.setStyleSheet(_BTN_DANGER)
        self.btn_toggle_estado.setEnabled(False)
        self.btn_toggle_estado.clicked.connect(self._toggle_estado)

        btn_row.addWidget(self.btn_nuevo)
        btn_row.addWidget(self.btn_editar)
        btn_row.addWidget(self.btn_toggle_estado)
        btn_row.addStretch()

        # Hint de doble-click
        hint = QLabel("Doble-clic en una fila para editar rápidamente")
        hint.setStyleSheet("font-size: 9pt; color: #a0aec0;")
        btn_row.addWidget(hint)

        root.addLayout(btn_row)

    # ─────────────────────────── Datos ───────────────────────────────────────
    def cargar_proveedores(self):
        """Carga todos los proveedores desde la BD y aplica el filtro actual."""
        try:
            self.proveedores_todos = self.proveedor_repo.get_all(solo_activos=False)
            self._aplicar_filtro()
            logger.debug(
                f"ProveedoresView: {len(self.proveedores_todos)} proveedores cargados"
            )
        except Exception as e:
            logger.error(f"Error cargando proveedores: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo cargar el catálogo:\n{e}")

    def _aplicar_filtro(self):
        """Filtra la lista según texto de búsqueda y combo de estado."""
        texto = self.search_input.text().lower().strip()
        estado_idx = self.combo_estado.currentIndex()  # 0=Todos 1=Activos 2=Inactivos

        result = []
        for p in self.proveedores_todos:
            # Filtro estado
            if estado_idx == 1 and not p.activo:
                continue
            if estado_idx == 2 and p.activo:
                continue
            # Filtro texto
            if texto:
                haystack = " ".join([
                    p.nombre or "",
                    p.contacto or "",
                    p.email or "",
                    p.telefono or "",
                ]).lower()
                if texto not in haystack:
                    continue
            result.append(p)

        self.proveedores_filtrados = result
        self._poblar_tabla()

    def _poblar_tabla(self):
        """Rellena la tabla con proveedores_filtrados."""
        self.tabla.clearSelection()
        self.tabla.setRowCount(0)
        activos = sum(1 for p in self.proveedores_todos if p.activo)

        for p in self.proveedores_filtrados:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)

            nombre_item = QTableWidgetItem(p.nombre)
            nombre_item.setForeground(
                QColor("#2d3748") if p.activo else QColor("#a0aec0")
            )
            self.tabla.setItem(row, 0, nombre_item)
            self.tabla.setItem(row, 1, QTableWidgetItem(p.contacto or ""))
            self.tabla.setItem(row, 2, QTableWidgetItem(p.telefono or ""))
            self.tabla.setItem(row, 3, QTableWidgetItem(p.email or ""))
            self.tabla.setItem(row, 4, QTableWidgetItem(p.notas or ""))

            estado_text = "Activo" if p.activo else "Inactivo"
            estado_item = QTableWidgetItem(estado_text)
            estado_item.setTextAlignment(Qt.AlignCenter)
            estado_item.setForeground(
                QColor("#38a169") if p.activo else QColor("#e53e3e")
            )
            self.tabla.setItem(row, 5, estado_item)

        # Actualizar contador y barra de info
        total = len(self.proveedores_filtrados)
        self.lbl_contador.setText(
            f"{total} proveedor{'es' if total != 1 else ''}"
        )
        self.info_bar.setText(
            f"{activos} activo(s) · {len(self.proveedores_todos) - activos} inactivo(s)"
            f" — mostrando {total} de {len(self.proveedores_todos)}"
        )
        self._on_selection_changed()  # Reset botones

    # ─────────────────────────── Selección ───────────────────────────────────
    def _on_selection_changed(self):
        rows = self.tabla.selectionModel().selectedRows()
        tiene_sel = len(rows) > 0
        self.btn_editar.setEnabled(tiene_sel)
        self.btn_toggle_estado.setEnabled(tiene_sel)

        if tiene_sel:
            prov = self._get_proveedor_seleccionado()
            if prov:
                nuevo_texto = "Activar" if not prov.activo else "Desactivar"
                self.btn_toggle_estado.setText(nuevo_texto)
                estilos = _BTN_SUCCESS if not prov.activo else _BTN_DANGER
                self.btn_toggle_estado.setStyleSheet(estilos)

    def _get_proveedor_seleccionado(self):
        rows = self.tabla.selectionModel().selectedRows()
        if rows:
            idx = rows[0].row()
            if idx < len(self.proveedores_filtrados):
                return self.proveedores_filtrados[idx]
        return None

    # ─────────────────────────── CRUD ────────────────────────────────────────
    def _nuevo_proveedor(self):
        dlg = _ProveedorFormDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            try:
                prov = dlg.get_proveedor()
                self.proveedor_repo.create(prov)
                self.cargar_proveedores()
                QMessageBox.information(
                    self, "Éxito", f"Proveedor '{prov.nombre}' creado correctamente."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el proveedor:\n{e}")

    def _editar_seleccionado(self, *_):
        prov = self._get_proveedor_seleccionado()
        if not prov:
            return
        dlg = _ProveedorFormDialog(proveedor=prov, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            try:
                prov_actualizado = dlg.get_proveedor()
                prov_actualizado.id = prov.id
                self.proveedor_repo.update(prov_actualizado)
                self.cargar_proveedores()
                QMessageBox.information(self, "Éxito", "Proveedor actualizado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar:\n{e}")

    def _toggle_estado(self):
        prov = self._get_proveedor_seleccionado()
        if not prov:
            return
        accion = "activar" if not prov.activo else "desactivar"
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Desea {accion} al proveedor '{prov.nombre}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            try:
                if prov.activo:
                    self.proveedor_repo.delete(prov.id)   # soft-delete / desactivar
                else:
                    # Reactivar
                    prov.activo = True
                    self.proveedor_repo.update(prov)
                self.cargar_proveedores()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo {accion}:\n{e}")

    def showEvent(self, event):
        """Actualiza datos al navegar a la pestaña."""
        super().showEvent(event)
        self.cargar_proveedores()


# ─────────────────────────────────────────────────────────────────────────────
# Formulario reutilizable para crear/editar un proveedor
# ─────────────────────────────────────────────────────────────────────────────
class _ProveedorFormDialog(QDialog):
    def __init__(self, proveedor: Proveedor = None, parent=None):
        super().__init__(parent)
        self.proveedor = proveedor
        self.is_edit = proveedor is not None
        self.setWindowTitle("Editar Proveedor" if self.is_edit else "Nuevo Proveedor")
        self.setMinimumWidth(440)
        self._setup()

    def _setup(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 16)

        title = QLabel("Editar Proveedor" if self.is_edit else "Nuevo Proveedor")
        title.setStyleSheet("font-size: 14pt; font-weight: 700; color: #2d3748;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        field_style = """
            QLineEdit, QTextEdit {
                border: 1px solid #cbd5e0;
                border-radius: 5px;
                padding: 7px 10px;
                font-size: 10pt;
            }
            QLineEdit:focus, QTextEdit:focus { border-color: #cc785c; }
        """

        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Nombre del proveedor *")
        self.nombre_input.setStyleSheet(field_style)

        self.contacto_input = QLineEdit()
        self.contacto_input.setPlaceholderText("Persona de contacto")
        self.contacto_input.setStyleSheet(field_style)

        self.telefono_input = QLineEdit()
        self.telefono_input.setPlaceholderText("Ej: 0999123456")
        self.telefono_input.setStyleSheet(field_style)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("correo@proveedor.com")
        self.email_input.setStyleSheet(field_style)

        self.notas_input = QTextEdit()
        self.notas_input.setMaximumHeight(80)
        self.notas_input.setPlaceholderText("Condiciones, descuentos, observaciones…")
        self.notas_input.setStyleSheet(field_style)

        form.addRow("Nombre *:", self.nombre_input)
        form.addRow("Contacto:", self.contacto_input)
        form.addRow("Teléfono:", self.telefono_input)
        form.addRow("Email:", self.email_input)
        form.addRow("Notas:", self.notas_input)
        layout.addLayout(form)

        if self.is_edit:
            self.nombre_input.setText(self.proveedor.nombre)
            self.contacto_input.setText(self.proveedor.contacto or "")
            self.telefono_input.setText(self.proveedor.telefono or "")
            self.email_input.setText(self.proveedor.email or "")
            self.notas_input.setPlainText(self.proveedor.notas or "")

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet(_BTN_SECONDARY)
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Guardar")
        btn_ok.setStyleSheet(_BTN_PRIMARY)
        btn_ok.clicked.connect(self._validar)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def _validar(self):
        if not self.nombre_input.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El nombre es obligatorio.")
            self.nombre_input.setFocus()
            return
        self.accept()

    def get_proveedor(self) -> Proveedor:
        return Proveedor(
            nombre=self.nombre_input.text().strip(),
            contacto=self.contacto_input.text().strip() or None,
            telefono=self.telefono_input.text().strip() or None,
            email=self.email_input.text().strip() or None,
            notas=self.notas_input.toPlainText().strip() or None,
        )


__all__ = ["ProveedoresView"]
