"""
Punto de entrada principal de la aplicación.
Inicializa la aplicación PyQt5 y la ventana principal.
"""
import sys
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

# Configurar el path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import LoggingConfig, AppConfig, DATABASE_DIR
from app.infrastructure.database import init_database
from app.presentation.main_window import MainWindow


def setup_logging():
    """Configura el sistema de logging"""
    logging.basicConfig(
        level=getattr(logging, LoggingConfig.LEVEL),
        format=LoggingConfig.FORMAT,
        handlers=[
            logging.FileHandler(LoggingConfig.FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info(f"Iniciando {AppConfig.NAME} v{AppConfig.VERSION}")
    logger.info("=" * 60)
    return logger


def check_database():
    """Verifica y crea la base de datos si no existe"""
    db_path = DATABASE_DIR / "ferreteria.db"

    if not db_path.exists():
        logger = logging.getLogger(__name__)
        logger.info("Base de datos no encontrada. Creando nueva base de datos...")
        try:
            init_database()
            logger.info("Base de datos creada exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error al crear base de datos: {e}")
            return False
    else:
        logger = logging.getLogger(__name__)
        logger.info(f"Base de datos encontrada: {db_path}")
        return True


def main():
    """Función principal de la aplicación"""
    # Configurar logging
    logger = setup_logging()

    try:
        # Verificar/crear base de datos
        if not check_database():
            print("Error: No se pudo inicializar la base de datos")
            return 1

        # Crear aplicación Qt
        app = QApplication(sys.argv)
        app.setApplicationName(AppConfig.NAME)
        app.setApplicationVersion(AppConfig.VERSION)

        # Configurar atributos de la aplicación
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        logger.info("Aplicación Qt inicializada")

        # Crear y mostrar ventana principal
        window = MainWindow()
        window.show()

        logger.info("Ventana principal mostrada")
        logger.info("Aplicación lista para usar")

        # Ejecutar aplicación
        exit_code = app.exec_()

        logger.info(f"Aplicación finalizada con código: {exit_code}")
        return exit_code

    except Exception as e:
        logger.error(f"Error fatal en la aplicación: {e}", exc_info=True)

        # Mostrar mensaje de error al usuario
        try:
            QMessageBox.critical(
                None,
                "Error Fatal",
                f"Ocurrió un error fatal:\n\n{str(e)}\n\nLa aplicación se cerrará."
            )
        except:
            print(f"Error fatal: {e}")

        return 1


if __name__ == "__main__":
    sys.exit(main())
