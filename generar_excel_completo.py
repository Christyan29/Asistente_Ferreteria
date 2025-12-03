"""
Script para generar archivos Excel de prueba con productos de ferretería.
Útil para probar la funcionalidad de importación masiva.
"""
import pandas as pd
from datetime import datetime

def generar_excel_completo():
    """Genera un archivo Excel con productos variados de ferretería"""

    productos = {
        'Nombre': [
            # Herramientas
            'Martillo de Carpintero 16oz',
            'Destornillador Plano 1/4"',
            'Destornillador Phillips #2',
            'Alicate Universal 8"',
            'Llave Inglesa 12"',
            'Sierra de Mano 24"',
            'Taladro Eléctrico 1/2"',
            'Nivel de Burbuja 24"',
            'Cinta Métrica 5m',
            'Escuadra de Carpintero',

            # Pinturas
            'Pintura Látex Blanca 1 Galón',
            'Pintura Látex Beige 1 Galón',
            'Pintura Esmalte Negro 1/4 Galón',
            'Brocha 2"',
            'Brocha 4"',
            'Rodillo 9"',
            'Thinner 1 Litro',

            # Electricidad
            'Cable Eléctrico #12 AWG',
            'Cable Eléctrico #14 AWG',
            'Tomacorriente Doble',
            'Interruptor Simple',
            'Interruptor Doble',
            'Cinta Aislante Negra',
            'Foco LED 9W',
            'Foco LED 12W',

            # Plomería
            'Tubo PVC 1/2" x 3m',
            'Tubo PVC 3/4" x 3m',
            'Codo PVC 1/2"',
            'Codo PVC 3/4"',
            'Tee PVC 1/2"',
            'Pegamento PVC 1/4 Litro',
            'Llave de Paso 1/2"',
            'Llave de Lavamanos',

            # Construcción
            'Cemento Gris 50kg',
            'Arena Fina m³',
            'Ripio m³',
            'Ladrillo Común (unidad)',
            'Bloque 15cm',
            'Varilla 12mm x 6m',
            'Alambre Galvanizado #18',

            # Fijación
            'Clavo 2" (libra)',
            'Clavo 3" (libra)',
            'Tornillo 1" (caja 100)',
            'Tornillo 2" (caja 100)',
            'Taco Fisher #8',
            'Perno 1/4" x 2"',
        ],

        'Categoría': [
            # Herramientas (10)
            'Herramientas', 'Herramientas', 'Herramientas', 'Herramientas', 'Herramientas',
            'Herramientas', 'Herramientas', 'Herramientas', 'Herramientas', 'Herramientas',

            # Pinturas (7)
            'Pinturas', 'Pinturas', 'Pinturas', 'Pinturas', 'Pinturas', 'Pinturas', 'Pinturas',

            # Electricidad (8)
            'Electricidad', 'Electricidad', 'Electricidad', 'Electricidad', 'Electricidad',
            'Electricidad', 'Electricidad', 'Electricidad',

            # Plomería (8)
            'Plomería', 'Plomería', 'Plomería', 'Plomería', 'Plomería',
            'Plomería', 'Plomería', 'Plomería',

            # Construcción (7)
            'Construcción', 'Construcción', 'Construcción', 'Construcción', 'Construcción',
            'Construcción', 'Construcción',

            # Fijación (6)
            'Fijación', 'Fijación', 'Fijación', 'Fijación', 'Fijación', 'Fijación',
        ],

        'Precio': [
            # Herramientas
            15.50, 3.25, 3.50, 8.75, 12.00, 18.50, 85.00, 14.50, 6.75, 5.25,

            # Pinturas
            25.00, 25.00, 8.50, 2.50, 3.50, 4.75, 5.00,

            # Electricidad
            1.20, 0.95, 2.50, 1.75, 2.25, 1.50, 3.50, 4.50,

            # Plomería
            8.50, 10.00, 0.75, 0.85, 0.90, 6.50, 12.00, 35.00,

            # Construcción
            8.50, 25.00, 28.00, 0.25, 0.45, 12.50, 2.50,

            # Fijación
            2.50, 3.00, 4.50, 5.50, 0.15, 0.25,
        ],

        'Stock': [
            # Herramientas
            30, 45, 50, 25, 18, 12, 8, 20, 35, 28,

            # Pinturas
            50, 45, 30, 60, 55, 40, 25,

            # Electricidad
            100, 120, 75, 80, 65, 90, 150, 140,

            # Plomería
            40, 35, 100, 95, 85, 20, 15, 10,

            # Construcción
            200, 15, 12, 5000, 800, 50, 100,

            # Fijación
            150, 140, 80, 75, 500, 300,
        ],

        'Unidad': [
            # Herramientas
            'unidad', 'unidad', 'unidad', 'unidad', 'unidad', 'unidad', 'unidad', 'unidad', 'unidad', 'unidad',

            # Pinturas
            'galón', 'galón', 'galón', 'unidad', 'unidad', 'unidad', 'litro',

            # Electricidad
            'metro', 'metro', 'unidad', 'unidad', 'unidad', 'unidad', 'unidad', 'unidad',

            # Plomería
            'unidad', 'unidad', 'unidad', 'unidad', 'unidad', 'litro', 'unidad', 'unidad',

            # Construcción
            'saco', 'm³', 'm³', 'unidad', 'unidad', 'unidad', 'libra',

            # Fijación
            'libra', 'libra', 'caja', 'caja', 'unidad', 'unidad',
        ],

        'Stock Mínimo': [
            # Herramientas
            5, 10, 10, 5, 5, 3, 2, 5, 10, 5,

            # Pinturas
            10, 10, 5, 15, 15, 10, 5,

            # Electricidad
            20, 20, 15, 15, 15, 20, 30, 30,

            # Plomería
            10, 10, 20, 20, 20, 5, 3, 2,

            # Construcción
            50, 5, 5, 1000, 200, 10, 20,

            # Fijación
            30, 30, 20, 20, 100, 100,
        ],

        'Marca': [
            # Herramientas
            'Stanley', 'Stanley', 'Stanley', 'Truper', 'Truper', 'Bahco', 'DeWalt', 'Stanley', 'Stanley', 'Truper',

            # Pinturas
            'Condor', 'Condor', 'Condor', 'Condor', 'Condor', 'Condor', 'Condor',

            # Electricidad
            'Electrocables', 'Electrocables', 'Bticino', 'Bticino', 'Bticino', '3M', 'Philips', 'Philips',

            # Plomería
            'Plastigama', 'Plastigama', 'Plastigama', 'Plastigama', 'Plastigama', 'Plastigama', 'FV', 'FV',

            # Construcción
            'Holcim', 'Local', 'Local', 'Bloques Cotopaxi', 'Bloques Cotopaxi', 'Adelca', 'Ideal',

            # Fijación
            'Clavos Ecuador', 'Clavos Ecuador', 'Tornillos SA', 'Tornillos SA', 'Fisher', 'Pernos SA',
        ],

        'Ubicación': [
            # Herramientas
            'A1', 'A1', 'A1', 'A2', 'A2', 'A3', 'A3', 'A4', 'A4', 'A5',

            # Pinturas
            'B1', 'B1', 'B2', 'B3', 'B3', 'B3', 'B4',

            # Electricidad
            'C1', 'C1', 'C2', 'C2', 'C2', 'C3', 'C4', 'C4',

            # Plomería
            'D1', 'D1', 'D2', 'D2', 'D2', 'D3', 'D4', 'D4',

            # Construcción
            'E1', 'Patio', 'Patio', 'Patio', 'Patio', 'E2', 'E3',

            # Fijación
            'F1', 'F1', 'F2', 'F2', 'F3', 'F3',
        ]
    }

    df = pd.DataFrame(productos)

    # Generar nombre de archivo con fecha
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f'inventario_ferreteria_{fecha}.xlsx'

    df.to_excel(nombre_archivo, index=False)

    print(f"✅ Archivo generado: {nombre_archivo}")
    print(f"📊 Total de productos: {len(df)}")
    print(f"📁 Categorías: {df['Categoría'].nunique()}")
    print(f"\nCategorías incluidas:")
    for cat in df['Categoría'].unique():
        count = len(df[df['Categoría'] == cat])
        print(f"  - {cat}: {count} productos")

    return nombre_archivo

if __name__ == "__main__":
    generar_excel_completo()
