"""
Script de migración para crear tablas de historial de conversaciones.
Ejecutar: python scripts/migrate_add_history.py
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.infrastructure.database import get_database
from app.infrastructure.models.conversation import ConversationModel, InteractionModel


def migrate():
    """Crea las tablas de historial en la base de datos"""
    print("=" * 60)
    print("MIGRACIÓN: Creando tablas de historial de conversaciones")
    print("=" * 60)

    try:
        db = get_database()

        # Crear tablas
        print("\n📋 Creando tabla 'conversations'...")
        ConversationModel.__table__.create(db.engine, checkfirst=True)
        print("✅ Tabla 'conversations' creada")

        print("\n📋 Creando tabla 'interactions'...")
        InteractionModel.__table__.create(db.engine, checkfirst=True)
        print("✅ Tabla 'interactions' creada")

        print("\n" + "=" * 60)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR EN MIGRACIÓN: {e}")
        raise


if __name__ == "__main__":
    migrate()
