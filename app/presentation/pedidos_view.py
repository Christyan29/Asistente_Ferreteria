"""
Vista de Pedidos - Productos con Stock Bajo
Muestra productos que necesitan reabastecimiento y permite generar pedidos en PDF
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import logging

from app.infrastructure.product_repository import ProductRepository
from app.services.pdf_generator import PDFGenerator
from app.presentation.components.review_dialog import ReviewDialog

logger = logging.getLogger(__name__)


class PedidosView(QWidget):
    """Vista para gestionar pedidos de productos con stock bajo"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.producto_repo = ProductRepository()
        self.pdf_generator = PDFGenerator()
        self.productos_bajo_stock = []

        self.setup_ui()
        self.cargar_productos()

    def setup_ui(self):
        """Configura la interfaz"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Productos con Stock Bajo")
        title.setStyleSheet("font-size: 24pt; font-weight: 700; color: #2d3748;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Contador
        self.contador_label = QLabel("0 productos")
        self.contador_label.setStyleSheet("""
            font-size: 14pt;
            color: #cc785c;
            font-weight: 600;
            background-color: #fff5f0;
            padding: 8px 16px;
            border-radius: 6px;
        """)
        header_layout.addWidget(self.contador_label)

        layout.addLayout(header_layout)

        # Descripción
        desc = QLabel("Genera pedidos en PDF para productos que necesitan reabastecimiento")
        desc.setStyleSheet("font-size: 11pt; color: #718096; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "Seleccionar", "Código", "Producto", "Categoría", "Stock Actual",
            "Faltante", "Unidad", "Marca", "Precio"
        ])

        # Configurar tabla
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)

        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Producto
        for i in [0, 1, 3, 4, 5, 6, 7, 8]:
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
            QTableWidget::item:selected {
                background-color: #fff5f0;
                color: #2d3748;
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

        layout.addWidget(self.tabla)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.btn_refrescar = QPushButton("Refrescar")
        self.btn_refrescar.setObjectName("secondaryButton")
        self.btn_refrescar.clicked.connect(self.cargar_productos)
        buttons_layout.addWidget(self.btn_refrescar)

        self.btn_generar = QPushButton("Generar Pedido PDF")
        self.btn_generar.setObjectName("primaryButton")
        self.btn_generar.clicked.connect(self.generar_pedido)
        buttons_layout.addWidget(self.btn_generar)

        layout.addLayout(buttons_layout)

    def cargar_productos(self):
        """Carga productos con stock bajo"""
        try:
            logger.info("Cargando productos con stock bajo...")
            self.productos_bajo_stock = self.producto_repo.get_low_stock()

            self.tabla.setRowCount(0)

            for producto in self.productos_bajo_stock:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)

                faltante = producto.stock_minimo - producto.stock

                # Checkbox para seleccionar
                checkbox = QTableWidgetItem()
                checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox.setCheckState(Qt.Checked)  # Seleccionado por defecto
                self.tabla.setItem(row, 0, checkbox)

                # Código
                self.tabla.setItem(row, 1, QTableWidgetItem(producto.codigo or ""))

                # Producto
                item_nombre = QTableWidgetItem(producto.nombre)
                item_nombre.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.tabla.setItem(row, 2, item_nombre)

                # Categoría
                item_cat = QTableWidgetItem(producto.categoria_nombre or "")
                item_cat.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.tabla.setItem(row, 3, item_cat)

                # Stock Actual (con color)
                item_stock = QTableWidgetItem(str(producto.stock))
                item_stock.setTextAlignment(Qt.AlignCenter)
                item_stock.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                if producto.stock == 0:
                    item_stock.setBackground(QColor("#fee"))
                    item_stock.setForeground(QColor("#c00"))
                elif producto.stock <= producto.stock_minimo / 2:
                    item_stock.setBackground(QColor("#fff3cd"))
                self.tabla.setItem(row, 4, item_stock)

                # Faltante (Columna 5)
                item_faltante = QTableWidgetItem(str(faltante))
                item_faltante.setTextAlignment(Qt.AlignCenter)
                item_faltante.setForeground(QColor("#cc785c"))
                item_faltante.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                f = item_faltante.font()
                f.setBold(True)
                item_faltante.setFont(f)
                self.tabla.setItem(row, 5, item_faltante)

                # Unidad (Columna 6)
                self.tabla.setItem(row, 6, QTableWidgetItem(producto.unidad_medida or "unidad"))

                # Marca (Columna 7)
                self.tabla.setItem(row, 7, QTableWidgetItem(producto.marca or ""))

                # Precio (Columna 8)
                item_precio = QTableWidgetItem(f"${producto.precio:.2f}")
                item_precio.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla.setItem(row, 8, item_precio)

            # Actualizar contador
            self.contador_label.setText(f"{len(self.productos_bajo_stock)} productos")

            # Habilitar/deshabilitar botón generar
            self.btn_generar.setEnabled(len(self.productos_bajo_stock) > 0)

            logger.info(f"Cargados {len(self.productos_bajo_stock)} productos con stock bajo")

        except Exception as e:
            logger.error(f"Error al cargar productos: {e}")
            QMessageBox.critical(self, "Error", f"Error al cargar productos:\n{str(e)}")

    def generar_pedido(self):
        """Genera pedido en PDF con diálogo de revisión"""
        if not self.productos_bajo_stock:
            QMessageBox.warning(self, "Advertencia", "No hay productos para generar pedido")
            return

        try:
            # Filtrar solo productos seleccionados
            productos_seleccionados = []
            for row in range(self.tabla.rowCount()):
                checkbox = self.tabla.item(row, 0)
                if checkbox and checkbox.checkState() == Qt.Checked:
                    # Obtener el producto correspondiente
                    producto = self.productos_bajo_stock[row]
                    productos_seleccionados.append(producto)

            if not productos_seleccionados:
                QMessageBox.warning(self, "Advertencia", "Selecciona al menos un producto para generar el pedido")
                return

            # Mostrar diálogo de revisión
            dialog = ReviewDialog(productos_seleccionados, self)

            if dialog.exec_() == dialog.Accepted:
                # Obtener cantidades editadas
                cantidades = dialog.get_cantidades_editadas()

                # Generar PDF
                filepath = self.pdf_generator.generar_pedido(productos_seleccionados, cantidades)

                if filepath:
                    # Preguntar si abrir
                    respuesta = QMessageBox.question(
                        self,
                        "PDF Generado",
                        f"Pedido generado exitosamente:\n{filepath}\n\n¿Desea abrir el archivo?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )

                    if respuesta == QMessageBox.Yes:
                        self.pdf_generator.abrir_archivo(filepath)

                    logger.info(f"Pedido PDF generado: {filepath}")

        except Exception as e:
            logger.error(f"Error al generar pedido: {e}")
            QMessageBox.critical(self, "Error", f"Error al generar pedido:\n{str(e)}")
