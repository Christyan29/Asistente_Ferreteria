"""
Configuración centralizada de la aplicación.
Carga variables de entorno y proporciona configuraciones globales.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = BASE_DIR / "app"
DATABASE_DIR = BASE_DIR / "database"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = APP_DIR / "assets"

# Crear directorios si no existen
DATABASE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)


class DatabaseConfig:
    """Configuración de base de datos"""
    URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_DIR}/ferreteria.db")
    ECHO = os.getenv("DATABASE_ECHO", "False").lower() == "true"
    POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))


class OpenAIConfig:
    """Configuración de OpenAI API"""
    API_KEY = os.getenv("OPENAI_API_KEY", "")
    MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
    TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

    # Prompt del sistema para el asistente
    SYSTEM_PROMPT = """Eres un asistente virtual de la Ferretería Disensa en Pomasqui, Ecuador.
Tu función es ayudar a los clientes a encontrar materiales de construcción y ferretería.
Debes ser amable, profesional y proporcionar información precisa sobre productos disponibles.
Si un producto no está en el inventario, sugiere alternativas similares.
Responde de manera concisa y clara."""


class VoiceConfig:
    """Configuración de reconocimiento de voz"""
    LANGUAGE = os.getenv("VOICE_LANGUAGE", "es-ES")
    TIMEOUT = int(os.getenv("VOICE_TIMEOUT", "5"))
    PHRASE_TIME_LIMIT = int(os.getenv("VOICE_PHRASE_TIME_LIMIT", "10"))
    ENERGY_THRESHOLD = int(os.getenv("VOICE_ENERGY_THRESHOLD", "4000"))


class TTSConfig:
    """Configuración de Text-to-Speech"""
    LANGUAGE = os.getenv("TTS_LANGUAGE", "es")
    SPEED = int(os.getenv("TTS_SPEED", "150"))
    VOLUME = float(os.getenv("TTS_VOLUME", "0.9"))
    USE_GTTS = os.getenv("TTS_USE_GTTS", "True").lower() == "true"
    AUDIO_DIR = ASSETS_DIR / "audio"


class LoggingConfig:
    """Configuración de logging"""
    LEVEL = os.getenv("LOG_LEVEL", "INFO")
    FILE = LOGS_DIR / "app.log"
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
    BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))


class AvatarConfig:
    """Configuración del avatar"""
    FPS = int(os.getenv("AVATAR_FPS", "30"))
    AVATAR_DIR = ASSETS_DIR / "avatar"
    DEFAULT_STATE = "idle"
    STATES = ["idle", "listening", "thinking", "speaking"]


class AppConfig:
    """Configuración general de la aplicación"""
    NAME = os.getenv("APP_NAME", "Asistente Virtual Ferretería Disensa")
    VERSION = os.getenv("APP_VERSION", "1.0.0")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Configuraciones de UI
    WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1200"))
    WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "800"))
    THEME = os.getenv("THEME", "dark")


# Validar configuraciones críticas
def validate_config():
    """Valida que las configuraciones críticas estén presentes"""
    errors = []

    if not OpenAIConfig.API_KEY or OpenAIConfig.API_KEY == "sk-your-api-key-here":
        errors.append("OPENAI_API_KEY no está configurada correctamente en .env")

    if not DATABASE_DIR.exists():
        errors.append(f"El directorio de base de datos no existe: {DATABASE_DIR}")

    if errors:
        raise ValueError(f"Errores de configuración:\n" + "\n".join(f"- {e}" for e in errors))


# Exportar todas las configuraciones
__all__ = [
    "BASE_DIR",
    "APP_DIR",
    "DATABASE_DIR",
    "LOGS_DIR",
    "ASSETS_DIR",
    "DatabaseConfig",
    "OpenAIConfig",
    "VoiceConfig",
    "TTSConfig",
    "LoggingConfig",
    "AvatarConfig",
    "AppConfig",
    "validate_config",
]
