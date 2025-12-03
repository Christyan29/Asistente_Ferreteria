"""
Servicio de Texto a Voz (TTS) - VERSIÓN CORREGIDA Y SIMPLIFICADA
"""
import pyttsx3
import logging
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class TTSService(QObject):
    """Servicio TTS con threading corregido"""

    speaking_started = pyqtSignal()
    speaking_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_speaking = False
        self._lock = threading.Lock()
        logger.info("TTSService inicializado")

    def speak(self, text):
        """
        Habla el texto en un hilo separado.
        IMPORTANTE: Crea un nuevo engine en cada llamada para evitar problemas.
        """
        if not text or not text.strip():
            return

        # Limpiar HTML básico
        text = text.replace("<b>", "").replace("</b>", "")
        text = text.replace("<br>", ". ").replace("<br/>", ". ")
        text = text.strip()

        logger.info(f"🔊 Iniciando TTS: '{text[:50]}...'")

        # Ejecutar en hilo separado
        thread = threading.Thread(target=self._speak_thread, args=(text,), daemon=True)
        thread.start()

    def _speak_thread(self, text):
        """Ejecuta TTS en hilo separado"""
        with self._lock:
            try:
                self.is_speaking = True
                self.speaking_started.emit()
                logger.info("✅ Señal speaking_started emitida")

                # CRÍTICO: Crear engine nuevo en cada llamada
                engine = pyttsx3.init()

                # Configurar voz en español
                try:
                    voices = engine.getProperty('voices')
                    for voice in voices:
                        voice_name = voice.name.lower()
                        if any(kw in voice_name for kw in ['spanish', 'es-', 'sabina', 'helena', 'mexico']):
                            engine.setProperty('voice', voice.id)
                            logger.info(f"Voz seleccionada: {voice.name}")
                            break
                except Exception as e:
                    logger.warning(f"No se pudo configurar voz en español: {e}")

                # Configurar velocidad y volumen
                engine.setProperty('rate', 160)
                engine.setProperty('volume', 1.0)

                # Hablar
                logger.info("🗣️ Hablando...")
                engine.say(text)
                engine.runAndWait()

                # Limpiar
                try:
                    engine.stop()
                except:
                    pass

                logger.info("✅ TTS completado")

            except Exception as e:
                logger.error(f"❌ Error en TTS: {e}", exc_info=True)
            finally:
                self.is_speaking = False
                self.speaking_finished.emit()
                logger.info("✅ Señal speaking_finished emitida")

    def stop(self):
        """Detiene el habla (si es posible)"""
        self.is_speaking = False


# Instancia global
_tts_service = None

def get_tts_service():
    """Obtiene la instancia global del servicio TTS"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
