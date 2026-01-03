"""
Servicio para importar productos desde archivos Excel - CORREGIDO
"""
import pandas as pd
import logging
from decimal import Decimal
from app.infrastructure.product_repository import ProductRepository, CategoriaRepository
from app.domain.producto import Producto
from app.domain.categoria import Categoria

logger = logging.getLogger(__name__)

class ExcelImporter:
    """
    Clase responsable de la importación masiva de productos desde Excel.
    """

    REQUIRED_COLUMNS = [
        'Nombre', 'Categoría', 'Precio', 'Stock', 'Unidad'
    ]

    OPTIONAL_COLUMNS = [
        'Código', 'Stock Mínimo', 'Marca', 'Ubicación', 'Descripción'
    ]

    def __init__(self):
        self.product_repo = ProductRepository()
        self.category_repo = CategoriaRepository()

    def import_products(self, file_path):
        """
        Importa productos desde un archivo Excel.

        Args:
            file_path (str): Ruta al archivo .xlsx

        Returns:
            dict: Resumen de la importación {'total': int, 'success': int, 'errors': list}
        """
        stats = {
            'total': 0,
            'success': 0,
            'updated': 0,
            'created': 0,
            'errors': []
        }

        try:
            # Leer archivo Excel
            df = pd.read_excel(file_path)

            # Validar columnas requeridas
            missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Faltan columnas requeridas: {', '.join(missing_cols)}")

            stats['total'] = len(df)

            # Obtener todas las categorías existentes
            existing_categories = {c.nombre.lower(): c for c in self.category_repo.get_all()}

            # Obtener todos los productos existentes para comparar por nombre
            existing_products = {p.nombre.lower(): p for p in self.product_repo.get_all(solo_activos=False)}

            for index, row in df.iterrows():
                try:
                    # Datos básicos
                    nombre = str(row['Nombre']).strip()
                    cat_nombre = str(row['Categoría']).strip()
                    precio = float(row['Precio'])
                    stock = int(row['Stock'])
                    unidad = str(row['Unidad']).strip()

                    if not nombre or not cat_nombre:
                        raise ValueError("Nombre y Categoría son obligatorios")

                    # Manejar categoría
                    categoria = existing_categories.get(cat_nombre.lower())
                    if not categoria:
                        # Crear nueva categoría
                        categoria = Categoria(
                            nombre=cat_nombre,
                            descripcion="Importada desde Excel",
                            activo=True
                        )
                        categoria = self.category_repo.create(categoria)
                        existing_categories[cat_nombre.lower()] = categoria
                        logger.info(f"Categoría creada: {cat_nombre}")

                    # Datos opcionales
                    codigo = str(row.get('Código', '')).strip() if pd.notna(row.get('Código')) else None
                    stock_min = int(row.get('Stock Mínimo', 10)) if pd.notna(row.get('Stock Mínimo')) else 10
                    marca = str(row.get('Marca', '')).strip() if pd.notna(row.get('Marca')) else None
                    ubicacion = str(row.get('Ubicación', '')).strip() if pd.notna(row.get('Ubicación')) else None
                    descripcion = str(row.get('Descripción', '')).strip() if pd.notna(row.get('Descripción')) else None

                    # Buscar producto existente por nombre
                    existing_product = existing_products.get(nombre.lower())

                    if existing_product:
                        # Actualizar producto existente
                        existing_product.codigo = codigo
                        existing_product.precio = Decimal(str(precio))
                        existing_product.stock = stock
                        existing_product.unidad_medida = unidad
                        existing_product.stock_minimo = stock_min
                        existing_product.marca = marca
                        existing_product.ubicacion = ubicacion
                        existing_product.descripcion = descripcion
                        existing_product.categoria_id = categoria.id
                        existing_product.activo = True

                        self.product_repo.update(existing_product)
                        stats['updated'] += 1
                        logger.info(f"Producto actualizado: {nombre}")
                    else:
                        # Crear nuevo producto
                        new_product = Producto(
                            codigo=codigo,
                            nombre=nombre,
                            descripcion=descripcion,
                            precio=Decimal(str(precio)),
                            stock=stock,
                            unidad_medida=unidad,
                            categoria_id=categoria.id,
                            stock_minimo=stock_min,
                            marca=marca,
                            ubicacion=ubicacion,
                            activo=True
                        )
                        created = self.product_repo.create(new_product)
                        existing_products[nombre.lower()] = created
                        stats['created'] += 1
                        logger.info(f"Producto creado: {nombre}")

                    stats['success'] += 1

                except Exception as e:
                    error_msg = f"Fila {index + 2}: {str(e)}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)

            return stats

        except Exception as e:
            logger.error(f"Error general en importación: {e}")
            raise e
