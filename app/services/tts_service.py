"""
Servicio de Texto a Voz (TTS) - VERSIÓN CORREGIDA Y ROBUSTA
"""
import pyttsx3
import logging
import threading
import pythoncom
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class TTSService(QObject):
    """Servicio TTS con capacidad real de interrupción"""

    speaking_started = pyqtSignal()
    speaking_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_speaking = False
        self.current_engine = None  # Referencia al engine actual para poder detenerlo
        self._lock = threading.Lock()
        logger.info("TTSService inicializado")

    def speak(self, text):
        """
        Habla el texto en un hilo separado.
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
        # Necesario para pyttsx3 en hilos
        pythoncom.CoInitialize()

        try:
            with self._lock:
                self.is_speaking = True
                self.speaking_started.emit()

                # Inicializar engine
                engine = pyttsx3.init()
                self.current_engine = engine # Guardar referencia para stop()

                # Configurar voz en español
                try:
                    voices = engine.getProperty('voices')
                    for voice in voices:
                        voice_name = voice.name.lower()
                        if any(kw in voice_name for kw in ['spanish', 'es-', 'sabina', 'helena', 'mexico']):
                            engine.setProperty('voice', voice.id)
                            break
                except Exception:
                    pass

                # Configurar velocidad y volumen
                engine.setProperty('rate', 160)
                engine.setProperty('volume', 1.0)

                # Conectar evento de fin si es necesario, pero runAndWait maneja el bloqueo

                logger.info("🗣️ Hablando...")
                engine.say(text)
                engine.runAndWait() # Bloquea hasta terminar o stop()

        except Exception as e:
            logger.error(f"❌ Error en TTS: {e}")
        finally:
            self.current_engine = None
            self.is_speaking = False
            pythoncom.CoUninitialize()
            self.speaking_finished.emit()
            logger.info("✅ TTS Finalizado")

    def stop(self):
        """Detiene el habla INMEDIATAMENTE"""
        if self.current_engine:
            logger.info("🛑 Forzando detención de TTS...")
            try:
                # stop() debe llamarse en el engine activo
                self.current_engine.stop()
            except Exception as e:
                logger.error(f"Error al detener engine: {e}")
        self.is_speaking = False
