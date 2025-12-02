"""
Vista de gestión de inventario.
Permite ver, agregar, editar y eliminar productos.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QComboBox, QMessageBox,
    QDialog, QFormLayout, QDoubleSpinBox, QSpinBox, QTextEdit, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from decimal import Decimal
import logging

from app.infrastructure.product_repository import ProductRepository, CategoriaRepository
from app.domain.producto import Producto
from app.domain.categoria import Categoria

logger = logging.getLogger(__name__)


class InventarioView(QWidget):
    """Vista principal de gestión de inventario"""

    # Señales
    producto_seleccionado = pyqtSignal(Producto)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.producto_repo = ProductRepository()
        self.categoria_repo = CategoriaRepository()
        self.productos = []
        self.categorias = []
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title = QLabel("Gestión de Inventario")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # Barra de búsqueda y filtros
        search_layout = self.create_search_bar()
        layout.addLayout(search_layout)

        # Botones de acción
        buttons_layout = self.create_action_buttons()
        layout.addLayout(buttons_layout)

        # Tabla de productos
        self.table = self.create_products_table()
        layout.addWidget(self.table)

        # Barra de estado
        self.status_label = QLabel("Listo")
        self.status_label.setStyleSheet("color: #a6adc8; font-size: 9pt;")
        layout.addWidget(self.status_label)

    def create_search_bar(self):
        """Crea la barra de búsqueda y filtros"""
        layout = QHBoxLayout()

        # Campo de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre, código o marca...")
        self.search_input.textChanged.connect(self.buscar_productos)
        layout.addWidget(self.search_input, stretch=3)

        # Filtro por categoría
        self.categoria_filter = QComboBox()
        self.categoria_filter.addItem("Todas las categorías", None)
        self.categoria_filter.currentIndexChanged.connect(self.filtrar_por_categoria)
        layout.addWidget(self.categoria_filter, stretch=1)

        # Filtro de stock bajo
        self.stock_bajo_btn = QPushButton("⚠️ Stock Bajo")
        self.stock_bajo_btn.setCheckable(True)
        self.stock_bajo_btn.clicked.connect(self.filtrar_stock_bajo)
        layout.addWidget(self.stock_bajo_btn)

        return layout

    def create_action_buttons(self):
        """Crea los botones de acción"""
        layout = QHBoxLayout()

        # Botón agregar
        self.btn_agregar = QPushButton("➕ Agregar Producto")
        self.btn_agregar.setObjectName("successButton")
        self.btn_agregar.clicked.connect(self.agregar_producto)
        layout.addWidget(self.btn_agregar)

        # Botón editar
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.setObjectName("primaryButton")
        self.btn_editar.clicked.connect(self.editar_producto)
        self.btn_editar.setEnabled(False)
        layout.addWidget(self.btn_editar)

        # Botón eliminar
        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.setObjectName("dangerButton")
        self.btn_eliminar.clicked.connect(self.eliminar_producto)
        self.btn_eliminar.setEnabled(False)
        layout.addWidget(self.btn_eliminar)

        layout.addStretch()

        # Botón refrescar
        self.btn_refrescar = QPushButton("🔄 Refrescar")
        self.btn_refrescar.clicked.connect(self.cargar_datos)
        layout.addWidget(self.btn_refrescar)

        return layout

    def create_products_table(self):
        """Crea la tabla de productos"""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Código", "Nombre", "Categoría", "Precio", "Stock",
            "Stock Mín.", "Unidad", "Marca"
        ])

        # Configurar tabla
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)

        # Conectar señal de selección
        table.itemSelectionChanged.connect(self.on_selection_changed)
        table.doubleClicked.connect(self.editar_producto)

        return table

    def cargar_datos(self):
        """Carga los datos desde la base de datos"""
        try:
            # Cargar categorías
            self.categorias = self.categoria_repo.get_all()
            self.actualizar_combo_categorias()

            # Cargar productos
            self.productos = self.producto_repo.get_all()
            self.actualizar_tabla()

            self.status_label.setText(f"✓ {len(self.productos)} productos cargados")
        except Exception as e:
            logger.error(f"Error al cargar datos: {e}")
            QMessageBox.critical(self, "Error", f"Error al cargar datos:\n{str(e)}")

    def actualizar_combo_categorias(self):
        """Actualiza el combo de categorías"""
        self.categoria_filter.clear()
        self.categoria_filter.addItem("Todas las categorías", None)
        for cat in self.categorias:
            self.categoria_filter.addItem(cat.nombre, cat.id)

    def actualizar_tabla(self, productos=None):
        """Actualiza la tabla con los productos"""
        if productos is None:
            productos = self.productos

        self.table.setRowCount(len(productos))

        for row, producto in enumerate(productos):
            # Código
            self.table.setItem(row, 0, QTableWidgetItem(producto.codigo or ""))

            # Nombre
            self.table.setItem(row, 1, QTableWidgetItem(producto.nombre))

            # Categoría
            self.table.setItem(row, 2, QTableWidgetItem(producto.categoria_nombre or "Sin categoría"))

            # Precio
            precio_item = QTableWidgetItem(producto.precio_formateado)
            precio_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, precio_item)

            # Stock
            stock_item = QTableWidgetItem(str(producto.stock))
            stock_item.setTextAlignment(Qt.AlignCenter)
            # Colorear si está bajo
            if producto.stock_bajo:
                stock_item.setBackground(QColor("#f38ba8"))
                stock_item.setForeground(QColor("#1e1e2e"))
            self.table.setItem(row, 4, stock_item)

            # Stock mínimo
            stock_min_item = QTableWidgetItem(str(producto.stock_minimo))
            stock_min_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, stock_min_item)

            # Unidad
            self.table.setItem(row, 6, QTableWidgetItem(producto.unidad_medida))

            # Marca
            self.table.setItem(row, 7, QTableWidgetItem(producto.marca or ""))

        # Ajustar columnas
        self.table.resizeColumnsToContents()

    def buscar_productos(self, texto):
        """Busca productos por texto"""
        if not texto.strip():
            self.actualizar_tabla()
            return

        try:
            resultados = self.producto_repo.search(texto)
            self.actualizar_tabla(resultados)
            self.status_label.setText(f"🔍 {len(resultados)} resultado(s) encontrado(s)")
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")

    def filtrar_por_categoria(self, index):
        """Filtra productos por categoría"""
        categoria_id = self.categoria_filter.currentData()

        if categoria_id is None:
            self.actualizar_tabla()
        else:
            try:
                productos = self.producto_repo.get_by_categoria(categoria_id)
                self.actualizar_tabla(productos)
                self.status_label.setText(f"📁 {len(productos)} producto(s) en esta categoría")
            except Exception as e:
                logger.error(f"Error al filtrar: {e}")

    def filtrar_stock_bajo(self, checked):
        """Filtra productos con stock bajo"""
        if checked:
            try:
                productos = self.producto_repo.get_stock_bajo()
                self.actualizar_tabla(productos)
                self.status_label.setText(f"⚠️ {len(productos)} producto(s) con stock bajo")
            except Exception as e:
                logger.error(f"Error al filtrar stock bajo: {e}")
        else:
            self.actualizar_tabla()

    def on_selection_changed(self):
        """Maneja el cambio de selección en la tabla"""
        has_selection = len(self.table.selectedItems()) > 0
        self.btn_editar.setEnabled(has_selection)
        self.btn_eliminar.setEnabled(has_selection)

    def get_selected_producto(self):
        """Obtiene el producto seleccionado"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        if row < len(self.productos):
            return self.productos[row]
        return None

    def agregar_producto(self):
        """Abre el diálogo para agregar un producto"""
        dialog = ProductoDialog(self.categorias, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                producto = dialog.get_producto()
                self.producto_repo.create(producto)
                self.cargar_datos()
                QMessageBox.information(self, "Éxito", "Producto agregado correctamente")
            except Exception as e:
                logger.error(f"Error al agregar producto: {e}")
                QMessageBox.critical(self, "Error", f"Error al agregar producto:\n{str(e)}")

    def editar_producto(self):
        """Abre el diálogo para editar el producto seleccionado"""
        producto = self.get_selected_producto()
        if not producto:
            return

        dialog = ProductoDialog(self.categorias, producto=producto, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                producto_actualizado = dialog.get_producto()
                producto_actualizado.id = producto.id
                self.producto_repo.update(producto_actualizado)
                self.cargar_datos()
                QMessageBox.information(self, "Éxito", "Producto actualizado correctamente")
            except Exception as e:
                logger.error(f"Error al actualizar producto: {e}")
                QMessageBox.critical(self, "Error", f"Error al actualizar producto:\n{str(e)}")

    def eliminar_producto(self):
        """Elimina el producto seleccionado"""
        producto = self.get_selected_producto()
        if not producto:
            return

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de eliminar el producto '{producto.nombre}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            try:
                self.producto_repo.delete(producto.id, soft_delete=True)
                self.cargar_datos()
                QMessageBox.information(self, "Éxito", "Producto eliminado correctamente")
            except Exception as e:
                logger.error(f"Error al eliminar producto: {e}")
                QMessageBox.critical(self, "Error", f"Error al eliminar producto:\n{str(e)}")


class ProductoDialog(QDialog):
    """Diálogo para agregar/editar productos"""

    def __init__(self, categorias, producto=None, parent=None):
        super().__init__(parent)
        self.categorias = categorias
        self.producto = producto
        self.is_edit = producto is not None
        self.setup_ui()

        if self.is_edit:
            self.load_producto_data()

    def setup_ui(self):
        """Configura la interfaz del diálogo"""
        self.setWindowTitle("Editar Producto" if self.is_edit else "Agregar Producto")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Formulario
        form_layout = QFormLayout()

        # Código
        self.codigo_input = QLineEdit()
        self.codigo_input.setPlaceholderText("Ej: PROD001")
        form_layout.addRow("Código:", self.codigo_input)

        # Nombre
        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Nombre del producto")
        form_layout.addRow("Nombre*:", self.nombre_input)

        # Descripción
        self.descripcion_input = QTextEdit()
        self.descripcion_input.setMaximumHeight(80)
        self.descripcion_input.setPlaceholderText("Descripción del producto")
        form_layout.addRow("Descripción:", self.descripcion_input)

        # Categoría
        self.categoria_combo = QComboBox()
        self.categoria_combo.addItem("Sin categoría", None)
        for cat in self.categorias:
            self.categoria_combo.addItem(cat.nombre, cat.id)
        form_layout.addRow("Categoría:", self.categoria_combo)

        # Precio
        self.precio_input = QDoubleSpinBox()
        self.precio_input.setRange(0, 999999.99)
        self.precio_input.setDecimals(2)
        self.precio_input.setPrefix("$ ")
        form_layout.addRow("Precio*:", self.precio_input)

        # Stock
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 999999)
        form_layout.addRow("Stock*:", self.stock_input)

        # Stock mínimo
        self.stock_min_input = QSpinBox()
        self.stock_min_input.setRange(0, 999999)
        form_layout.addRow("Stock Mínimo:", self.stock_min_input)

        # Unidad de medida
        self.unidad_input = QComboBox()
        self.unidad_input.setEditable(True)
        self.unidad_input.addItems(["unidad", "metro", "litro", "galón", "kilo", "caja", "paquete"])
        form_layout.addRow("Unidad:", self.unidad_input)

        # Marca
        self.marca_input = QLineEdit()
        self.marca_input.setPlaceholderText("Marca del producto")
        form_layout.addRow("Marca:", self.marca_input)

        # Ubicación
        self.ubicacion_input = QLineEdit()
        self.ubicacion_input.setPlaceholderText("Ej: Pasillo 3, Estante A")
        form_layout.addRow("Ubicación:", self.ubicacion_input)

        layout.addLayout(form_layout)

        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancelar)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setObjectName("primaryButton")
        self.btn_guardar.clicked.connect(self.accept)
        buttons_layout.addWidget(self.btn_guardar)

        layout.addLayout(buttons_layout)

    def load_producto_data(self):
        """Carga los datos del producto en el formulario"""
        self.codigo_input.setText(self.producto.codigo or "")
        self.nombre_input.setText(self.producto.nombre)
        self.descripcion_input.setPlainText(self.producto.descripcion or "")
        self.precio_input.setValue(float(self.producto.precio))
        self.stock_input.setValue(self.producto.stock)
        self.stock_min_input.setValue(self.producto.stock_minimo)
        self.unidad_input.setCurrentText(self.producto.unidad_medida)
        self.marca_input.setText(self.producto.marca or "")
        self.ubicacion_input.setText(self.producto.ubicacion or "")

        # Seleccionar categoría
        if self.producto.categoria_id:
            index = self.categoria_combo.findData(self.producto.categoria_id)
            if index >= 0:
                self.categoria_combo.setCurrentIndex(index)

    def get_producto(self):
        """Obtiene el producto con los datos del formulario"""
        return Producto(
            codigo=self.codigo_input.text().strip() or None,
            nombre=self.nombre_input.text().strip(),
            descripcion=self.descripcion_input.toPlainText().strip() or None,
            precio=Decimal(str(self.precio_input.value())),
            stock=self.stock_input.value(),
            stock_minimo=self.stock_min_input.value(),
            unidad_medida=self.unidad_input.currentText(),
            categoria_id=self.categoria_combo.currentData(),
            marca=self.marca_input.text().strip() or None,
            ubicacion=self.ubicacion_input.text().strip() or None,
        )
