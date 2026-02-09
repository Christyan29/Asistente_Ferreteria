"""
Script de prueba para verificar que el sistema de historial funciona correctamente.
Ejecutar: python scripts/test_history.py
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.conversation_service import ConversationService
from app.infrastructure.conversation_repository import ConversationRepository


def test_conversation_service():
    """Prueba el servicio de conversaciones"""
    print("=" * 60)
    print("PRUEBA: Sistema de Historial de Conversaciones")
    print("=" * 60)

    try:
        # Crear servicio
        print("\n1. Creando ConversationService...")
        service = ConversationService()
        print("✅ Servicio creado")

        # Guardar interacción de prueba
        print("\n2. Guardando interacción de prueba...")
        interaction_id = service.save_interaction(
            question="tienen martillos?",
            answer="Sí, tenemos Martillo Stanley. Disponible: 10 unidades a $1.50",
            intent="product_search",
            response_source="groq+database",
            response_time_ms=1200,
            confidence=0.95
        )
        print(f"✅ Interacción guardada con ID: {interaction_id}")

        # Guardar otra interacción
        print("\n3. Guardando segunda interacción...")
        interaction_id2 = service.save_interaction(
            question="como instalar una repisa?",
            answer="Herramientas necesarias: taladro, nivel, tornillos...",
            intent="instruction",
            response_source="knowledge_base",
            response_time_ms=800,
            confidence=None
        )
        print(f"✅ Segunda interacción guardada con ID: {interaction_id2}")

        # Obtener conversaciones recientes
        print("\n4. Obteniendo conversaciones recientes...")
        repo = ConversationRepository()
        conversations = repo.get_recent_conversations(limit=5)
        print(f"✅ Encontradas {len(conversations)} conversaciones")

        for conv in conversations:
            print(f"   - Sesión: {conv.session_id[:8]}... | Interacciones: {conv.total_interactions} | Inicio: {conv.started_at}")

        # Obtener detalles de la conversación actual
        if conversations:
            print("\n5. Obteniendo detalles de la conversación actual...")
            conv, interactions = repo.get_conversation_with_interactions(conversations[0].id)
            print(f"✅ Conversación: {conv.session_id[:8]}...")
            print(f"   Total de interacciones: {len(interactions)}")

            for i, inter in enumerate(interactions, 1):
                print(f"\n   Interacción {i}:")
                print(f"   Q: {inter.question}")
                print(f"   A: {inter.answer[:50]}...")
                print(f"   Tipo: {inter.intent_type} | Fuente: {inter.response_source} | Tiempo: {inter.response_time_ms}ms")

        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR EN PRUEBA: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    test_conversation_service()
