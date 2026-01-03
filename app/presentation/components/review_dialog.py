"""
Diálogo de revisión de pedido antes de generar PDF.
Permite al usuario revisar y editar cantidades.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QSpinBox, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from typing import List, Dict
import logging

from app.domain.producto import Producto

logger = logging.getLogger(__name__)


class ReviewDialog(QDialog):
    """Diálogo para revisar pedido antes de generar PDF"""

    def __init__(self, productos: List[Producto], parent=None):
        super().__init__(parent)
        self.productos = productos
        self.cantidades_editadas = {}
        self.total_estimado = 0

        self.setup_ui()
        self.calcular_total()

    def setup_ui(self):
        """Configura la interfaz"""
        self.setWindowTitle("Revisar Pedido")
        self.setMinimumSize(800, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title = QLabel("Revisar Pedido")
        title.setStyleSheet("font-size: 20pt; font-weight: 700; color: #2d3748;")
        layout.addWidget(title)

        # Descripción
        desc = QLabel("Revisa las cantidades sugeridas. Puedes editarlas antes de generar el PDF.")
        desc.setStyleSheet("font-size: 11pt; color: #718096; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Producto", "Stock Actual",
            "Faltante", "Cantidad a Pedir", "Precio Unit.", "Subtotal"
        ])

        # Configurar tabla
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)

        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Producto
        for i in [1, 2, 3, 4, 5]:
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f7fafc;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: 600;
                color: #2d3748;
            }
        """)

        # Configurar altura de filas para que el SpinBox quepa cómodamente
        self.tabla.verticalHeader().setDefaultSectionSize(45)

        # Llenar tabla
        self.llenar_tabla()

        layout.addWidget(self.tabla)

        # Total
        self.total_label = QLabel()
        self.total_label.setStyleSheet("""
            font-size: 16pt;
            font-weight: 700;
            color: #cc785c;
            background-color: #fff5f0;
            padding: 15px;
            border-radius: 6px;
        """)
        self.total_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.total_label)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secondaryButton")
        btn_cancelar.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancelar)

        btn_generar = QPushButton("Generar PDF")
        btn_generar.setObjectName("primaryButton")
        btn_generar.clicked.connect(self.accept)
        buttons_layout.addWidget(btn_generar)

        layout.addLayout(buttons_layout)

    def llenar_tabla(self):
        """Llena la tabla con los productos"""
        self.tabla.setRowCount(0)
        self.spinboxes = {}

        for producto in self.productos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)

            faltante = producto.stock_minimo - producto.stock
            cantidad_sugerida = max(faltante, producto.stock_minimo)

            # Producto
            self.tabla.setItem(row, 0, QTableWidgetItem(producto.nombre))

            # Stock Actual
            item_stock = QTableWidgetItem(str(producto.stock))
            item_stock.setTextAlignment(Qt.AlignCenter)
            item_stock.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.tabla.setItem(row, 1, item_stock)

            # Faltante (Columna 2)
            item_faltante = QTableWidgetItem(str(faltante))
            item_faltante.setTextAlignment(Qt.AlignCenter)
            item_faltante.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.tabla.setItem(row, 2, item_faltante)

            # Cantidad a Pedir (SpinBox editable) (Columna 3)
            spinbox = QSpinBox()
            spinbox.setMinimum(1)
            spinbox.setMaximum(9999)
            spinbox.setValue(cantidad_sugerida)
            spinbox.setAlignment(Qt.AlignCenter)
            # Tamaño ajustado para caber en la columna
            spinbox.setFixedWidth(65)
            spinbox.setFixedHeight(28)
            spinbox.setStyleSheet("""
                QSpinBox {
                    font-size: 11pt;
                    padding: 2px 4px;
                    padding-right: 18px;
                }
            """)
            spinbox.valueChanged.connect(lambda v, p=producto: self.on_cantidad_changed(p, v))
            self.tabla.setCellWidget(row, 3, spinbox)
            self.spinboxes[producto.id] = spinbox

            # Precio Unitario (Columna 4)
            item_precio = QTableWidgetItem(f"${producto.precio:.2f}")
            item_precio.setTextAlignment(Qt.AlignCenter)
            self.tabla.setItem(row, 4, item_precio)

            # Subtotal (Columna 5)
            subtotal = float(producto.precio) * cantidad_sugerida
            item_subtotal = QTableWidgetItem(f"${subtotal:.2f}")
            item_subtotal.setTextAlignment(Qt.AlignCenter)
            self.tabla.setItem(row, 5, item_subtotal)

    def on_cantidad_changed(self, producto: Producto, nueva_cantidad: int):
        """Maneja cambio de cantidad"""
        self.cantidades_editadas[producto.id] = nueva_cantidad
        self.calcular_total()

        # Actualizar subtotal en la tabla
        for row in range(self.tabla.rowCount()):
            item_nombre = self.tabla.item(row, 0)
            if item_nombre and item_nombre.text() == producto.nombre:
                subtotal = float(producto.precio) * nueva_cantidad
                self.tabla.item(row, 6).setText(f"${subtotal:.2f}")
                break

    def calcular_total(self):
        """Calcula el total estimado"""
        total = 0
        for producto in self.productos:
            if producto.id in self.cantidades_editadas:
                cantidad = self.cantidades_editadas[producto.id]
            else:
                faltante = producto.stock_minimo - producto.stock
                cantidad = max(faltante, producto.stock_minimo)

            total += float(producto.precio) * cantidad

        self.total_estimado = total
        self.total_label.setText(f"TOTAL ESTIMADO: ${total:.2f}")

    def get_cantidades_editadas(self) -> Dict[int, int]:
        """Retorna las cantidades editadas"""
        # Asegurar que todas las cantidades estén en el diccionario
        for producto in self.productos:
            if producto.id not in self.cantidades_editadas:
                spinbox = self.spinboxes.get(producto.id)
                if spinbox:
                    self.cantidades_editadas[producto.id] = spinbox.value()

        return self.cantidades_editadas
