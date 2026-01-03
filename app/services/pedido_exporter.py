"""
Servicio para exportar pedidos de productos con stock bajo a Excel.
"""
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List
import logging
import os

from app.domain.producto import Producto

logger = logging.getLogger(__name__)


class PedidoExporter:
    """Servicio para exportar pedidos a Excel"""

    def __init__(self):
        self.output_dir = Path("pedidos")
        self.output_dir.mkdir(exist_ok=True)

    def exportar_productos_bajo_stock(self, productos: List[Producto]) -> str:
        """
        Exporta productos con stock bajo a Excel.

        Args:
            productos: Lista de productos con stock bajo

        Returns:
            Ruta del archivo Excel generado
        """
        if not productos:
            logger.warning("No hay productos para exportar")
            return None

        # Preparar datos
        data = []
        for p in productos:
            faltante = p.stock_minimo - p.stock
            cantidad_pedir = max(faltante, p.stock_minimo)  # Pedir al menos el mínimo

            data.append({
                'Código': p.codigo or '',
                'Producto': p.nombre,
                'Categoría': p.categoria_nombre or 'Sin categoría',
                'Stock Actual': p.stock,
                'Stock Mínimo': p.stock_minimo,
                'Faltante': faltante,
                'Cantidad a Pedir': cantidad_pedir,
                'Unidad': p.unidad_medida or 'unidad',
                'Marca': p.marca or '',
                'Ubicación': p.ubicacion or '',
                'Precio Unitario': float(p.precio),
                'Total Estimado': float(p.precio) * cantidad_pedir
            })

        # Crear DataFrame
        df = pd.DataFrame(data)

        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"pedido_{timestamp}.xlsx"
        filepath = self.output_dir / filename

        # Exportar a Excel con formato
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Pedido', index=False)

                # Obtener worksheet para formatear
                worksheet = writer.sheets['Pedido']

                # Ajustar anchos de columna
                column_widths = {
                    'A': 12,  # Código
                    'B': 35,  # Producto
                    'C': 20,  # Categoría
                    'D': 12,  # Stock Actual
                    'E': 12,  # Stock Mínimo
                    'F': 12,  # Faltante
                    'G': 15,  # Cantidad a Pedir
                    'H': 10,  # Unidad
                    'I': 15,  # Marca
                    'J': 15,  # Ubicación
                    'K': 15,  # Precio Unitario
                    'L': 15,  # Total Estimado
                }

                for col, width in column_widths.items():
                    worksheet.column_dimensions[col].width = width

                # Formatear header
                from openpyxl.styles import Font, PatternFill, Alignment

                header_fill = PatternFill(start_color="CC785C", end_color="CC785C", fill_type="solid")
                header_font = Font(bold=True, color="FFFFFF")

                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center', vertical='center')

                # Agregar filtros
                worksheet.auto_filter.ref = worksheet.dimensions

            logger.info(f"Archivo Excel generado: {filepath}")
            logger.info(f"Total productos: {len(productos)}")
            logger.info(f"Total estimado: ${df['Total Estimado'].sum():.2f}")

            return str(filepath)

        except Exception as e:
            logger.error(f"Error al generar Excel: {e}")
            raise

    def abrir_archivo(self, filepath: str):
        """
        Abre el archivo Excel generado.

        Args:
            filepath: Ruta del archivo a abrir
        """
        try:
            if os.path.exists(filepath):
                os.startfile(filepath)  # Windows
                logger.info(f"Abriendo archivo: {filepath}")
            else:
                logger.error(f"Archivo no encontrado: {filepath}")
        except Exception as e:
            logger.error(f"Error al abrir archivo: {e}")
