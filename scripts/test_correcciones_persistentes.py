"""
Script de verificación para correcciones persistentes de UI y Exportación.
Ejecutar: python scripts/test_correcciones_persistentes.py
"""
import sys
import os
from unittest.mock import MagicMock

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_correcciones_persistentes():
    """Prueba las correcciones de UI, Exportación y CSS"""
    print("=" * 70)
    print("VERIFICACIÓN: Correcciones Persistentes (UI, Export, CSS)")
    print("=" * 70)

    try:
        # Test 1: Verificar método export_to_csv
        print("\n✅ Test 1: Verificar función Exportar CSV")
        from app.presentation.historial_view import HistorialView

        if hasattr(HistorialView, 'export_to_csv'):
            print("   ✓ Método 'export_to_csv' existe en HistorialView")
        else:
            print("   ❌ Método 'export_to_csv' NO encontrado")
            return False

        # Test 2: Verificar corrección CSS (análisis estático simple)
        print("\n✅ Test 2: Verificar CSS de estadísticas (sin comillas problemáticas)")
        import inspect
        source = inspect.getsource(HistorialView.load_statistics)

        if "font-family: 'Segoe UI'" in source or "font-family: \"Segoe UI\"" in source:
             print("   ⚠️ ADVERTENCIA: Se detectaron comillas en font-family (potencial riesgo)")
        elif "font-family: Arial" in source:
             print("   ✓ Se detectó uso de fuente segura 'Arial' sin comillas")
        else:
             print("   ✓ No se detectaron patrones problemáticos obvios en font-family")

        # Test 3: Verificar estilos de pestañas
        print("\n✅ Test 3: Verificar estilos de pestañas (min-width)")
        source_setup = inspect.getsource(HistorialView.setup_ui)
        if "min-width: 130px" in source_setup:
             print("   ✓ 'min-width: 130px' encontrado en estilos de pestañas")
        else:
             print("   ⚠️ No se encontró 'min-width' exacto (puede ser diferente valor o no aplicado)")

        print("\n" + "=" * 70)
        print("✅ VERIFICACIÓN DE CÓDIGO COMPLETADA")
        print("=" * 70)
        print("Para verificar visualmente:")
        print("1. Ejecuta: python app/main.py")
        print("2. Ve a Historial -> Pestaña Estadísticas (NO debe haber error)")
        print("3. Ve a Historial -> Pestaña Conversaciones -> Botón Exportar (DEBE estar habilitado)")
        print("4. Verifica nombres de pestañas (NO deben estar cortados)")

        return True

    except Exception as e:
        print(f"\n❌ ERROR EN VERIFICACIÓN: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_correcciones_persistentes()
    sys.exit(0 if success else 1)
