"""
Diálogo para gestionar el catálogo de proveedores.
Permite crear, editar y desactivar proveedores.
Accesible desde el menú de la ventana principal.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox, QHeaderView,
    QFormLayout, QLineEdit, QTextEdit
)
from PyQt5.QtCore import Qt
import logging

from app.infrastructure.proveedor_repository import ProveedorRepository, Proveedor

logger = logging.getLogger(__name__)


class ProveedoresDialog(QDialog):
    """Diálogo de gestión de proveedores (CRUD completo)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.proveedor_repo = ProveedorRepository()
        self.proveedores = []
        self.setWindowTitle("Gestión de Proveedores")
        self.setMinimumSize(700, 480)
        self.setup_ui()
        self.cargar_proveedores()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Título
        title = QLabel("Catálogo de Proveedores")
        title.setStyleSheet("font-size: 18pt; font-weight: 700; color: #2d3748;")
        layout.addWidget(title)

        desc = QLabel("Administra los proveedores disponibles para asignar a productos.")
        desc.setStyleSheet("font-size: 10pt; color: #718096; margin-bottom: 8px;")
        layout.addWidget(desc)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(
            ["Nombre", "Contacto", "Teléfono", "Email", "Estado"]
        )
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in [1, 2, 3, 4]:
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f7fafc;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: 600;
                color: #2d3748;
            }
        """)
        layout.addWidget(self.tabla)

        # Botones
        btn_layout = QHBoxLayout()

        self.btn_nuevo = QPushButton("Nuevo Proveedor")
        self.btn_nuevo.setObjectName("successButton")
        self.btn_nuevo.clicked.connect(self.nuevo_proveedor)
        btn_layout.addWidget(self.btn_nuevo)

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setObjectName("primaryButton")
        self.btn_editar.setEnabled(False)
        self.btn_editar.clicked.connect(self.editar_proveedor)
        btn_layout.addWidget(self.btn_editar)

        self.btn_eliminar = QPushButton("Desactivar")
        self.btn_eliminar.setObjectName("dangerButton")
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.clicked.connect(self.desactivar_proveedor)
        btn_layout.addWidget(self.btn_eliminar)

        btn_layout.addStretch()

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        btn_layout.addWidget(btn_cerrar)

        layout.addLayout(btn_layout)

        self.tabla.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def cargar_proveedores(self):
        """Carga proveedores desde la BD"""
        try:
            self.proveedores = self.proveedor_repo.get_all(solo_activos=False)
            self.tabla.setRowCount(0)
            for prov in self.proveedores:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)
                self.tabla.setItem(row, 0, QTableWidgetItem(prov.nombre))
                self.tabla.setItem(row, 1, QTableWidgetItem(prov.contacto or ""))
                self.tabla.setItem(row, 2, QTableWidgetItem(prov.telefono or ""))
                self.tabla.setItem(row, 3, QTableWidgetItem(prov.email or ""))
                estado_item = QTableWidgetItem("Activo" if prov.activo else "Inactivo")
                estado_item.setForeground(
                    Qt.darkGreen if prov.activo else Qt.red
                )
                self.tabla.setItem(row, 4, estado_item)
        except Exception as e:
            logger.error(f"Error al cargar proveedores: {e}")

    def _on_selection_changed(self):
        tiene_sel = len(self.tabla.selectionModel().selectedRows()) > 0
        self.btn_editar.setEnabled(tiene_sel)
        self.btn_eliminar.setEnabled(tiene_sel)

    def _get_proveedor_seleccionado(self):
        rows = self.tabla.selectionModel().selectedRows()
        if rows:
            idx = rows[0].row()
            if idx < len(self.proveedores):
                return self.proveedores[idx]
        return None

    def nuevo_proveedor(self):
        """Abre diálogo para crear un proveedor"""
        dialog = _ProveedorFormDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                prov = dialog.get_proveedor()
                self.proveedor_repo.create(prov)
                self.cargar_proveedores()
                QMessageBox.information(self, "Éxito", "Proveedor creado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el proveedor:\n{str(e)}")

    def editar_proveedor(self):
        """Abre diálogo para editar el proveedor seleccionado"""
        prov = self._get_proveedor_seleccionado()
        if not prov:
            return
        dialog = _ProveedorFormDialog(proveedor=prov, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                prov_actualizado = dialog.get_proveedor()
                prov_actualizado.id = prov.id
                self.proveedor_repo.update(prov_actualizado)
                self.cargar_proveedores()
                QMessageBox.information(self, "Éxito", "Proveedor actualizado.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar:\n{str(e)}")

    def desactivar_proveedor(self):
        """Desactiva (soft-delete) el proveedor seleccionado"""
        prov = self._get_proveedor_seleccionado()
        if not prov:
            return
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Desactivar al proveedor '{prov.nombre}'?\n"
            "Los productos asociados mantendrán su historial.",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            try:
                self.proveedor_repo.delete(prov.id)
                self.cargar_proveedores()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo desactivar:\n{str(e)}")


# ---------------------------------------------------------------------------
# Diálogo de formulario (crear / editar un proveedor)
# ---------------------------------------------------------------------------

class _ProveedorFormDialog(QDialog):
    """Formulario para crear o editar un proveedor"""

    def __init__(self, proveedor: Proveedor = None, parent=None):
        super().__init__(parent)
        self.proveedor = proveedor
        self.is_edit = proveedor is not None
        self.setWindowTitle("Editar Proveedor" if self.is_edit else "Nuevo Proveedor")
        self.setMinimumWidth(420)
        self._setup()

    def _setup(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Nombre del proveedor *")
        form.addRow("Nombre *:", self.nombre_input)

        self.contacto_input = QLineEdit()
        self.contacto_input.setPlaceholderText("Persona de contacto")
        form.addRow("Contacto:", self.contacto_input)

        self.telefono_input = QLineEdit()
        self.telefono_input.setPlaceholderText("Teléfono")
        form.addRow("Teléfono:", self.telefono_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("correo@proveedor.com")
        form.addRow("Email:", self.email_input)

        self.notas_input = QTextEdit()
        self.notas_input.setMaximumHeight(70)
        self.notas_input.setPlaceholderText("Observaciones adicionales")
        form.addRow("Notas:", self.notas_input)

        layout.addLayout(form)

        # Cargar datos si es edición
        if self.is_edit:
            self.nombre_input.setText(self.proveedor.nombre)
            self.contacto_input.setText(self.proveedor.contacto or "")
            self.telefono_input.setText(self.proveedor.telefono or "")
            self.email_input.setText(self.proveedor.email or "")
            self.notas_input.setPlainText(self.proveedor.notas or "")

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("Guardar")
        btn_ok.setObjectName("primaryButton")
        btn_ok.clicked.connect(self._validar_y_aceptar)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def _validar_y_aceptar(self):
        nombre = self.nombre_input.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Campo requerido", "El nombre del proveedor es obligatorio.")
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


__all__ = ["ProveedoresDialog"]
