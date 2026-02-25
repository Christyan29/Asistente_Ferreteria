"""
Vista de gestión de inventario.
Permite ver, agregar, editar y eliminar productos.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QComboBox, QMessageBox,
    QDialog, QFormLayout, QDoubleSpinBox, QSpinBox, QTextEdit, QGroupBox,
    QFileDialog, QProgressDialog, QMenu, QAction, QHeaderView,
    QFrame, QScrollArea   # ✅ NUEVO: panel colapsable
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from decimal import Decimal
import logging

from app.infrastructure.product_repository import ProductRepository, CategoriaRepository
from app.domain.producto import Producto
from app.domain.categoria import Categoria
from app.services.excel_importer import ExcelImporter
from app.infrastructure.proveedor_repository import ProveedorRepository  # ✅ NUEVO

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

        # Título + botón alertas en misma fila
        title_row = QHBoxLayout()
        title = QLabel("Gestión de Inventario")
        title.setObjectName("titleLabel")
        title_row.addWidget(title)
        title_row.addStretch()

        # ✅ NUEVO: botón para desplegar/colapsar panel de alertas
        self._btn_alertas = QPushButton("⚠ Alertas (0)")
        self._btn_alertas.setCheckable(True)
        self._btn_alertas.setChecked(False)
        self._btn_alertas.setFixedWidth(130)
        self._btn_alertas.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: #a0aec0;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 9pt;
                font-weight: 600;
            }
            QPushButton:checked {
                background-color: #c53030;
                color: white;
            }
        """)
        self._btn_alertas.clicked.connect(self.toggle_panel_alertas)
        title_row.addWidget(self._btn_alertas)
        layout.addLayout(title_row)

        # Barra de búsqueda y filtros
        search_layout = self.create_search_bar()
        layout.addLayout(search_layout)

        # Botones de acción
        buttons_layout = self.create_action_buttons()
        layout.addLayout(buttons_layout)

        # Contenedor horizontal: tabla + panel alertas
        self._content_row = QHBoxLayout()
        self._content_row.setSpacing(10)

        # Tabla de productos
        self.table = self.create_products_table()
        self._content_row.addWidget(self.table, stretch=3)

        # ✅ NUEVO: Panel lateral de alertas (oculto por defecto)
        self._panel_alertas = self._crear_panel_alertas()
        self._panel_alertas.setVisible(False)
        self._content_row.addWidget(self._panel_alertas, stretch=1)

        layout.addLayout(self._content_row)

        # Barra de estado
        self.status_label = QLabel("Listo")
        self.status_label.setStyleSheet("color: #a6adc8; font-size: 9pt;")
        layout.addWidget(self.status_label)

    def create_search_bar(self):
        """Crea la barra de búsqueda y filtros"""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        # Campo de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre, código o marca...")
        self.search_input.setMinimumHeight(40)
        self.search_input.textChanged.connect(self.buscar_productos)
        layout.addWidget(self.search_input, stretch=4)

        # Estilo unificado para desplegables (con flechitas)
        combo_style = """
            QComboBox, QPushButton#stockBajoButton {
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 5px 15px;
                background-color: white;
                min-height: 32px;
                text-align: left;
            }
            QComboBox:hover, QPushButton#stockBajoButton:hover {
                border: 1px solid #cc785c;
                background-color: #fffaf9;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;            /* Triángulo ▼ */
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                width: 0;
                height: 0;
                margin-right: 15px;
            }
            QPushButton#stockBajoButton::menu-indicator {
                image: none;
                border-left: 5px solid transparent;            /* Triángulo ▼ */
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                width: 0;
                height: 0;
                subcontrol-origin: padding;
                subcontrol-position: center right;
                right: 15px;
            }
        """

        # Filtro por categoría
        self.categoria_filter = QComboBox()
        self.categoria_filter.addItem("Todas las categorías", None)
        self.categoria_filter.setStyleSheet(combo_style)
        self.categoria_filter.currentIndexChanged.connect(self.filtrar_por_categoria)
        layout.addWidget(self.categoria_filter, stretch=1)

        # Filtro de stock bajo (Botón con Menú)
        self.stock_bajo_btn = QPushButton("Stock Bajo")
        self.stock_bajo_btn.setObjectName("stockBajoButton")
        self.stock_bajo_btn.setMinimumHeight(40)
        self.stock_bajo_btn.setStyleSheet(combo_style)
        self.setup_stock_bajo_menu()
        layout.addWidget(self.stock_bajo_btn, stretch=1)

        return layout

    def create_action_buttons(self):
        """Crea los botones de acción"""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        # Botones principales (Izquierda)
        self.btn_agregar = QPushButton("Agregar Producto")
        self.btn_agregar.setObjectName("successButton")
        self.btn_agregar.setMinimumHeight(38)
        self.btn_agregar.clicked.connect(self.agregar_producto)
        layout.addWidget(self.btn_agregar)

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setObjectName("primaryButton")
        self.btn_editar.setMinimumHeight(38)
        self.btn_editar.clicked.connect(self.editar_producto)
        self.btn_editar.setEnabled(False)
        layout.addWidget(self.btn_editar)

        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setObjectName("dangerButton")
        self.btn_eliminar.setMinimumHeight(38)
        self.btn_eliminar.clicked.connect(self.eliminar_producto)
        self.btn_eliminar.setEnabled(False)
        layout.addWidget(self.btn_eliminar)

        # Espaciador central
        layout.addStretch()

        # Botones de mantenimiento (Derecha)
        self.btn_importar = QPushButton("Importar Excel")
        self.btn_importar.setMinimumHeight(38)
        self.btn_importar.setFixedWidth(130)
        self.btn_importar.clicked.connect(self.importar_excel)
        self.btn_importar.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #444;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
            }
        """)
        layout.addWidget(self.btn_importar)

        self.btn_refrescar = QPushButton("Refrescar")
        self.btn_refrescar.setMinimumHeight(38)
        self.btn_refrescar.setFixedWidth(110)
        self.btn_refrescar.clicked.connect(self.cargar_datos)
        self.btn_refrescar.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #666;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #f1f3f5;
            }
        """)
        layout.addWidget(self.btn_refrescar)

        return layout

    def create_products_table(self):
        """Crea la tabla de productos"""
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "Seleccionar", "Código", "Nombre", "Categoría", "Precio", "Stock",
            "Stock Mín.", "Unidad", "Marca"
        ])

        # Configurar tabla
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)

        # Ajuste de columnas y estilos
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        # Selección Centrada
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        table.setColumnWidth(0, 100)

        # Distribución Proporcional
        header.setSectionResizeMode(2, QHeaderView.Stretch)      # Nombre se expande más
        header.setSectionResizeMode(8, QHeaderView.Stretch)      # Marca se expande
        header.setStretchLastSection(False)

        # CSS para centrar checkboxes
        table.setStyleSheet("""
            QTableWidget::indicator {
                subcontrol-origin: padding;
                subcontrol-position: center;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)

        # Conectar señales
        table.itemSelectionChanged.connect(self.on_selection_changed)
        table.doubleClicked.connect(self.editar_producto)
        table.itemChanged.connect(self.on_item_changed)

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
            # Checkbox de selección
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_item.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 0, chk_item)

            # Código
            self.table.setItem(row, 1, QTableWidgetItem(producto.codigo or ""))

            # Nombre
            self.table.setItem(row, 2, QTableWidgetItem(producto.nombre))

            # Categoría
            self.table.setItem(row, 3, QTableWidgetItem(producto.categoria_nombre or "Sin categoría"))

            # Precio
            precio_item = QTableWidgetItem(producto.precio_formateado)
            precio_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, precio_item)

            # Stock
            stock_item = QTableWidgetItem(str(producto.stock))
            stock_item.setTextAlignment(Qt.AlignCenter)
            # Colorear si está bajo
            if producto.stock_bajo:
                stock_item.setBackground(QColor("#f38ba8"))
                stock_item.setForeground(QColor("#1e1e2e"))
            self.table.setItem(row, 5, stock_item)

            # Stock mínimo
            stock_min_item = QTableWidgetItem(str(producto.stock_minimo))
            stock_min_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, stock_min_item)

            # Unidad
            self.table.setItem(row, 7, QTableWidgetItem(producto.unidad_medida))

            # Marca
            self.table.setItem(row, 8, QTableWidgetItem(producto.marca or ""))

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
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 10px 30px 10px 15px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #fff2ed;
                color: #cc785c;
            }
        """)

        # Acción: Ver productos en stock bajo (filtro)
        self.action_ver_stock_bajo = QAction("Ver productos con bajo stock", self)
        self.action_ver_stock_bajo.setCheckable(True)
        self.action_ver_stock_bajo.triggered.connect(lambda: self.filtrar_stock_bajo(self.action_ver_stock_bajo.isChecked()))
        menu.addAction(self.action_ver_stock_bajo)

        menu.addSeparator()

        # Acción: Configurar stock mínimo global
        action_global = QAction("Fijar stock mínimo a todos", self)
        action_global.triggered.connect(self.configurar_stock_global)
        menu.addAction(action_global)

        # Acción: Configurar stock mínimo para producto seleccionado
        self.action_individual = QAction("Fijar stock mínimo a este producto", self)
        self.action_individual.triggered.connect(self.configurar_stock_especifico)
        self.action_individual.setEnabled(True)
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
            QMessageBox.warning(
                self,
                "Sin Selección",
                "Por favor, selecciona primero un producto de la tabla para ajustar su stock mínimo."
            )
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

    def on_item_changed(self, item):
        """Maneja el cambio en una celda (para los checkboxes de selección única)"""
        if item.column() == 0:
            if item.checkState() == Qt.Checked:
                # Desmarcar los demás
                self.table.blockSignals(True)
                for row in range(self.table.rowCount()):
                    if row != item.row():
                        other_item = self.table.item(row, 0)
                        if other_item:
                            other_item.setCheckState(Qt.Unchecked)
                self.table.blockSignals(False)

            # Actualizar estado de botones basado en si hay algún checkbox marcado
            hay_marcado = False
            for row in range(self.table.rowCount()):
                check_item = self.table.item(row, 0)
                if check_item and check_item.checkState() == Qt.Checked:
                    hay_marcado = True
                    break

            # Podríamos habilitar/deshabilitar botones aquí si fuera necesario
            pass

    def get_selected_producto(self):
        """Obtiene el producto seleccionado mediante el checkbox"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                if row < len(self.productos_actuales):
                    return self.productos_actuales[row]

        # Fallback para botones Editar/Eliminar si usan la selección estándar de fila
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
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
                producto_creado = self.producto_repo.create(producto)
                # ✅ NUEVO: guardar relación con proveedor si se seleccionó uno
                proveedor_id = dialog.get_proveedor_id_seleccionado()
                if proveedor_id and producto_creado.id:
                    try:
                        from app.infrastructure.proveedor_repository import ProveedorRepository
                        prov_repo = ProveedorRepository()
                        prov_repo.asignar_proveedor_a_producto(producto_creado.id, proveedor_id)
                    except Exception as pe:
                        logger.warning(f"No se pudo asignar proveedor al producto: {pe}")
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
                # ✅ NUEVO: actualizar relación con proveedor
                proveedor_id = dialog.get_proveedor_id_seleccionado()
                try:
                    from app.infrastructure.proveedor_repository import ProveedorRepository
                    prov_repo = ProveedorRepository()
                    if proveedor_id:
                        prov_repo.asignar_proveedor_a_producto(producto.id, proveedor_id)
                    else:
                        prov_repo.remover_proveedor_de_producto(producto.id)
                except Exception as pe:
                    logger.warning(f"No se pudo actualizar proveedor del producto: {pe}")
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
    # =========================================================================
    # ✅ Panel lateral colapsable de Notificaciones de stock
    # =========================================================================

    def _crear_panel_alertas(self) -> QFrame:
        """Construye el widget del panel lateral (oculto por defecto)."""
        panel = QFrame()
        panel.setObjectName("panelAlertas")
        panel.setMinimumWidth(240)
        panel.setMaximumWidth(270)
        panel.setStyleSheet("""
            QFrame#panelAlertas {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)

        v = QVBoxLayout(panel)
        v.setSpacing(8)
        v.setContentsMargins(10, 10, 10, 10)

        # Encabezado: título + botón Limpiar
        header_row = QHBoxLayout()
        header_lbl = QLabel("Notificaciones")
        header_lbl.setStyleSheet(
            "color: #c53030; font-size: 10pt; font-weight: 700;"
        )
        header_row.addWidget(header_lbl)
        header_row.addStretch()

        self._btn_limpiar = QPushButton("Limpiar")
        self._btn_limpiar.setFixedHeight(22)
        self._btn_limpiar.setStyleSheet("""
            QPushButton {
                color: #a0aec0;
                background: transparent;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 8pt;
            }
            QPushButton:hover {
                background-color: #f7fafc;
                color: #4a5568;
                border-color: #cbd5e0;
            }
        """)
        self._btn_limpiar.clicked.connect(self._limpiar_panel)
        header_row.addWidget(self._btn_limpiar)
        v.addLayout(header_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #e2e8f0; max-height: 1px;")
        v.addWidget(sep)

        # Área scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #f7fafc; width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e0; border-radius: 3px;
            }
        """)

        self._alertas_container = QWidget()
        self._alertas_container.setStyleSheet("background: transparent;")
        self._alertas_layout = QVBoxLayout(self._alertas_container)
        self._alertas_layout.setSpacing(8)     # ✅ más espacio entre tarjetas
        self._alertas_layout.setContentsMargins(2, 4, 2, 4)
        self._alertas_layout.addStretch()

        scroll.setWidget(self._alertas_container)
        v.addWidget(scroll)

        hint = QLabel("Clic en un producto para actuar")
        hint.setStyleSheet(
            "color: #a0aec0; font-size: 8pt; padding-top: 4px;"
        )
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        v.addWidget(hint)

        self._productos_alerta_actual = []
        return panel

    def actualizar_panel_alertas(self, productos: list) -> None:
        """
        Refresca el contenido del panel con los productos con stock bajo.
        Cada tarjeta es clickeable y abre el diálogo de autorización.
        """
        # Guardar lista actual para uso en clics
        self._productos_alerta_actual = list(productos)

        # Limpiar items existentes (excepto stretch final)
        while self._alertas_layout.count() > 1:
            item = self._alertas_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not productos:
            empty = QLabel("Sin notificaciones")
            empty.setStyleSheet("color: #a0aec0; font-size: 9pt;")
            empty.setAlignment(Qt.AlignCenter)
            self._alertas_layout.insertWidget(0, empty)
            self._btn_alertas.setText("Notificaciones (0)")
            self._btn_alertas.setChecked(False)
            self._panel_alertas.setVisible(False)
            return

        n = len(productos)
        self._btn_alertas.setText(f"Notificaciones ({n})")

        for i, producto in enumerate(productos):
            faltante = max(0, producto.stock_minimo - producto.stock)

            # Tarjeta como QPushButton clickeable
            card = QPushButton()
            card.setCursor(Qt.PointingHandCursor)
            card.setFixedHeight(60)   # ✅ altura fija para que no se amontonen
            card.setStyleSheet("""
                QPushButton {
                    background-color: #fff5f0;
                    border: 1px solid #fed7d7;
                    border-left: 3px solid #c53030;
                    border-radius: 5px;
                    padding: 8px 10px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #fee2e2;
                    border-color: #c53030;
                }
            """)

            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(2)
            card_layout.setContentsMargins(4, 4, 4, 4)

            name_lbl = QLabel(producto.nombre)
            name_lbl.setStyleSheet(
                "color: #2d3748; font-size: 9pt; font-weight: 600;"
                "background: transparent; border: none;"
            )
            name_lbl.setWordWrap(True)
            card_layout.addWidget(name_lbl)

            stock_lbl = QLabel(
                f"Stock: {producto.stock} \u2022 Mín: {producto.stock_minimo} "
                f"(faltan {faltante})"
            )
            stock_lbl.setStyleSheet(
                "color: #c53030; font-size: 8pt; background: transparent; border: none;"
            )
            card_layout.addWidget(stock_lbl)

            # Conectar clic — abre el diálogo con TODOS los productos actuales
            card.clicked.connect(self._abrir_autorizacion_desde_panel)

            self._alertas_layout.insertWidget(i, card)

        logger.debug(f"Panel notificaciones actualizado: {n} producto(s)")

    def _abrir_autorizacion_desde_panel(self) -> None:
        """Abre el diálogo de autorización de pedido desde una tarjeta del panel."""
        if not self._productos_alerta_actual:
            return
        try:
            from app.presentation.components.alerta_autorizacion_dialog import (
                AlertaAutorizacionDialog
            )
            # Obtener usuario autenticado desde la ventana principal
            authenticated_user = None
            parent = self.parent()
            if parent and hasattr(parent, 'authenticated_user'):
                authenticated_user = parent.authenticated_user

            dialog = AlertaAutorizacionDialog(
                productos=self._productos_alerta_actual,
                authenticated_user=authenticated_user,
                parent=self,
            )
            if dialog.exec_() == AlertaAutorizacionDialog.Accepted:
                pedido = dialog.get_pedido_creado()
                if pedido:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self,
                        "Pedido Creado",
                        f"Pedido de reabastecimiento registrado.\n"
                        f"ID: #{pedido.id}  |  Productos: {len(self._productos_alerta_actual)}\n"
                        f"Puede ver los detalles en la pestaña Pedidos."
                    )
        except Exception as e:
            logger.error(f"Error al abrir diálogo de autorización desde panel: {e}")

    def _limpiar_panel(self) -> None:
        """
        Elimina todas las tarjetas del panel, vacía la lista interna,
        resetea el badge a (0) y oculta el panel.
        El monitor de stock las volverá a añadir en el siguiente ciclo
        si el stock sigue estando bajo.
        """
        # 1. Eliminar todas las tarjetas del layout (excepto el stretch final)
        while self._alertas_layout.count() > 1:
            item = self._alertas_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 2. Vaciar lista interna
        self._productos_alerta_actual = []

        # 3. Mostrar mensaje vacío
        empty = QLabel("Sin notificaciones")
        empty.setStyleSheet("color: #a0aec0; font-size: 9pt;")
        empty.setAlignment(Qt.AlignCenter)
        self._alertas_layout.insertWidget(0, empty)

        # 4. Resetear badge
        self._btn_alertas.setText("Notificaciones (0)")
        self._btn_alertas.setChecked(False)

        # 5. Ocultar panel
        self._panel_alertas.setVisible(False)
        logger.debug("Panel notificaciones limpiado completamente por el usuario")

    def toggle_panel_alertas(self) -> None:
        """Muestra u oculta el panel lateral de notificaciones."""
        visible = self._btn_alertas.isChecked()
        self._panel_alertas.setVisible(visible)
        logger.debug(f"Panel notificaciones {'visible' if visible else 'oculto'}")


class ProductoDialog(QDialog):

    """Diálogo para agregar/editar productos"""

    def __init__(self, categorias, producto=None, parent=None):
        super().__init__(parent)
        self.categorias = categorias
        self.producto = producto
        self.is_edit = producto is not None
        self.proveedor_repo = ProveedorRepository()   # ✅ NUEVO
        self.proveedores = self.proveedor_repo.get_all()  # ✅ NUEVO: carga proveedores activos
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

        # ✅ NUEVO: Proveedor
        self.proveedor_combo = QComboBox()
        self.proveedor_combo.addItem("-- Sin proveedor --", None)
        for prov in self.proveedores:
            self.proveedor_combo.addItem(prov.nombre, prov.id)
        self.proveedor_combo.setToolTip(
            "Proveedor principal de este producto.\n"
            "Aparecerá al generar pedidos automáticos."
        )
        form_layout.addRow("Proveedor:", self.proveedor_combo)

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

        # ✅ NUEVO: Cargar proveedor principal asignado al producto
        try:
            proveedor = self.proveedor_repo.get_proveedor_de_producto(self.producto.id)
            if proveedor:
                idx = self.proveedor_combo.findData(proveedor.id)
                if idx >= 0:
                    self.proveedor_combo.setCurrentIndex(idx)
        except Exception:
            pass  # Si falla, deja el combo en '-- Sin proveedor --'

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

    def get_proveedor_id_seleccionado(self) -> int | None:
        """✅ NUEVO: Retorna el ID del proveedor seleccionado (None si no hay)"""
        return self.proveedor_combo.currentData()
