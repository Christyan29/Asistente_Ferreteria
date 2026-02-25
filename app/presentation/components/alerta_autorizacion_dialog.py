"""
Diálogo de autorización de pedido automático.
Versión 2: más compacto, sin selección de filas, 3 opciones de respuesta,
y con soporte para "ignorar durante el día".
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from typing import List, Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)

# Fecha en que los productos fueron ignorados "durante el día"
_ignorados_hoy: dict = {}   # {producto_id: date}


class AlertaAutorizacionDialog(QDialog):
    """
    Popup de autorización para pedidos automáticos.

    Resultados posibles (código de retorno):
        QDialog.Accepted   → usuario autorizó el pedido
        QDialog.Rejected   → "Recordar más tarde"
        2                  → "Ignorar durante el día" (CustomRole 2)
    """

    IGNORAR_DIA_CODE = 2

    def __init__(self, productos, authenticated_user: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.productos = productos
        self.authenticated_user = authenticated_user
        self._pedido_creado = None

        self.setWindowTitle("Stock Bajo Detectado")
        self.setMinimumWidth(640)
        self.setMaximumWidth(780)
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(18, 16, 18, 16)

        # --- Encabezado compacto (sin ícono de advertencia) ---
        header = QLabel(f"{len(self.productos)} producto(s) con stock bajo")
        header.setStyleSheet("""
            font-size: 13pt;
            font-weight: 700;
            color: #c53030;
            padding: 8px 12px;
            background-color: #fff5f0;
            border-left: 4px solid #c53030;
            border-radius: 4px;
        """)
        layout.addWidget(header)

        # Sub-texto compacto
        sub = QLabel(
            "El monitor automático encontró productos por debajo del stock mínimo. "
            "Autorice un pedido o elija una opción de posponer."
        )
        sub.setStyleSheet("font-size: 9pt; color: #718096;")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # --- Tabla sin selección de filas ---
        self._tabla = QTableWidget()
        self._tabla.setColumnCount(4)
        self._tabla.setHorizontalHeaderLabels(["Producto", "Stock", "Mínimo", "Proveedor"])
        self._tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabla.setSelectionMode(QTableWidget.NoSelection)   # Sin selección
        self._tabla.setFocusPolicy(Qt.NoFocus)                   # Sin borde de foco
        self._tabla.verticalHeader().setVisible(False)

        hh = self._tabla.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in [1, 2, 3]:
            hh.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self._tabla.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: #ffffff;
                gridline-color: #f0f4f8;
                outline: 0;
            }
            QTableWidget::item {
                padding: 4px 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: transparent;
                color: inherit;
            }
            QHeaderView::section {
                background-color: #f7fafc;
                padding: 6px 8px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: 600;
                font-size: 9pt;
                color: #4a5568;
            }
        """)

        self._llenar_tabla()
        # Ajustar altura de tabla dinámicamente
        row_h = self._tabla.rowHeight(0) if self._tabla.rowCount() else 24
        header_h = self._tabla.horizontalHeader().height()
        self._tabla.setMaximumHeight(header_h + row_h * self._tabla.rowCount() + 4)
        layout.addWidget(self._tabla)

        # --- Botones (3 opciones) ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addStretch()

        btn_ignorar_dia = QPushButton("Ignorar durante el día")
        btn_ignorar_dia.setStyleSheet("""
            QPushButton {
                color: #718096;
                background-color: #f7fafc;
                border: 1px solid #cbd5e0;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #edf2f7;
                color: #4a5568;
                border-color: #a0aec0;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
        """)
        btn_ignorar_dia.clicked.connect(self._ignorar_dia)
        btn_layout.addWidget(btn_ignorar_dia)

        btn_recordar = QPushButton("Recordar más tarde")
        btn_recordar.setStyleSheet("""
            QPushButton {
                color: #4a5568;
                background-color: #ffffff;
                border: 1px solid #cc785c;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 9pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #fff5f0;
                color: #cc785c;
                border-color: #b5634a;
            }
            QPushButton:pressed {
                background-color: #fee2d5;
            }
        """)
        btn_recordar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_recordar)

        btn_autorizar = QPushButton("Autorizar Pedido")
        btn_autorizar.setStyleSheet("""
            QPushButton {
                background-color: #cc785c;
                color: white;
                font-weight: 700;
                padding: 8px 18px;
                border-radius: 6px;
                font-size: 9pt;
                border: none;
            }
            QPushButton:hover {
                background-color: #b5634a;
            }
            QPushButton:pressed {
                background-color: #9e5040;
            }
        """)
        btn_autorizar.clicked.connect(self._autorizar)
        btn_layout.addWidget(btn_autorizar)

        layout.addLayout(btn_layout)


    def _llenar_tabla(self):
        """Rellena la tabla con los productos afectados."""
        try:
            from app.infrastructure.proveedor_repository import ProveedorRepository
            prov_repo = ProveedorRepository()
        except Exception:
            prov_repo = None

        self._tabla.setRowCount(0)
        for producto in self.productos:
            row = self._tabla.rowCount()
            self._tabla.insertRow(row)

            # Nombre
            nombre_item = QTableWidgetItem(producto.nombre)
            nombre_item.setFlags(Qt.ItemIsEnabled)   # No seleccionable
            self._tabla.setItem(row, 0, nombre_item)

            # Stock actual (fondo rojo suave)
            stock_item = QTableWidgetItem(str(producto.stock))
            stock_item.setTextAlignment(Qt.AlignCenter)
            stock_item.setBackground(QColor("#fed7d7"))
            stock_item.setForeground(QColor("#c53030"))
            stock_item.setFlags(Qt.ItemIsEnabled)
            self._tabla.setItem(row, 1, stock_item)

            # Mínimo
            min_item = QTableWidgetItem(str(producto.stock_minimo))
            min_item.setTextAlignment(Qt.AlignCenter)
            min_item.setFlags(Qt.ItemIsEnabled)
            self._tabla.setItem(row, 2, min_item)

            # Proveedor
            proveedor_nombre = "sin asignar"
            if prov_repo:
                try:
                    prov = prov_repo.get_proveedor_de_producto(producto.id)
                    if prov:
                        proveedor_nombre = prov.nombre
                except Exception:
                    pass
            prov_item = QTableWidgetItem(proveedor_nombre)
            prov_item.setFlags(Qt.ItemIsEnabled)
            self._tabla.setItem(row, 3, prov_item)

    def _ignorar_dia(self):
        """Marca todos los productos como 'ignorados hoy' y cierra."""
        hoy = date.today()
        for p in self.productos:
            _ignorados_hoy[p.id] = hoy
        logger.info(
            f"Alertas ignoradas durante el día {hoy} para "
            f"{len(self.productos)} productos"
        )
        self.done(self.IGNORAR_DIA_CODE)

    def _autorizar(self):
        """Crea el pedido en la BD y cierra con Accept."""
        try:
            from app.infrastructure.pedidos_repository import PedidosRepository
            from app.infrastructure.proveedor_repository import ProveedorRepository

            prov_repo = ProveedorRepository()
            proveedor = None
            if self.productos:
                proveedor = prov_repo.get_proveedor_de_producto(self.productos[0].id)

            cantidades = {
                p.id: max(p.stock_minimo - p.stock, p.stock_minimo)
                for p in self.productos
            }

            self._pedido_creado = PedidosRepository().crear_pedido(
                proveedor_id=proveedor.id if proveedor else None,
                proveedor_nombre=proveedor.nombre if proveedor else None,
                productos_seleccionados=self.productos,
                cantidades=cantidades,
                created_by=self.authenticated_user,
                notas="Pedido generado automáticamente por monitor de stock",
            )

            logger.info(
                f"Pedido #{self._pedido_creado.id} autorizado por "
                f"{self.authenticated_user} ({len(self.productos)} productos)"
            )
            self.accept()

        except Exception as e:
            logger.error(f"Error al autorizar pedido: {e}")
            QMessageBox.critical(
                self, "Error",
                f"No se pudo registrar el pedido:\n{str(e)}"
            )

    def get_pedido_creado(self):
        return self._pedido_creado


def productos_ignorados_hoy(productos: list) -> list:
    """Filtra la lista de productos quitando los ignorados 'durante el día'."""
    hoy = date.today()
    return [p for p in productos if _ignorados_hoy.get(p.id) != hoy]


__all__ = ["AlertaAutorizacionDialog", "productos_ignorados_hoy"]
