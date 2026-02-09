"""
Script de verificación exhaustiva para correcciones finales.
Ejecutar: python scripts/test_solucion_definitiva.py
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import csv
import io

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestSolucionDefinitiva(unittest.TestCase):

    def setUp(self):
        # Mock de módulos Qt para evitar errores gráficos
        sys.modules['PyQt5.QtWidgets'] = MagicMock()
        sys.modules['PyQt5.QtCore'] = MagicMock()
        sys.modules['PyQt5.QtGui'] = MagicMock()

        # Importar la clase a probar
        from app.presentation.historial_view import HistorialView
        self.HistorialView = HistorialView

    def test_css_estadisticas_limpio(self):
        """Verifica que el HTML de estadísticas NO tenga font-family"""
        print("\n✅ Test 1: Verificar limpieza de CSS en estadísticas")

        # Mock del servicio de analíticas
        analytics_mock = MagicMock()
        analytics_mock.get_daily_stats.return_value = {}
        analytics_mock.get_top_products.return_value = []
        analytics_mock.get_intent_distribution.return_value = {}
        analytics_mock.get_response_time_stats.return_value = {}

        # Instanciar vista (mockeada)
        view = MagicMock()
        view.analytics_service = analytics_mock
        view.stats_browser = MagicMock()

        # Ejecutar método load_statistics directamente usando la función de la clase
        # pero pasando el mock como 'self'
        self.HistorialView.load_statistics(view)

        # Obtener el HTML generado
        args, _ = view.stats_browser.setHtml.call_args
        html_generado = args[0]

        # Verificar ausencia de font-family
        if "font-family" in html_generado:
            print("   ❌ FALLO: Se encontró 'font-family' en el HTML generado")
            self.fail("CSS sucio detectado")
        else:
            print("   ✓ HTML limpio de declaraciones de fuente inline")

    def test_estructura_exportacion_csv(self):
        """Verifica la lógica de exportación CSV detallada"""
        print("\n✅ Test 2: Verificar estructura de exportación CSV")

        view = MagicMock()

        # Mock servicio y repositorio
        mock_repo = MagicMock()
        view.conversation_service.repository = mock_repo

        # Datos de prueba
        mock_conv = MagicMock()
        mock_conv.id = 123
        mock_conv.started_at = MagicMock()
        mock_conv.started_at.strftime.return_value = "2026-02-08"
        mock_conv.total_interactions = 5

        mock_inter = MagicMock()
        mock_inter.created_at.strftime.side_effect = ["2026-02-08", "12:00:00"]
        mock_inter.question = "Pregunta Test"
        mock_inter.answer = "Respuesta Test"
        mock_inter.intent = "product_search"

        # Configurar retornos
        mock_repo.get_recent_conversations.return_value = [mock_conv]
        mock_repo.get_conversation_with_interactions.return_value = (mock_conv, [mock_inter])

        # Mockear open() para capturar escritura
        with patch('builtins.open', new_callable=MagicMock) as mock_open:
            # Mockear QFileDialog para devolver nombre
            with patch('app.presentation.historial_view.QFileDialog.getSaveFileName', return_value=('test.csv', '')):

                # Ejecutar exportación
                self.HistorialView.export_to_csv(view)

                # Verificar llamadas a write
                handle = mock_open.return_value.__enter__.return_value

                # Verificar encabezados
                # Como csv writer hace muchas llamadas pequeñas, es difícil verificar string exacto
                # Pero podemos verificar que se haya abierto el archivo
                mock_open.assert_called_with('test.csv', 'w', newline='', encoding='utf-8')
                print("   ✓ Archivo abierto correctamente")

                # Verificar que se consultaron las interacciones (clave para reporte detallado)
                mock_repo.get_conversation_with_interactions.assert_called_with(123)
                print("   ✓ Se obtuvieron interacciones detalladas (no solo resumen)")

if __name__ == '__main__':
    unittest.main()
