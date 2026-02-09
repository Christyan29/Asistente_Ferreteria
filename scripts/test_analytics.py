"""
Script de prueba para verificar el servicio de analíticas y queries del repositorio.
Ejecutar: python scripts/test_analytics.py
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.analytics_service import AnalyticsService
from app.infrastructure.conversation_repository import ConversationRepository


def test_analytics():
    """Prueba el servicio de analíticas y los métodos del repositorio"""
    print("=" * 70)
    print("PRUEBA: Servicio de Analíticas - Fase 3")
    print("=" * 70)

    try:
        # Test 1: Inicializar servicio
        print("\n✅ Test 1: Inicialización del servicio")
        service = AnalyticsService()
        print("   ✓ AnalyticsService inicializado correctamente")

        # Test 2: Top productos
        print("\n✅ Test 2: Top productos consultados")
        top_products = service.get_top_products(limit=5)
        if top_products:
            print(f"   ✓ Se encontraron {len(top_products)} productos:")
            for i, (product, count) in enumerate(top_products, 1):
                print(f"      {i}. {product[:50]}... ({count} consultas)")
        else:
            print("   ⚠️  No hay productos consultados aún")

        # Test 3: Distribución de intenciones
        print("\n✅ Test 3: Distribución de intenciones")
        intent_dist = service.get_intent_distribution()
        if intent_dist:
            print(f"   ✓ Se encontraron {len(intent_dist)} tipos de intenciones:")
            for intent_type, data in intent_dist.items():
                print(f"      • {intent_type}: {data['count']} ({data['percentage']}%)")
        else:
            print("   ⚠️  No hay datos de intenciones aún")

        # Test 4: Estadísticas diarias
        print("\n✅ Test 4: Estadísticas diarias")
        daily_stats = service.get_daily_stats()
        if daily_stats:
            print(f"   ✓ Total de conversaciones: {daily_stats['total_conversations']}")
            print(f"   ✓ Total de interacciones: {daily_stats['total_interactions']}")
            print(f"   ✓ Promedio conversaciones/día: {daily_stats['avg_conversations_per_day']}")
            print(f"   ✓ Promedio interacciones/día: {daily_stats['avg_interactions_per_day']}")
            print(f"   ✓ Días analizados: {daily_stats['days_analyzed']}")
        else:
            print("   ⚠️  No hay estadísticas diarias disponibles")

        # Test 5: Estadísticas de tiempo de respuesta
        print("\n✅ Test 5: Estadísticas de tiempo de respuesta")
        time_stats = service.get_response_time_stats()
        if time_stats and time_stats.get('avg_ms', 0) > 0:
            print(f"   ✓ Tiempo mínimo: {time_stats['min_s']}s ({time_stats['min_ms']}ms)")
            print(f"   ✓ Tiempo máximo: {time_stats['max_s']}s ({time_stats['max_ms']}ms)")
            print(f"   ✓ Tiempo promedio: {time_stats['avg_s']}s ({time_stats['avg_ms']}ms)")
        else:
            print("   ⚠️  No hay estadísticas de tiempo disponibles")

        # Test 6: Resumen completo
        print("\n✅ Test 6: Resumen completo")
        summary = service.get_complete_summary()
        print(f"   ✓ Resumen generado con {len(summary)} secciones")

        # Test 7: Verificar métodos del repositorio directamente
        print("\n✅ Test 7: Métodos del repositorio")
        repo = ConversationRepository()

        total_conv = repo.get_total_conversations_count()
        print(f"   ✓ Total conversaciones (repo): {total_conv}")

        total_inter = repo.get_total_interactions_count()
        print(f"   ✓ Total interacciones (repo): {total_inter}")

        intent_counts = repo.get_intent_counts()
        print(f"   ✓ Tipos de intenciones (repo): {len(intent_counts)}")

        print("\n" + "=" * 70)
        print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("=" * 70)

        print("\n📊 RESUMEN DE FUNCIONALIDADES VERIFICADAS:")
        print("   1. ✅ AnalyticsService inicializa correctamente")
        print("   2. ✅ get_top_products() funciona")
        print("   3. ✅ get_intent_distribution() funciona")
        print("   4. ✅ get_daily_stats() funciona")
        print("   5. ✅ get_response_time_stats() funciona")
        print("   6. ✅ get_complete_summary() funciona")
        print("   7. ✅ Métodos del repositorio funcionan")

        print("\n✅ LISTO PARA INTEGRAR EN LA UI")

        return True

    except Exception as e:
        print(f"\n❌ ERROR EN PRUEBA: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_analytics()
    sys.exit(0 if success else 1)
