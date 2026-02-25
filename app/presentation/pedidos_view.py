"""
Vista de Pedidos - Productos con Stock Bajo
Muestra productos que necesitan reabastecimiento y permite generar pedidos en PDF
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QMessageBox, QHeaderView, QDialog,
    QListWidget, QListWidgetItem, QDialogButtonBox, QTabWidget,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import logging

from app.infrastructure.product_repository import ProductRepository
from app.services.pdf_generator import PDFGenerator
from app.presentation.components.review_dialog import ReviewDialog
# ✅ NUEVO: repositorios para persistencia de pedidos
from app.infrastructure.pedidos_repository import PedidosRepository
from app.infrastructure.proveedor_repository import ProveedorRepository

logger = logging.getLogger(__name__)


class PedidosView(QWidget):
    """Vista para gestionar pedidos de productos con stock bajo"""

    def __init__(self, parent=None, authenticated_user=None):
        super().__init__(parent)

        self.producto_repo = ProductRepository()
        self.pdf_generator = PDFGenerator()
        self.pedidos_repo = PedidosRepository()       # ✅ NUEVO
        self.proveedor_repo = ProveedorRepository()   # ✅ NUEVO
        self.productos_bajo_stock = []
        self.authenticated_user = authenticated_user  # ✅ NUEVO: para el log del pedido

        self.setup_ui()
        self.cargar_productos()

    def setup_ui(self):
        """Configura la interfaz con dos sub-pestañas: Stock Bajo e Historial de Pedidos."""
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── QTabWidget principal ─────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #f8f9fb;
            }
            QTabBar::tab {
                padding: 10px 28px;
                font-size: 10pt;
                font-weight: 500;
                color: #718096;
                background-color: #f0f4f8;
                border: 1px solid #e2e8f0;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 6px;
                min-width: 130px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #cc785c;
                font-weight: 700;
                border-bottom: 2px solid #cc785c;
            }
            QTabBar::tab:hover:!selected {
                background-color: #edf2f7;
                color: #4a5568;
            }
        """)
        root.addWidget(self.tabs)

        # ================================================================
        # SUB-PESTAÑA 1: Stock Bajo
        # ================================================================
        tab_stock = QWidget()
        self.tabs.addTab(tab_stock, "Stock Bajo")
        layout_stock = QVBoxLayout(tab_stock)
        layout_stock.setSpacing(12)
        layout_stock.setContentsMargins(20, 18, 20, 16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Productos con Stock Bajo")
        title.setStyleSheet("font-size: 20pt; font-weight: 700; color: #2d3748;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.contador_label = QLabel("0 productos")
        self.contador_label.setStyleSheet("""
            font-size: 13pt; color: #cc785c; font-weight: 600;
            background-color: #fff5f0; padding: 6px 14px; border-radius: 6px;
        """)
        header_layout.addWidget(self.contador_label)
        layout_stock.addLayout(header_layout)

        desc = QLabel("Selecciona los productos que necesitas reponer y genera el pedido en PDF.")
        desc.setStyleSheet("font-size: 10pt; color: #718096;")
        layout_stock.addWidget(desc)

        # Tabla de stock bajo (sin cambios en estructura)
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "Seleccionar", "Código", "Producto", "Categoría", "Stock Actual",
            "Faltante", "Unidad", "Marca", "Precio"
        ])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        hdr = self.tabla.horizontalHeader()
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        for i in [0, 1, 3, 4, 5, 6, 7, 8]:
            hdr.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
            }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:selected { background-color: #fff5f0; color: #2d3748; }
            QHeaderView::section {
                background-color: #f7fafc; padding: 10px;
                border: none; border-bottom: 2px solid #e2e8f0;
                font-weight: 600; color: #2d3748;
            }
        """)
        layout_stock.addWidget(self.tabla)

        # Botones Stock Bajo
        btns_stock = QHBoxLayout()
        btns_stock.addStretch()
        self.btn_refrescar = QPushButton("Refrescar")
        self.btn_refrescar.setObjectName("secondaryButton")
        self.btn_refrescar.clicked.connect(self.cargar_productos)
        btns_stock.addWidget(self.btn_refrescar)
        self.btn_generar = QPushButton("Generar Pedido PDF")
        self.btn_generar.setObjectName("primaryButton")
        self.btn_generar.clicked.connect(self.generar_pedido)
        btns_stock.addWidget(self.btn_generar)
        layout_stock.addLayout(btns_stock)

        # ================================================================
        # SUB-PESTAÑA 2: Historial de Pedidos
        # ================================================================
        tab_historial = QWidget()
        self.tabs.addTab(tab_historial, "Historial de Pedidos")
        layout_hist = QVBoxLayout(tab_historial)
        layout_hist.setSpacing(10)
        layout_hist.setContentsMargins(20, 18, 20, 16)

        # Header historial
        hist_header = QHBoxLayout()
        lbl_hist = QLabel("Historial de Pedidos de Reabastecimiento")
        lbl_hist.setStyleSheet("font-size: 16pt; font-weight: 700; color: #2d3748;")
        hist_header.addWidget(lbl_hist)
        hist_header.addStretch()

        self.btn_marcar_enviado = QPushButton("✓  Marcar como Enviado")
        self.btn_marcar_enviado.setEnabled(False)
        self.btn_marcar_enviado.setStyleSheet("""
            QPushButton {
                background-color: #3182ce; color: white; border: none;
                border-radius: 6px; padding: 8px 16px; font-size: 10pt; font-weight: 600;
            }
            QPushButton:hover { background-color: #2b6cb0; }
            QPushButton:pressed { background-color: #2c5282; }
            QPushButton:disabled { background-color: #bee3f8; }
        """)
        self.btn_marcar_enviado.clicked.connect(self._marcar_enviado)
        hist_header.addWidget(self.btn_marcar_enviado)

        self.btn_refrescar_pedidos = QPushButton("↺  Actualizar")
        self.btn_refrescar_pedidos.setObjectName("secondaryButton")
        self.btn_refrescar_pedidos.clicked.connect(self.cargar_pedidos_registrados)
        hist_header.addWidget(self.btn_refrescar_pedidos)
        layout_hist.addLayout(hist_header)

        pedidos_desc = QLabel(
            "Pedidos generados automáticamente por el monitor de stock o al guardar un PDF."
        )
        pedidos_desc.setStyleSheet("font-size: 9pt; color: #718096;")
        layout_hist.addWidget(pedidos_desc)

        # Tabla de pedidos — 6 columnas: ID | Fecha | Productos | Proveedor | Asignar | Estado
        self.tabla_pedidos = QTableWidget()
        self.tabla_pedidos.setColumnCount(6)
        self.tabla_pedidos.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Productos", "Proveedor", "Asignar", "Estado"]
        )
        self.tabla_pedidos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_pedidos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_pedidos.setAlternatingRowColors(True)
        self.tabla_pedidos.verticalHeader().setVisible(False)
        ph = self.tabla_pedidos.horizontalHeader()
        ph.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        ph.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Fecha
        ph.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Productos
        ph.setSectionResizeMode(3, QHeaderView.Interactive)        # Proveedor
        ph.setSectionResizeMode(4, QHeaderView.Fixed)             # Asignar (fijo)
        ph.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Estado
        self.tabla_pedidos.setColumnWidth(3, 160)  # Proveedor: 160 px
        self.tabla_pedidos.setColumnWidth(4, 140)  # Asignar: 140 px fijo
        self.tabla_pedidos.verticalHeader().setDefaultSectionSize(55)  # fila más alta
        self.tabla_pedidos.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
            }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:selected { background-color: #fff5f0; color: #2d3748; }
            QHeaderView::section {
                background-color: #f7fafc; padding: 8px;
                border: none; border-bottom: 2px solid #e2e8f0;
                font-weight: 600; color: #2d3748;
            }
        """)
        self.tabla_pedidos.selectionModel().selectionChanged.connect(
            self._on_pedido_selection_changed
        )
        self.tabla_pedidos.cellDoubleClicked.connect(self._on_tabla_pedidos_double_click)
        layout_hist.addWidget(self.tabla_pedidos)

        hint_pedidos = QLabel(
            "Selecciona un pedido y usa los botones de arriba. "
            "También puedes hacer doble-clic en Proveedor."
        )
        hint_pedidos.setStyleSheet("font-size: 8pt; color: #a0aec0; padding: 2px 0;")
        layout_hist.addWidget(hint_pedidos)

        # Lista interna
        self._pedidos_registrados = []

        # Cargar datos al iniciar
        self.cargar_pedidos_registrados()

    def cargar_pedidos_registrados(self):
        """Carga los últimos pedidos registrados en la BD — tabla con 6 columnas."""
        try:
            pedidos = self.pedidos_repo.get_pedidos_recientes(limite=20)
            self.tabla_pedidos.setRowCount(0)

            if not pedidos:
                self._pedidos_registrados = []
                self.tabla_pedidos.setRowCount(1)
                empty_item = QTableWidgetItem("No hay pedidos registrados aún")
                empty_item.setTextAlignment(Qt.AlignCenter)
                empty_item.setForeground(QColor("#a0aec0"))
                self.tabla_pedidos.setItem(0, 0, empty_item)
                self.tabla_pedidos.setSpan(0, 0, 1, 6)
                self.btn_marcar_enviado.setEnabled(False)
                return

            self._pedidos_registrados = list(pedidos)
            for row, pedido in enumerate(pedidos):
                self.tabla_pedidos.insertRow(row)

                # Col 0: ID
                id_item = QTableWidgetItem(f"#{pedido.id}")
                id_item.setTextAlignment(Qt.AlignCenter)
                id_item.setForeground(QColor("#cc785c"))
                self.tabla_pedidos.setItem(row, 0, id_item)

                # Col 1: Fecha
                fecha_str = (
                    pedido.fecha_pedido.strftime("%d/%m/%Y %H:%M")
                    if pedido.fecha_pedido else "—"
                )
                fecha_item = QTableWidgetItem(fecha_str)
                fecha_item.setTextAlignment(Qt.AlignCenter)
                self.tabla_pedidos.setItem(row, 1, fecha_item)

                # Col 2: Cantidad productos
                n_prods = len(pedido.detalles)
                prods_item = QTableWidgetItem(str(n_prods))
                prods_item.setTextAlignment(Qt.AlignCenter)
                self.tabla_pedidos.setItem(row, 2, prods_item)

                # Col 3: Proveedor
                prov_texto = pedido.proveedor_nombre or "sin asignar"
                prov_item = QTableWidgetItem(prov_texto)
                if not pedido.proveedor_nombre:
                    prov_item.setForeground(QColor("#a0aec0"))
                self.tabla_pedidos.setItem(row, 3, prov_item)

                # Col 4: Botón Asignar — tamaño fijo, centrado con stretch
                cell_widget = QWidget()
                cell_widget.setStyleSheet("background: transparent;")
                cell_layout = QHBoxLayout(cell_widget)
                cell_layout.setContentsMargins(4, 3, 4, 3)
                cell_layout.setSpacing(0)

                btn_asignar = QPushButton("Asignar")
                # SizePolicy Fixed evita que el layout estire el botón
                btn_asignar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                btn_asignar.setFixedWidth(72)
                btn_asignar.setFixedHeight(32)
                btn_asignar.setStyleSheet("""
                    QPushButton {
                        background-color: #cc785c;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 9pt;
                        font-weight: 600;
                    }
                    QPushButton:hover  { background-color: #b5634a; }
                    QPushButton:pressed { background-color: #9c4f36; }
                """)
                btn_asignar.clicked.connect(
                    lambda checked, r=row, p=pedido: self._seleccionar_proveedor_pedido(p, r)
                )
                # Stretch a ambos lados → botón centrado y NO estirado
                cell_layout.addStretch()
                cell_layout.addWidget(btn_asignar)
                cell_layout.addStretch()
                self.tabla_pedidos.setCellWidget(row, 4, cell_widget)

                # Col 5: Estado
                label_estado = {
                    "pendiente": "Por enviar",
                    "enviado": "Enviado ✓",
                    "recibido": "Recibido ✓✓",
                }.get(pedido.estado.lower(), pedido.estado.capitalize())
                color_estado = {
                    "pendiente": "#d69e2e",
                    "enviado": "#3182ce",
                    "recibido": "#38a169",
                }.get(pedido.estado.lower(), "#718096")
                estado_item = QTableWidgetItem(label_estado)
                estado_item.setTextAlignment(Qt.AlignCenter)
                estado_item.setForeground(QColor(color_estado))
                self.tabla_pedidos.setItem(row, 5, estado_item)

        except Exception as e:
            logger.error(f"Error al cargar pedidos registrados: {e}")

    def _on_pedido_selection_changed(self):
        """Habilita/deshabilita el botón 'Marcar como Enviado' según la fila seleccionada."""
        rows = self.tabla_pedidos.selectionModel().selectedRows()
        if not rows:
            self.btn_marcar_enviado.setEnabled(False)
            return
        idx = rows[0].row()
        if idx >= len(self._pedidos_registrados):
            self.btn_marcar_enviado.setEnabled(False)
            return
        pedido = self._pedidos_registrados[idx]
        # Solo habilitar si el estado es pendiente
        self.btn_marcar_enviado.setEnabled(
            pedido.estado.lower() == "pendiente"
        )

    def _marcar_enviado(self):
        """Cambia el estado del pedido seleccionado a 'enviado' en la BD."""
        rows = self.tabla_pedidos.selectionModel().selectedRows()
        if not rows:
            return
        idx = rows[0].row()
        if idx >= len(self._pedidos_registrados):
            return
        pedido = self._pedidos_registrados[idx]
        try:
            self.pedidos_repo.update_estado_pedido(pedido.id, "enviado")
            # Actualizar celda y objeto en memoria
            self.tabla_pedidos.item(idx, 5).setText("Enviado ✓")
            self.tabla_pedidos.item(idx, 5).setForeground(QColor("#3182ce"))
            self._pedidos_registrados[idx] = type(pedido)(
                id=pedido.id,
                proveedor_id=pedido.proveedor_id,
                proveedor_nombre=pedido.proveedor_nombre,
                estado="enviado",
                notas=pedido.notas,
                created_by=pedido.created_by,
                fecha_pedido=pedido.fecha_pedido,
                detalles=pedido.detalles,
            )
            self.btn_marcar_enviado.setEnabled(False)
            logger.info(f"Pedido #{pedido.id} marcado como enviado")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar el estado:\n{e}")

    def _on_tabla_pedidos_double_click(self, row: int, column: int) -> None:
        """Abre el selector de proveedor al hacer doble-clic en la columna Proveedor (3)."""
        if column != 3:
            return
        if row >= len(self._pedidos_registrados):
            return
        pedido = self._pedidos_registrados[row]
        self._seleccionar_proveedor_pedido(pedido, row)

    def _seleccionar_proveedor_pedido(self, pedido, row: int) -> None:
        """Diálogo de selección rápida de proveedor activo para un pedido."""
        try:
            proveedores = self.proveedor_repo.get_all(solo_activos=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar proveedores:\n{e}")
            return

        if not proveedores:
            QMessageBox.information(
                self, "Sin proveedores",
                "No hay proveedores activos. Agregue uno en la pestaña Proveedores."
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Asignar Proveedor al Pedido")
        dlg.setMinimumWidth(380)
        v = QVBoxLayout(dlg)
        v.setSpacing(10)
        v.setContentsMargins(16, 16, 16, 12)

        v.addWidget(QLabel(
            f"<b>Pedido #{pedido.id}</b> — selecciona el proveedor activo:"
        ))

        lista = QListWidget()
        lista.setStyleSheet("""
            QListWidget {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background: white;
            }
            QListWidget::item {
                padding: 8px 10px;
            }
            QListWidget::item:selected {
                background-color: #fff5f0;
                color: #cc785c;
            }
        """)
        lista.setAlternatingRowColors(True)

        for prov in proveedores:
            item = QListWidgetItem(f"{prov.nombre}  —  {prov.contacto or ''} | {prov.telefono or ''}")
            item.setData(Qt.UserRole, prov)
            lista.addItem(item)

        # Pre-selecciona el proveedor actual si ya hay uno
        if pedido.proveedor_id:
            for i in range(lista.count()):
                prov_item = lista.item(i).data(Qt.UserRole)
                if prov_item.id == pedido.proveedor_id:
                    lista.setCurrentRow(i)
                    break

        v.addWidget(lista)

        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btns.button(QDialogButtonBox.Ok).setText("Asignar")
        btns.button(QDialogButtonBox.Ok).setStyleSheet("""
            QPushButton {
                background-color: #cc785c; color: white; border: none;
                border-radius: 5px; padding: 6px 16px; font-weight: 600;
            }
            QPushButton:hover { background-color: #b5634a; }
        """)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        v.addWidget(btns)

        if dlg.exec_() != QDialog.Accepted:
            return

        selected = lista.currentItem()
        if not selected:
            return

        prov_sel = selected.data(Qt.UserRole)
        try:
            self.pedidos_repo.update_proveedor_pedido(
                pedido_id=pedido.id,
                proveedor_id=prov_sel.id,
                proveedor_nombre=prov_sel.nombre
            )
            # Actualizar celda en la tabla sin recargar todo
            self.tabla_pedidos.item(row, 3).setText(prov_sel.nombre)
            # Actualizar objeto en lista mem
            self._pedidos_registrados[row] = type(pedido)(
                id=pedido.id,
                proveedor_id=prov_sel.id,
                proveedor_nombre=prov_sel.nombre,
                estado=pedido.estado,
                notas=pedido.notas,
                created_by=pedido.created_by,
                fecha_pedido=pedido.fecha_pedido,
                detalles=pedido.detalles,
            )
            logger.info(
                f"Proveedor del pedido #{pedido.id} actualizado a: {prov_sel.nombre}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar el pedido:\n{e}")

    def showEvent(self, event):
        """Recarga ambas tablas cada vez que el usuario navega a esta pestaña."""
        super().showEvent(event)
        self.cargar_productos()
        self.cargar_pedidos_registrados()

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

                # Generar PDF (flujo existente - sin cambios)
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

                # ✅ NUEVO: Ofrecer guardar el pedido en la base de datos
                self._guardar_pedido_en_bd(productos_seleccionados, cantidades)

        except Exception as e:
            logger.error(f"Error al generar pedido: {e}")
            QMessageBox.critical(self, "Error", f"Error al generar pedido:\n{str(e)}")

    # =========================================================================
    # ✅ NUEVO: Método para guardar pedido en BD (no afecta al flujo del PDF)
    # =========================================================================

    def _guardar_pedido_en_bd(self, productos_seleccionados, cantidades):
        """
        Muestra un diálogo de confirmación y guarda el pedido en la base de datos.
        Método completamente independiente del flujo de PDF existente.
        """
        try:
            # Buscar el proveedor principal del primer producto seleccionado
            proveedor = None
            proveedor_id = None
            proveedor_nombre = None

            if productos_seleccionados:
                proveedor = self.proveedor_repo.get_proveedor_de_producto(
                    productos_seleccionados[0].id
                )

            if proveedor:
                proveedor_id = proveedor.id
                proveedor_nombre = proveedor.nombre
                info_proveedor = f"Proveedor: {proveedor_nombre}"
            else:
                info_proveedor = "Proveedor: (no asignado)"

            n_productos = len(productos_seleccionados)
            total_items = sum(cantidades.get(p.id, 1) for p in productos_seleccionados)

            respuesta = QMessageBox.question(
                self,
                "Guardar Pedido",
                f"¿Desea registrar este pedido en la base de datos?\n\n"
                f"  {info_proveedor}\n"
                f"  Productos: {n_productos}\n"
                f"  Unidades totales: {total_items}\n\n"
                f"El pedido quedará en estado 'pendiente' para seguimiento.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if respuesta == QMessageBox.Yes:
                pedido = self.pedidos_repo.crear_pedido(
                    proveedor_id=proveedor_id,
                    proveedor_nombre=proveedor_nombre,
                    productos_seleccionados=productos_seleccionados,
                    cantidades=cantidades,
                    created_by=self.authenticated_user,
                )
                QMessageBox.information(
                    self,
                    "Pedido Registrado",
                    f"Pedido #{pedido.id} guardado correctamente.\n"
                    f"Estado: Pendiente\n"
                    f"{info_proveedor}\n"
                    f"Productos: {n_productos}"
                )
                logger.info(
                    f"Pedido #{pedido.id} registrado en BD — "
                    f"{n_productos} productos — usuario: {self.authenticated_user}"
                )

        except Exception as e:
            logger.error(f"Error al guardar pedido en BD: {e}")
            QMessageBox.warning(
                self,
                "Advertencia",
                f"El PDF fue generado correctamente, pero no se pudo guardar en la base de datos:\n{str(e)}"
            )
