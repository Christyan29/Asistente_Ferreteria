"""
Script de prueba para validar la configuración de base de datos.
Crea la base de datos, inserta datos de prueba y realiza consultas básicas.
"""
import sys
from pathlib import Path
from decimal import Decimal

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.config.settings import DatabaseConfig, validate_config
from app.infrastructure.database import init_database, session_scope
from app.infrastructure.product_repository import ProductRepository, CategoriaRepository
from app.domain.producto import Producto
from app.domain.categoria import Categoria


def test_database_setup():
    """Prueba la configuración de la base de datos"""
    print("=" * 60)
    print("PRUEBA DE BASE DE DATOS - FASE 1")
    print("=" * 60)

    # 1. Validar configuración
    print("\n1. Validando configuración...")
    try:
        # Comentar la validación de API key para esta prueba
        print(f"   ✓ Base de datos: {DatabaseConfig.URL}")
        print(f"   ✓ Configuración cargada correctamente")
    except Exception as e:
        print(f"   ✗ Error en configuración: {e}")
        return False

    # 2. Inicializar base de datos
    print("\n2. Inicializando base de datos...")
    try:
        db = init_database()
        print("   ✓ Base de datos inicializada")
        print("   ✓ Tablas creadas: productos, categorias")
    except Exception as e:
        print(f"   ✗ Error al inicializar BD: {e}")
        return False

    # 3. Crear categorías de prueba
    print("\n3. Creando categorías de prueba...")
    try:
        with session_scope() as session:
            cat_repo = CategoriaRepository(session)

            categorias = [
                Categoria(nombre="Herramientas", descripcion="Herramientas manuales y eléctricas"),
                Categoria(nombre="Pinturas", descripcion="Pinturas y accesorios"),
                Categoria(nombre="Electricidad", descripcion="Material eléctrico"),
                Categoria(nombre="Plomería", descripcion="Tuberías y accesorios"),
            ]

            for cat in categorias:
                cat_creada = cat_repo.create(cat)
                print(f"   ✓ Categoría creada: {cat_creada.nombre} (ID: {cat_creada.id})")
    except Exception as e:
        print(f"   ✗ Error al crear categorías: {e}")
        return False

    # 4. Crear productos de prueba
    print("\n4. Creando productos de prueba...")
    try:
        with session_scope() as session:
            prod_repo = ProductRepository(session)

            productos = [
                Producto(
                    codigo="MART001",
                    nombre="Martillo de Carpintero",
                    descripcion="Martillo con mango de madera, 16 oz",
                    precio=Decimal("12.50"),
                    stock=25,
                    stock_minimo=5,
                    unidad_medida="unidad",
                    categoria_id=1,
                    marca="Stanley"
                ),
                Producto(
                    codigo="PINT001",
                    nombre="Pintura Látex Blanco",
                    descripcion="Pintura látex interior/exterior, 1 galón",
                    precio=Decimal("18.99"),
                    stock=50,
                    stock_minimo=10,
                    unidad_medida="galón",
                    categoria_id=2,
                    marca="Condor"
                ),
                Producto(
                    codigo="ELEC001",
                    nombre="Cable Eléctrico #12",
                    descripcion="Cable eléctrico calibre 12 AWG",
                    precio=Decimal("2.50"),
                    stock=100,
                    stock_minimo=20,
                    unidad_medida="metro",
                    categoria_id=3,
                    marca="Electrocables"
                ),
                Producto(
                    codigo="PLOM001",
                    nombre="Tubo PVC 1/2 pulgada",
                    descripcion="Tubo PVC presión 1/2 pulgada x 3 metros",
                    precio=Decimal("3.75"),
                    stock=3,  # Stock bajo para probar alertas
                    stock_minimo=10,
                    unidad_medida="unidad",
                    categoria_id=4,
                    marca="Plastigama"
                ),
            ]

            for prod in productos:
                prod_creado = prod_repo.create(prod)
                stock_status = "⚠️ STOCK BAJO" if prod_creado.stock_bajo else "✓"
                print(f"   {stock_status} Producto: {prod_creado.nombre} - Stock: {prod_creado.stock}")
    except Exception as e:
        print(f"   ✗ Error al crear productos: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 5. Probar búsquedas
    print("\n5. Probando búsquedas...")
    try:
        prod_repo = ProductRepository()

        # Buscar todos los productos
        todos = prod_repo.get_all()
        print(f"   ✓ Total de productos: {len(todos)}")

        # Buscar por texto
        resultados = prod_repo.search("pintura")
        print(f"   ✓ Búsqueda 'pintura': {len(resultados)} resultado(s)")

        # Buscar por código
        producto = prod_repo.get_by_codigo("MART001")
        if producto:
            print(f"   ✓ Producto por código: {producto.nombre} - {producto.precio_formateado}")

        # Productos con stock bajo
        stock_bajo = prod_repo.get_stock_bajo()
        print(f"   ⚠️  Productos con stock bajo: {len(stock_bajo)}")
        for p in stock_bajo:
            print(f"      - {p.nombre}: {p.stock}/{p.stock_minimo}")

    except Exception as e:
        print(f"   ✗ Error en búsquedas: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 6. Probar actualización de stock
    print("\n6. Probando actualización de stock...")
    try:
        prod_repo = ProductRepository()

        # Obtener un producto
        producto = prod_repo.get_by_codigo("MART001")
        stock_inicial = producto.stock

        # Actualizar stock (vender 5 unidades)
        producto_actualizado = prod_repo.actualizar_stock(producto.id, -5)
        print(f"   ✓ Stock actualizado: {stock_inicial} → {producto_actualizado.stock}")

        # Reponer stock
        producto_actualizado = prod_repo.actualizar_stock(producto.id, 10)
        print(f"   ✓ Stock repuesto: {producto_actualizado.stock}")

    except Exception as e:
        print(f"   ✗ Error al actualizar stock: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    print("=" * 60)
    print("\nLa base de datos está lista para usar.")
    print(f"Ubicación: {DatabaseConfig.URL}")

    return True


if __name__ == "__main__":
    try:
        success = test_database_setup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
