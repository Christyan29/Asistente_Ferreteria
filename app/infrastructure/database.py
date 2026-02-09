"""
Configuración de la base de datos.
Maneja la conexión, sesiones y creación de tablas.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from app.config.settings import DatabaseConfig
from app.infrastructure.models.producto import Base, ProductoModel, CategoriaModel
from app.infrastructure.models.conversation import ConversationModel, InteractionModel  # ✅ NUEVO

logger = logging.getLogger(__name__)


class Database:
    """Clase para manejar la conexión y sesiones de base de datos"""

    def __init__(self):
        """Inicializa el motor de base de datos"""
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()

    def _initialize_engine(self):
        """Crea el motor de SQLAlchemy"""
        # Configuración especial para SQLite
        connect_args = {}
        poolclass = None

        if "sqlite" in DatabaseConfig.URL:
            connect_args = {"check_same_thread": False}
            poolclass = StaticPool
            logger.info(f"Configurando SQLite: {DatabaseConfig.URL}")

        # Crear el motor
        self.engine = create_engine(
            DatabaseConfig.URL,
            echo=DatabaseConfig.ECHO,
            connect_args=connect_args,
            poolclass=poolclass,
            pool_pre_ping=True,  # Verifica conexiones antes de usarlas
        )

        # Habilitar foreign keys en SQLite
        if "sqlite" in DatabaseConfig.URL:
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        # Crear SessionLocal
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info("Motor de base de datos inicializado correctamente")

    def create_tables(self):
        """Crea todas las tablas en la base de datos"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Tablas creadas exitosamente")
        except Exception as e:
            logger.error(f"Error al crear tablas: {e}")
            raise

    def drop_tables(self):
        """Elimina todas las tablas (usar con precaución)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("Todas las tablas han sido eliminadas")
        except Exception as e:
            logger.error(f"Error al eliminar tablas: {e}")
            raise

    def get_session(self) -> Session:
        """Obtiene una nueva sesión de base de datos"""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Context manager para manejar sesiones de base de datos.
        Hace commit automático si no hay errores, rollback si hay excepciones.

        Uso:
            with db.session_scope() as session:
                session.add(producto)
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en transacción de base de datos: {e}")
            raise
        finally:
            session.close()

    def close(self):
        """Cierra el motor de base de datos"""
        if self.engine:
            self.engine.dispose()
            logger.info("Conexión a base de datos cerrada")


# Instancia global de la base de datos
_db_instance = None


def get_database() -> Database:
    """Obtiene la instancia singleton de la base de datos"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def init_database():
    """Inicializa la base de datos y crea las tablas"""
    db = get_database()
    db.create_tables()
    logger.info("Base de datos inicializada")
    return db


def get_session() -> Session:
    """Función helper para obtener una sesión"""
    db = get_database()
    return db.get_session()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager para sesiones de base de datos"""
    db = get_database()
    with db.session_scope() as session:
        yield session


# Exportar componentes principales
__all__ = [
    "Database",
    "get_database",
    "init_database",
    "get_session",
    "session_scope",
    "Base",
    "ProductoModel",
    "CategoriaModel",
]
