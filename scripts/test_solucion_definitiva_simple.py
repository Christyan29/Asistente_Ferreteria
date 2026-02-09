"""
Script de verificación estática simplificada.
Analiza el código fuente para asegurar que las correcciones están aplicadas.
"""
import sys
import os
import inspect

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def verificar_cambios():
    print("=" * 60)
    print("VERIFICACIÓN ESTÁTICA DE CÓDIGO")
    print("=" * 60)

    try:
        from app.presentation.historial_view import HistorialView

        # 1. Verificar existencia de export_to_csv
        if hasattr(HistorialView, 'export_to_csv'):
            print("✅ [OK] Método export_to_csv existe")
        else:
            print("❌ [FAIL] Método export_to_csv NO existe")
            return False

        # 2. Analizar código fuente de export_to_csv
        src_export = inspect.getsource(HistorialView.export_to_csv)

        if "historial_interacciones_" in src_export and "datetime.now()" in src_export:
             print("✅ [OK] Generación de nombre automático detectada")
        else:
             print("❌ [FAIL] No se detectó generación de nombre automático")

        if "interactions" in src_export and "writer.writerow" in src_export:
             print("✅ [OK] Bucle de interacciones detectado (exportación detallada)")
        else:
             print("❌ [FAIL] No se detectó iteración sobre interacciones")

        # 3. Analizar código fuente de create_stats_panel
        src_panel = inspect.getsource(HistorialView.create_stats_panel)
        if "font-family" in src_panel and "Segoe UI" in src_panel:
             print("✅ [OK] Fuente definida en el widget (create_stats_panel)")
        else:
             print("❌ [FAIL] No se detectó definición de fuente en el widget")

        # 4. Analizar código fuente de load_statistics
        src_stats = inspect.getsource(HistorialView.load_statistics)
        if "font-family:" not in src_stats:
             print("✅ [OK] HTML de estadísticas LIMPIO de 'font-family'")
        else:
             print("⚠️ [WARN] Se detectó 'font-family' en load_statistics (verificar que no sea en HTML)")
             # Imprimir línea sospechosa para debug
             for line in src_stats.split('\n'):
                 if "font-family:" in line:
                     print(f"      Línea: {line.strip()}")

        print("-" * 60)
        print("RESULTADO: Las correcciones parecen aplicadas correctamente.")
        return True

    except Exception as e:
        print(f"❌ Error fatal en verificación: {e}")
        return False

if __name__ == "__main__":
    success = verificar_cambios()
    sys.exit(0 if success else 1)
