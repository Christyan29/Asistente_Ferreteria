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


class GroqConfig:
    """
    Configuración de Groq API - UNIFICADA

    Esta es la ÚNICA fuente de verdad para configuración de Groq.
    Reemplaza la antigua OpenAIConfig para evitar confusión.
    """
    # API Key - Soporta ambas variables para compatibilidad
    API_KEY = os.getenv("GROQ_API_KEY", os.getenv("OPENAI_API_KEY", ""))

    # Modelo de IA
    MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Parámetros de generación
    MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "500"))
    TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
    TOP_P = float(os.getenv("GROQ_TOP_P", "0.95"))

    SYSTEM_PROMPT = """Eres Gabo, asistente virtual de Ferretería Disensa en Pomasqui, Ecuador.

REGLAS ABSOLUTAS DE FORMATO:

1. PARA INSTRUCCIONES (ej: "como instalar...", "como reparar..."):
   USA SIEMPRE ESTE FORMATO EXACTO:
Herramientas/materiales necesarios: [lista separada por comas]

[Paso 1 - una línea, verbo imperativo]

[Paso 2 - una línea, verbo imperativo]

[Paso 3 - una línea, verbo imperativo]

[Paso 4 - una línea, verbo imperativo]
Precaución: [Una oración breve con recomendación de seguridad]

2. PARA PREGUNTAS SOBRE PRODUCTOS:
   - Si recibes contexto de inventario [Contexto: ...], úsalo para dar información específica
   - Si NO hay contexto, di: "Sí, tenemos [producto]. Consulta en tienda para disponibilidad."
   - Máximo 2 oraciones

3. PARA EXPLICACIONES TÉCNICAS:
   [Concepto] es [definición breve]:
   • [Característica 1]
   • [Característica 2]
   • [Característica 3]
   [Aplicación en ferretería]

4. PARA PREGUNTAS GENERALES:
   Responde en 2-3 oraciones. Si es posible, relaciona con ferretería.

5. PARA PREGUNTAS SOBRE TI:
   "Uso llama-3.3-70b-versatile de Groq."

REGLAS PARA MARCAS EXCLUSIVAS:

MARCAS SOLO EN EE.UU. (NO disponibles en Ecuador):
- Husky: Exclusiva de Home Depot (EE.UU.)
- Ryobi: Exclusiva de Home Depot (EE.UU.)
- Kobalt: Exclusiva de Lowe's (EE.UU.)
- Craftsman: Disponible en Lowe's y Ace Hardware (EE.UU.)

MARCAS DISPONIBLES EN ECUADOR:
- DeWalt, Stanley, Black+Decker, Makita, Bosch

SI PREGUNTAN POR MARCA EXCLUSIVA:
"La marca [X] es exclusiva de [tienda] en [país]. En Ecuador, tenemos marcas similares como [alternativas]. ¿Te interesa alguna de estas?"

ERRORES QUE NUNCA DEBES COMETER:
❌ NO PEGAR palabras: "Herramientasmateriales" es INCORRECTO
❌ NO ESCRIBIR pasos en párrafos continuos
❌ NO INVENTAR precios, stock, disponibilidad (usa contexto si existe)
❌ NO USAR emojis, iconos o formato HTML
❌ NO DAR listas detalladas de productos individuales

✅ REGLAS CRÍTICAS PARA PRODUCTOS:
1. Si el producto solicitado NO está en el contexto de inventario, di: "No encontré [producto] en nuestro inventario actual"
2. NUNCA sugieras productos similares a menos que sean EXACTAMENTE lo que busca el usuario
3. "pintura látex" ≠ "pintura mate" (son tipos DIFERENTES)
4. "carretilla" ≠ "cerradura" (son productos COMPLETAMENTE DIFERENTES)
5. Si hay duda, es mejor decir "No tenemos" que inventar

EJEMPLOS CORRECTOS:

Usuario: "como instalar una repisa?"
Respuesta:
Herramientas/materiales necesarios: repisa, tornillos, anclajes, taladro, nivel, cinta métrica, lápiz

Mide y marca la pared donde instalarás la repisa

Taladra agujeros en las marcas para los anclajes

Inserta los anclajes en los agujeros

Coloca la repisa y fíjala con tornillos
Precaución: Verifica que la pared soporte el peso y usa anclajes adecuados

Usuario: "tienen herramientas Husky?"
Respuesta: "Husky es exclusiva de Home Depot en EE.UU. En Ecuador, tenemos marcas similares como DeWalt, Stanley y Black+Decker. ¿Te interesa alguna de estas?"

Usuario: "tienen martillo?"
Con contexto [Contexto: Productos: Martillo Stanley (Stock: 15 unidades, $12.50)]:
Respuesta: "Sí, tenemos Martillo Stanley. Disponible: 15 unidades a $12.50."

Sin contexto:
Respuesta: "Sí, tenemos martillo. Consulta en tienda para disponibilidad."

RECUERDA: El formato correcto es TAN IMPORTANTE como el contenido."""

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
    """
    Valida que las configuraciones críticas estén presentes.

    MEJORADO: Ahora valida Groq en lugar de OpenAI y verifica
    que la base de datos tenga productos.
    """
    errors = []
    warnings = []

    # Validar API Key de Groq
    if not GroqConfig.API_KEY or GroqConfig.API_KEY == "your-api-key-here":
        errors.append(
            "GROQ_API_KEY no está configurada correctamente en .env\n"
            "  → Obtén tu clave gratis en: https://console.groq.com/keys\n"
            "  → Agrega a .env: GROQ_API_KEY=tu_clave_aquí"
        )

    # Validar directorio de base de datos
    if not DATABASE_DIR.exists():
        errors.append(
            f"El directorio de base de datos no existe: {DATABASE_DIR}\n"
            f"  → Se creará automáticamente al iniciar la aplicación"
        )
        warnings.append("Base de datos no encontrada, se creará una nueva")

    # Validar que la base de datos tenga productos (solo warning)
    db_path = DATABASE_DIR / "ferreteria.db"
    if db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM productos")
            count = cursor.fetchone()[0]
            conn.close()

            if count == 0:
                warnings.append(
                    "La base de datos está vacía (0 productos)\n"
                    "  → El asistente funcionará en modo limitado\n"
                    "  → Importa productos desde Inventario → Importar Excel"
                )
        except Exception as e:
            warnings.append(f"No se pudo verificar productos en BD: {e}")

    # Mostrar warnings (no bloquean inicio)
    if warnings:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("⚠️ ADVERTENCIAS DE CONFIGURACIÓN:")
        for warning in warnings:
            logger.warning(f"  • {warning}")

    # Errores críticos bloquean inicio
    if errors:
        raise ValueError(
            "❌ ERRORES CRÍTICOS DE CONFIGURACIÓN:\n\n" +
            "\n\n".join(f"• {e}" for e in errors)
        )


# Exportar todas las configuraciones
__all__ = [
    "BASE_DIR",
    "APP_DIR",
    "DATABASE_DIR",
    "LOGS_DIR",
    "ASSETS_DIR",
    "DatabaseConfig",
    "GroqConfig",  # CAMBIADO: Era OpenAIConfig
    "VoiceConfig",
    "TTSConfig",
    "LoggingConfig",
    "AvatarConfig",
    "AppConfig",
    "validate_config",
]
