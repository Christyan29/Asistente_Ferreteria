"""
Script de prueba para verificar TTS y Avatar
"""
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Importar servicios
from app.services.tts_service import TTSService
from app.presentation.components.avatar_widget import AvatarWidget

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test TTS y Avatar")
        self.setGeometry(100, 100, 400, 500)

        layout = QVBoxLayout(self)

        # Avatar
        self.avatar = AvatarWidget()
        layout.addWidget(self.avatar, alignment=Qt.AlignCenter)

        # Label de estado
        self.status_label = QLabel("Listo")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Servicio TTS
        self.tts = TTSService()

        # Conectar señales
        self.tts.speaking_started.connect(self.on_speaking_started)
        self.tts.speaking_finished.connect(self.on_speaking_finished)

        # Botones de prueba
        btn1 = QPushButton("Prueba 1: Hablar")
        btn1.clicked.connect(self.test_hablar_1)
        layout.addWidget(btn1)

        btn2 = QPushButton("Prueba 2: Hablar de nuevo")
        btn2.clicked.connect(self.test_hablar_2)
        layout.addWidget(btn2)

        btn3 = QPushButton("Prueba 3: Hablar tercera vez")
        btn3.clicked.connect(self.test_hablar_3)
        layout.addWidget(btn3)

        btn_avatar = QPushButton("Test Avatar: Listening")
        btn_avatar.clicked.connect(lambda: self.avatar.start_listening())
        layout.addWidget(btn_avatar)

        btn_avatar2 = QPushButton("Test Avatar: Speaking")
        btn_avatar2.clicked.connect(lambda: self.avatar.start_speaking())
        layout.addWidget(btn_avatar2)

        btn_avatar3 = QPushButton("Test Avatar: Stop")
        btn_avatar3.clicked.connect(lambda: self.avatar.stop())
        layout.addWidget(btn_avatar3)

        print("✅ TestWindow inicializado")
        print("✅ Señales conectadas")

    def on_speaking_started(self):
        print("🔊 SEÑAL RECIBIDA: speaking_started")
        self.status_label.setText("🔊 HABLANDO...")
        self.avatar.start_speaking()

    def on_speaking_finished(self):
        print("🔇 SEÑAL RECIBIDA: speaking_finished")
        self.status_label.setText("✅ Terminado")
        self.avatar.stop()

    def test_hablar_1(self):
        print("\n" + "="*50)
        print("TEST 1: Primera llamada a TTS")
        print("="*50)
        self.status_label.setText("Preparando...")
        self.tts.speak("Esta es la primera prueba de texto a voz")

    def test_hablar_2(self):
        print("\n" + "="*50)
        print("TEST 2: Segunda llamada a TTS")
        print("="*50)
        self.status_label.setText("Preparando...")
        self.tts.speak("Esta es la segunda prueba. Si escuchas esto, el bug está corregido")

    def test_hablar_3(self):
        print("\n" + "="*50)
        print("TEST 3: Tercera llamada a TTS")
        print("="*50)
        self.status_label.setText("Preparando...")
        self.tts.speak("Tercera prueba. Todo funciona correctamente")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("INICIANDO PRUEBA DE TTS Y AVATAR")
    print("="*60)

    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()

    print("\n📋 INSTRUCCIONES:")
    print("1. Haz clic en 'Prueba 1: Hablar'")
    print("2. Espera a que termine de hablar")
    print("3. Haz clic en 'Prueba 2: Hablar de nuevo'")
    print("4. Si escuchas la segunda prueba, el bug está CORREGIDO ✅")
    print("5. Observa el avatar cambiar de color")
    print("\n")

    sys.exit(app.exec_())
