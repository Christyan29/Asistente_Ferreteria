"""
Script para probar el micrófono y diagnosticar problemas.
Ejecuta este script para verificar si tu micrófono funciona correctamente.
"""
import speech_recognition as sr
import sys

def test_microphone():
    """Prueba el micrófono y muestra información de diagnóstico"""

    print("=" * 80)
    print("🎤 PRUEBA DE MICRÓFONO - Asistente Ferretería Disensa")
    print("=" * 80)

    recognizer = sr.Recognizer()

    # Paso 1: Listar micrófonos disponibles
    print("\n📋 Paso 1: Listando micrófonos disponibles...")
    try:
        mic_list = sr.Microphone.list_microphone_names()
        print(f"✅ Se encontraron {len(mic_list)} dispositivos de audio:")
        for i, name in enumerate(mic_list):
            print(f"   [{i}] {name}")
    except Exception as e:
        print(f"❌ Error al listar micrófonos: {e}")
        return False

    # Paso 2: Inicializar micrófono por defecto
    print("\n🎙️ Paso 2: Inicializando micrófono por defecto...")
    try:
        microphone = sr.Microphone()
        print("✅ Micrófono inicializado correctamente")
    except OSError as e:
        print(f"❌ Error de sistema: {e}")
        print("\n💡 Soluciones:")
        print("   1. Conecta un micrófono (USB o jack 3.5mm)")
        print("   2. Verifica que Windows detecte el micrófono (Panel de Control → Sonido)")
        print("   3. Asegúrate de que los drivers estén instalados")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

    # Paso 3: Ajustar ruido ambiental
    print("\n🔊 Paso 3: Ajustando ruido ambiental...")
    try:
        with microphone as source:
            print("   Calibrando... (mantén silencio)")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"✅ Nivel de energía: {recognizer.energy_threshold}")
    except Exception as e:
        print(f"❌ Error al calibrar: {e}")
        return False

    # Paso 4: Prueba de escucha
    print("\n🎤 Paso 4: Prueba de escucha...")
    print("   📢 HABLA AHORA (tienes 5 segundos)...")

    try:
        with microphone as source:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("✅ Audio capturado correctamente")
    except sr.WaitTimeoutError:
        print("⚠️ Timeout: No se detectó voz en 5 segundos")
        print("   Verifica que el micrófono esté funcionando")
        return False
    except Exception as e:
        print(f"❌ Error al capturar audio: {e}")
        return False

    # Paso 5: Reconocimiento de voz
    print("\n🧠 Paso 5: Reconociendo voz (requiere internet)...")
    try:
        text = recognizer.recognize_google(audio, language="es-ES")
        print(f"✅ TEXTO RECONOCIDO: '{text}'")
        print("\n🎉 ¡ÉXITO! Tu micrófono funciona perfectamente.")
        return True
    except sr.UnknownValueError:
        print("⚠️ No se entendió el audio")
        print("   Intenta hablar más claro y cerca del micrófono")
        return False
    except sr.RequestError as e:
        print(f"❌ Error de conexión: {e}")
        print("   Verifica tu conexión a internet")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    print("\n")
    success = test_microphone()

    print("\n" + "=" * 80)
    if success:
        print("✅ DIAGNÓSTICO: Tu micrófono está funcionando correctamente")
        print("   El botón de micrófono en la aplicación debería funcionar.")
    else:
        print("❌ DIAGNÓSTICO: Hay problemas con el micrófono")
        print("\n💡 SOLUCIONES RECOMENDADAS:")
        print("   1. Conecta un micrófono externo (USB o jack 3.5mm)")
        print("   2. Ve a: Configuración de Windows → Privacidad → Micrófono")
        print("   3. Activa 'Permitir que las aplicaciones accedan al micrófono'")
        print("   4. Verifica que Python tenga permisos de micrófono")
        print("   5. Prueba el micrófono en otra aplicación (ej: WhatsApp Web)")
    print("=" * 80)

    input("\nPresiona ENTER para salir...")

if __name__ == "__main__":
    main()
