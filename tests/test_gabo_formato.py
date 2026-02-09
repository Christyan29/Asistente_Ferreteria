"""
Prueba del formato de instrucciones del asistente Gabo.
Este archivo debe guardarse en la carpeta tests.
"""
import sys
import os

# Agregar el directorio raíz al path para poder importar los módulos de la aplicación
sys.path.append('..')

print("=" * 70)
print("🧪 PRUEBA DEL FORMATO DE INSTRUCCIONES - ASISTENTE GABO")
print("=" * 70)

# Intentar importar el servicio de Groq
try:
    from app.services.groq_service import get_groq_service
    print("✅ Módulo groq_service importado correctamente")
except ImportError as e:
    print(f"❌ Error al importar groq_service: {e}")
    print("\n📁 Verificando estructura de archivos...")
    print(f"Directorio actual: {os.getcwd()}")
    print(f"¿Existe ../app/services/groq_service.py? {os.path.exists('../app/services/groq_service.py')}")
    sys.exit(1)

# Obtener el servicio
try:
    service = get_groq_service()

    if not service.is_available():
        print("❌ El servicio de Groq no está disponible")
        print("   Verifica que tengas una API key configurada en el archivo .env")
        sys.exit(1)

    print("✅ Servicio Groq disponible")

    # Lista de preguntas para probar
    preguntas = [
        "necesito instrucciones para instalar una taza de baño",
        "como instalar una lámpara solar",
        "pasos para colocar cerámica en el piso",
        "instrucciones para pintar una pared",
        "como reparar un grifo que gotea"
    ]

    print(f"\n🔍 Probando {len(preguntas)} preguntas de instrucciones...")
    print("=" * 70)

    resultados = []

    for i, pregunta in enumerate(preguntas, 1):
        print(f"\n{'='*60}")
        print(f"❓ Prueba {i}: '{pregunta}'")
        print(f"{'='*60}")

        try:
            # Obtener respuesta
            respuesta = service.chat_with_context(pregunta)

            print(f"📄 Respuesta obtenida ({len(respuesta)} caracteres):")
            print("-" * 40)

            # Mostrar los primeros 300 caracteres
            if len(respuesta) > 300:
                print(respuesta[:300] + "...")
            else:
                print(respuesta)

            print("-" * 40)

            # Verificar el formato
            formato_correcto = True
            errores = []

            # 1. Verificar que tenga "Herramientas/materiales necesarios:"
            if "Herramientas/materiales necesarios:" not in respuesta:
                formato_correcto = False
                errores.append("❌ FALTA: 'Herramientas/materiales necesarios:'")
            else:
                print("✅ TIENE: 'Herramientas/materiales necesarios:'")

            # 2. Verificar que NO tenga "Herramientasmateriales" (pegado)
            if "Herramientasmateriales" in respuesta:
                formato_correcto = False
                errores.append("❌ ERROR: Tiene 'Herramientasmateriales' (debe estar separado con /)")
            else:
                print("✅ CORRECTO: No tiene 'Herramientasmateriales'")

            # 3. Verificar pasos numerados
            tiene_pasos_numerados = any(str(num) + "." in respuesta for num in range(1, 10))
            if not tiene_pasos_numerados:
                formato_correcto = False
                errores.append("❌ FALTA: Pasos numerados (1., 2., 3., etc.)")
            else:
                print("✅ TIENE: Pasos numerados")

            # 4. Verificar que tenga "Precaución:"
            if "Precaución:" not in respuesta:
                formato_correcto = False
                errores.append("❌ FALTA: 'Precaución:'")
            else:
                print("✅ TIENE: 'Precaución:'")

            # Mostrar errores si los hay
            if errores:
                print("\n⚠️ PROBLEMAS DETECTADOS:")
                for error in errores:
                    print(f"  {error}")
            else:
                print("\n🎉 ¡FORMATO CORRECTO!")

            resultados.append({
                "pregunta": pregunta,
                "correcto": formato_correcto,
                "errores": errores
            })

        except Exception as e:
            print(f"❌ ERROR durante la prueba: {e}")
            resultados.append({
                "pregunta": pregunta,
                "correcto": False,
                "errores": [f"Excepción: {str(e)}"]
            })

    # Mostrar resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN FINAL")
    print("=" * 70)

    pruebas_correctas = sum(1 for r in resultados if r["correcto"])
    total_pruebas = len(resultados)

    print(f"✅ Pruebas con formato correcto: {pruebas_correctas}/{total_pruebas}")

    if pruebas_correctas < total_pruebas:
        print("\n🔧 Pruebas que necesitan corrección:")
        for r in resultados:
            if not r["correcto"]:
                print(f"\n  ❌ Pregunta: '{r['pregunta']}'")
                for error in r["errores"]:
                    print(f"     {error}")

    if pruebas_correctas == total_pruebas:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON! El formato es correcto.")
    else:
        print(f"\n⚠️ {total_pruebas - pruebas_correctas} pruebas fallaron.")

    print("\n" + "=" * 70)

except Exception as e:
    print(f"❌ Error general: {e}")
    import traceback
    traceback.print_exc()