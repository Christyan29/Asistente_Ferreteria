"""
Servicio de Texto a Voz (TTS) usando pyttsx3.
Permite que el asistente hable las respuestas.
"""
import pyttsx3
import logging
import threading
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class TTSService(QObject):
    """
    Servicio para convertir texto a voz.
    Hereda de QObject para emitir señales si es necesario.
    """
    speaking_started = pyqtSignal()
    speaking_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        try:
            self.engine = pyttsx3.init()
            self._configurar_voz()
        except Exception as e:
            logger.error(f"Error al inicializar motor TTS: {e}")
            self.engine = None

    def _configurar_voz(self):
        """Configura la voz en español y parámetros de velocidad/volumen"""
        if not self.engine:
            return

        try:
            # Configurar velocidad (rate)
            self.engine.setProperty('rate', 160)  # Velocidad normal

            # Configurar volumen
            self.engine.setProperty('volume', 1.0)

            # Buscar voz en español
            voices = self.engine.getProperty('voices')
            voz_espanol = None

            for voice in voices:
                if "spanish" in voice.name.lower() or "es-es" in voice.id.lower() or "es_es" in voice.id.lower():
                    voz_espanol = voice.id
                    break

            # Si no encuentra español explícito, busca cualquier voz que contenga 'ES' o 'Mexico'
            if not voz_espanol:
                for voice in voices:
                    if "mexico" in voice.name.lower() or "sabina" in voice.name.lower() or "helena" in voice.name.lower():
                        voz_espanol = voice.id
                        break

            if voz_espanol:
                self.engine.setProperty('voice', voz_espanol)
                logger.info(f"Voz configurada: {voz_espanol}")
            else:
                logger.warning("No se encontró voz en español específica, usando predeterminada.")

        except Exception as e:
            logger.error(f"Error al configurar voz: {e}")

    def speak(self, text):
        """
        Habla el texto proporcionado en un hilo separado.

        Args:
            text (str): Texto a hablar.
        """
        if not self.engine:
            logger.error("Motor TTS no inicializado")
            return

        # Limpiar texto de caracteres HTML simples si los hay (básico)
        text = text.replace("<b>", "").replace("</b>", "").replace("<br>", ". ")

        # Ejecutar en hilo para no bloquear UI
        thread = threading.Thread(target=self._speak_thread, args=(text,))
        thread.daemon = True
        thread.start()

    def _speak_thread(self, text):
        """Función interna para ejecutar en hilo"""
        try:
            self.speaking_started.emit()
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error durante el habla: {e}")
        finally:
            self.speaking_finished.emit()

    def stop(self):
        """Detiene el habla actual"""
        if self.engine:
            self.engine.stop()

# Instancia global
_tts_service = None

def get_tts_service():
    """Obtiene o crea la instancia del servicio TTS"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
