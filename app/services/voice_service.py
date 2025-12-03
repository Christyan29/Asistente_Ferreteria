"""
Servicio de Reconocimiento de Voz (STT).
Permite que el asistente escuche comandos del usuario.
"""
import speech_recognition as sr
import logging

logger = logging.getLogger(__name__)

class VoiceService:
    """
    Servicio para convertir voz a texto.
    """
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self._initialize_microphone()

    def _initialize_microphone(self):
        """Inicializa el micrófono con mejor manejo de errores"""
        try:
            # Listar dispositivos disponibles
            logger.info("Buscando dispositivos de audio...")

            # Intentar con el micrófono por defecto
            self.microphone = sr.Microphone()

            # Probar que funciona
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)

            logger.info("✅ Micrófono inicializado correctamente")

        except OSError as e:
            logger.error(f"❌ Error de sistema al acceder al micrófono: {e}")
            logger.error("Verifica que:")
            logger.error("  1. El micrófono esté conectado")
            logger.error("  2. Los drivers estén instalados")
            logger.error("  3. Windows tenga permisos de micrófono para Python")
            self.microphone = None
        except Exception as e:
            logger.error(f"❌ Error inesperado al inicializar micrófono: {e}")
            self.microphone = None

    def is_available(self):
        """Verifica si el servicio de voz está disponible"""
        return self.microphone is not None

    def listen(self, timeout=5, phrase_time_limit=10):
        """
        Escucha el micrófono y devuelve el texto reconocido.

        Args:
            timeout (int): Segundos a esperar antes de dejar de escuchar si no hay voz.
            phrase_time_limit (int): Duración máxima de la frase.

        Returns:
            str: Texto reconocido o None si hubo error/silencio.
        """
        if not self.microphone:
            logger.error("Micrófono no disponible")
            return None

        try:
            with self.microphone as source:
                logger.info("Ajustando ruido ambiental...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

                logger.info("Escuchando...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

                logger.info("Reconociendo...")
                # Usar Google Speech Recognition (requiere internet)
                # language='es-ES' para español de España, o 'es-MX' para México
                text = self.recognizer.recognize_google(audio, language="es-ES")
                logger.info(f"Texto reconocido: {text}")
                return text

        except sr.WaitTimeoutError:
            logger.warning("Tiempo de espera agotado (silencio)")
            return None
        except sr.UnknownValueError:
            logger.warning("No se entendió el audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Error de conexión con servicio de reconocimiento: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al escuchar: {e}")
            return None

# Instancia global
_voice_service = None

def get_voice_service():
    """Obtiene o crea la instancia del servicio de voz"""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
