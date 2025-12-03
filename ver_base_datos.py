"""
Script para visualizar el contenido de la base de datos de forma amigable.
"""
import sqlite3
import pandas as pd
from pathlib import Path

def visualizar_base_datos():
    """Muestra el contenido de la base de datos"""

    db_path = Path('database/ferreteria.db')

    if not db_path.exists():
        print("❌ No se encontró la base de datos en: database/ferreteria.db")
        print("   Asegúrate de haber ejecutado la aplicación al menos una vez.")
        return

    # Conectar a la base de datos
    conn = sqlite3.connect(str(db_path))

    print("=" * 80)
    print("📊 VISUALIZADOR DE BASE DE DATOS - FERRETERÍA DISENSA")
    print("=" * 80)

    # Mostrar categorías
    print("\n📁 CATEGORÍAS:")
    print("-" * 80)
    categorias = pd.read_sql_query("""
        SELECT id, nombre, descripcion,
               (SELECT COUNT(*) FROM productos WHERE categoria_id = categorias.id) as total_productos
        FROM categorias
        WHERE activo = 1
        ORDER BY nombre
    """, conn)

    if len(categorias) > 0:
        print(categorias.to_string(index=False))
        print(f"\nTotal de categorías: {len(categorias)}")
    else:
        print("No hay categorías registradas.")

    # Mostrar productos
    print("\n\n📦 PRODUCTOS:")
    print("-" * 80)
    productos = pd.read_sql_query("""
        SELECT
            p.codigo as Código,
            p.nombre as Nombre,
            c.nombre as Categoría,
            p.precio as Precio,
            p.stock as Stock,
            p.stock_minimo as 'Stock Mín',
            p.unidad_medida as Unidad,
            p.marca as Marca,
            p.ubicacion as Ubicación,
            CASE
                WHEN p.stock <= p.stock_minimo THEN '⚠️ BAJO'
                ELSE '✅ OK'
            END as Estado
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        WHERE p.activo = 1
        ORDER BY c.nombre, p.nombre
    """, conn)

    if len(productos) > 0:
        # Configurar pandas para mostrar todas las columnas
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)

        print(productos.to_string(index=False))
        print(f"\n📊 Total de productos: {len(productos)}")

        # Estadísticas
        productos_bajo_stock = len(productos[productos['Estado'] == '⚠️ BAJO'])
        if productos_bajo_stock > 0:
            print(f"⚠️  Productos con stock bajo: {productos_bajo_stock}")

        # Valor total del inventario
        valor_total = (productos['Precio'] * productos['Stock']).sum()
        print(f"💰 Valor total del inventario: ${valor_total:,.2f}")

    else:
        print("No hay productos registrados.")
        print("\n💡 Tip: Importa productos desde Excel o agrégalos manualmente en la aplicación.")

    conn.close()

    print("\n" + "=" * 80)
    print("✅ Visualización completada")
    print("=" * 80)

if __name__ == "__main__":
    visualizar_base_datos()
