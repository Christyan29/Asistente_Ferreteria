"""
Servicio para generar pedidos en PDF.
Crea documentos PDF profesionales para compartir con proveedores.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime
from pathlib import Path
from typing import List
import logging
import os

from app.domain.producto import Producto

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generador de PDFs para pedidos"""

    def __init__(self):
        # Guardar en carpeta Descargas del usuario
        downloads_path = Path.home() / "Downloads" / "Pedidos_Ferreteria"
        self.output_dir = downloads_path
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generar_pedido(self, productos: List[Producto], cantidades_editadas: dict = None) -> str:
        """
        Genera un PDF de pedido con los productos.

        Args:
            productos: Lista de productos con stock bajo
            cantidades_editadas: Diccionario con cantidades editadas {producto_id: cantidad}

        Returns:
            Ruta del archivo PDF generado
        """
        if not productos:
            logger.warning("No hay productos para generar PDF")
            return None

        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"pedido_{timestamp}.pdf"
        filepath = self.output_dir / filename

        try:
            # Crear documento con metadatos
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch,
                title="Pedido de Reabastecimiento - Ferretería Disensa",
                author="Ferretería Disensa - Pomasqui",
                subject="Pedido de productos con stock bajo"
            )

            # Contenedor de elementos
            elements = []
            styles = getSampleStyleSheet()

            # Estilo personalizado para título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#cc785c'),
                spaceAfter=30,
                alignment=TA_CENTER
            )

            # Título
            title = Paragraph("PEDIDO DE REABASTECIMIENTO", title_style)
            elements.append(title)

            # Información del pedido
            info_style = styles['Normal']
            fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
            info = Paragraph(f"<b>Fecha:</b> {fecha}<br/><b>Ferretería Disensa - Pomasqui</b>", info_style)
            elements.append(info)
            elements.append(Spacer(1, 0.3*inch))

            # Preparar datos de la tabla
            data = [['Código', 'Producto', 'Stock\nActual', 'Stock\nMínimo', 'Cantidad\na Pedir', 'Unidad', 'Precio\nUnit.', 'Total']]

            total_general = 0

            for p in productos:
                # Calcular cantidad a pedir
                if cantidades_editadas and p.id in cantidades_editadas:
                    cantidad_pedir = cantidades_editadas[p.id]
                else:
                    faltante = p.stock_minimo - p.stock
                    cantidad_pedir = max(faltante, p.stock_minimo)

                subtotal = float(p.precio) * cantidad_pedir
                total_general += subtotal

                data.append([
                    p.codigo or '',
                    p.nombre,  # Sin truncar, reportlab maneja el ajuste
                    str(p.stock),
                    str(p.stock_minimo),
                    str(cantidad_pedir),
                    p.unidad_medida or 'unidad',
                    f'${p.precio:.2f}',
                    f'${subtotal:.2f}'
                ])

            # Crear tabla
            table = Table(data, colWidths=[0.8*inch, 2.2*inch, 0.6*inch, 0.6*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.8*inch])

            # Estilo de la tabla
            table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cc785c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),

                # Datos
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (2, 1), (-1, -1), 'CENTER'),  # Números centrados
                ('ALIGN', (0, 1), (1, -1), 'LEFT'),  # Código y nombre a la izquierda
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff5f0')]),

                # Bordes
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))

            # Total
            total_style = ParagraphStyle(
                'Total',
                parent=styles['Normal'],
                fontSize=14,
                textColor=colors.HexColor('#cc785c'),
                alignment=TA_RIGHT,
                fontName='Helvetica-Bold'
            )
            total_text = Paragraph(f"<b>TOTAL ESTIMADO: ${total_general:.2f}</b>", total_style)
            elements.append(total_text)

            elements.append(Spacer(1, 0.3*inch))

            # Notas
            notes_style = ParagraphStyle(
                'Notes',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey
            )
            notes = Paragraph(
                "<b>Notas:</b><br/>"
                "• Este pedido fue generado automáticamente por el sistema de gestión de inventario.<br/>"
                "• Las cantidades sugeridas se calculan en base al stock mínimo configurado.<br/>"
                "• Por favor, confirmar disponibilidad y precios con el proveedor.",
                notes_style
            )
            elements.append(notes)

            # Construir PDF
            doc.build(elements)

            logger.info(f"PDF generado: {filepath}")
            logger.info(f"Total productos: {len(productos)}")
            logger.info(f"Total estimado: ${total_general:.2f}")

            return str(filepath)

        except Exception as e:
            logger.error(f"Error al generar PDF: {e}")
            raise

    def abrir_archivo(self, filepath: str):
        """
        Abre el PDF en el navegador Y muestra la carpeta donde está guardado.

        Args:
            filepath: Ruta del archivo a abrir
        """
        try:
            if os.path.exists(filepath):
                # Abrir PDF en navegador
                os.startfile(filepath)
                logger.info(f"Abriendo PDF en navegador: {filepath}")

                # También mostrar la carpeta donde está guardado
                import subprocess
                subprocess.Popen(f'explorer /select,"{filepath}"')
                logger.info(f"Mostrando ubicación en Explorador: {filepath}")
            else:
                logger.error(f"Archivo no encontrado: {filepath}")
        except Exception as e:
            logger.error(f"Error al abrir archivo: {e}")
