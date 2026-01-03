"""
Vista de gestión de inventario.
Permite ver, agregar, editar y eliminar productos.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QComboBox, QMessageBox,
    QDialog, QFormLayout, QDoubleSpinBox, QSpinBox, QTextEdit, QGroupBox,
    QFileDialog, QProgressDialog, QMenu, QAction, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from decimal import Decimal
import logging

from app.infrastructure.product_repository import ProductRepository, CategoriaRepository
from app.domain.producto import Producto
from app.domain.categoria import Categoria
from app.services.excel_importer import ExcelImporter

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
        self.productos_actuales = []  # Para manejar filtros correctamente
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

        # Filtro de stock bajo (Menú)
        self.stock_bajo_btn = QPushButton("Stock Bajo")
        self.stock_bajo_btn.setObjectName("stockBajoButton")
        self.setup_stock_bajo_menu()
        layout.addWidget(self.stock_bajo_btn)

        return layout

    def create_action_buttons(self):
        """Crea los botones de acción"""
        layout = QHBoxLayout()

        # Botón agregar
        self.btn_agregar = QPushButton("Agregar Producto")
        self.btn_agregar.setObjectName("successButton")
        self.btn_agregar.clicked.connect(self.agregar_producto)
        layout.addWidget(self.btn_agregar)

        # Botón editar
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setObjectName("primaryButton")
        self.btn_editar.clicked.connect(self.editar_producto)
        self.btn_editar.setEnabled(False)
        layout.addWidget(self.btn_editar)

        # Botón eliminar
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setObjectName("dangerButton")
        self.btn_eliminar.clicked.connect(self.eliminar_producto)
        self.btn_eliminar.setEnabled(False)
        layout.addWidget(self.btn_eliminar)

        # Separador
        layout.addStretch()

        # Botón importar Excel
        self.btn_importar = QPushButton("Importar Excel")
        self.btn_importar.clicked.connect(self.importar_excel)
        self.btn_importar.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        layout.addWidget(self.btn_importar)

        # Botón refrescar
        self.btn_refrescar = QPushButton("Refrescar")
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
        table.verticalHeader().setVisible(False)

        # Ajuste de columnas
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Nombre ajustable
        table.setColumnWidth(1, 280) # Ancho inicial razonable
        header.setSectionResizeMode(7, QHeaderView.Stretch)      # Marca se estira
        header.setStretchLastSection(False)

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

            self.status_label.setText(f" {len(self.productos)} productos cargados")
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

        self.productos_actuales = productos
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

        # En la header de la tabla ya se configuró el auto-ajuste
        # self.table.resizeColumnsToContents() # Eliminado para evitar smashed columns iniciales

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
                productos = self.producto_repo.get_low_stock() # Usamos el método correcto del repo
                self.actualizar_tabla(productos)
                self.status_label.setText(f" ⚠️ {len(productos)} producto(s) con stock bajo")
            except Exception as e:
                logger.error(f"Error al filtrar stock bajo: {e}")
        else:
            self.actualizar_tabla()

    def setup_stock_bajo_menu(self):
        """Configura el menú desplegable del botón Stock Bajo"""
        menu = QMenu(self)

        # Acción: Ver productos en stock bajo (filtro)
        self.action_ver_stock_bajo = QAction("Ver Productos con Stock Bajo", self)
        self.action_ver_stock_bajo.setCheckable(True)
        self.action_ver_stock_bajo.triggered.connect(lambda: self.filtrar_stock_bajo(self.action_ver_stock_bajo.isChecked()))
        menu.addAction(self.action_ver_stock_bajo)

        menu.addSeparator()

        # Acción: Configurar stock mínimo global
        action_global = QAction("Configurar Stock Mínimo (Todos...)", self)
        action_global.triggered.connect(self.configurar_stock_global)
        menu.addAction(action_global)

        # Acción: Configurar stock mínimo para producto seleccionado
        self.action_individual = QAction("Configurar Stock Mínimo (Seleccionado...)", self)
        self.action_individual.triggered.connect(self.configurar_stock_especifico)
        self.action_individual.setEnabled(False)
        menu.addAction(self.action_individual)

        self.stock_bajo_btn.setMenu(menu)

    def configurar_stock_global(self):
        """Abre un diálogo para configurar el stock mínimo de todos los productos"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurar Stock Mínimo Global")
        layout = QVBoxLayout(dialog)

        label = QLabel("Establecer el mismo stock mínimo para\nTODOS los productos del inventario:")
        label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(label)

        spin = QSpinBox()
        spin.setRange(0, 9999)
        spin.setValue(10)
        spin.setFixedWidth(100)
        layout.addWidget(spin, alignment=Qt.AlignCenter)

        layout.addSpacing(20)

        buttons = QHBoxLayout()
        btn_ok = QPushButton("Aplicar a Todos")
        btn_ok.setObjectName("successButton")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dialog.reject)
        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)

        if dialog.exec_() == QDialog.Accepted:
            nuevo_minimo = spin.value()
            try:
                # Iterar y actualizar todos los productos
                for p in self.productos:
                    p.stock_minimo = nuevo_minimo
                    self.producto_repo.update(p)
                self.cargar_datos()
                QMessageBox.information(self, "Éxito", f"Se actualizó el stock mínimo a {nuevo_minimo} para todos los productos.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el stock global:\n{str(e)}")

    def configurar_stock_especifico(self):
        """Abre un diálogo rápido para el producto seleccionado"""
        producto = self.get_selected_producto()
        if not producto:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Stock Mínimo: {producto.nombre}")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"<b>Producto:</b> {producto.nombre}"))
        layout.addWidget(QLabel(f"<b>Stock Actual:</b> {producto.stock}"))

        layout.addSpacing(10)

        form_layout = QFormLayout()
        spin = QSpinBox()
        spin.setRange(0, 9999)
        spin.setValue(producto.stock_minimo)
        form_layout.addRow("Stock Mínimo:", spin)
        layout.addLayout(form_layout)

        layout.addSpacing(15)

        buttons = QHBoxLayout()
        btn_ok = QPushButton("Guardar")
        btn_ok.setObjectName("successButton")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dialog.reject)
        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)

        if dialog.exec_() == QDialog.Accepted:
            producto.stock_minimo = spin.value()
            try:
                self.producto_repo.update(producto)
                self.cargar_datos()
                QMessageBox.information(self, "Éxito", "Configuración guardada.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al guardar:\n{str(e)}")

    def on_selection_changed(self):
        """Maneja el cambio de selección en la tabla"""
        selected_rows = self.table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        self.btn_editar.setEnabled(has_selection)
        self.btn_eliminar.setEnabled(has_selection)

        # Habilitar acción individual en el menú de stock bajo si hay una instancia de la acción
        if hasattr(self, 'action_individual'):
            self.action_individual.setEnabled(has_selection)

    def get_selected_producto(self):
        """Obtiene el producto seleccionado"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        if row < len(self.productos_actuales):
            return self.productos_actuales[row]
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

    def importar_excel(self):
        """Importa productos desde un archivo Excel"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo Excel", "", "Archivos Excel (*.xlsx);;Todos los archivos (*.*)"
        )

        if not file_path:
            return

        try:
            importer = ExcelImporter()

            # Mostrar progreso indeterminado
            progress = QProgressDialog("Importando productos...", "Cancelar", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            # Ejecutar importación
            stats = importer.import_products(file_path)
            progress.cancel()

            mensaje = (
                f"Importación completada.\n\n"
                f"Total procesado: {stats['total']}\n"
                f"✅ Éxitos: {stats['success']} (Creados: {stats['created']}, Actualizados: {stats['updated']})\n"
                f"❌ Errores: {len(stats['errors'])}"
            )

            if stats['errors']:
                mensaje += "\n\nPrimeros errores:\n" + "\n".join(stats['errors'][:5])

            QMessageBox.information(self, "Resultado Importación", mensaje)
            self.cargar_datos()

        except Exception as e:
            logger.error(f"Error en importación: {e}")
            QMessageBox.critical(self, "Error", f"Error al importar archivo:\n{str(e)}")


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
        self.stock_min_input.setValue(5)  # Valor por defecto sugerido
        self.stock_min_input.setToolTip(
            "Stock mínimo para alertas de reabastecimiento.\n"
            "Cuando el stock llegue a este nivel, aparecerá en la pestaña 'Pedidos'."
        )
        self.stock_min_input.setStyleSheet("""
            QSpinBox {
                background-color: #fff5f0;
                border: 2px solid #cc785c;
                padding: 4px;
            }
        """)
        form_layout.addRow("Stock Mínimo*:", self.stock_min_input)

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
