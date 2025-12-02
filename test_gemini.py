"""
Script de prueba para verificar la conexión con Gemini
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv()

print("=== Prueba de Conexión con Gemini ===\n")

# Verificar API key
api_key = os.getenv("GEMINI_API_KEY")
print(f"1. API Key encontrada: {'Sí' if api_key else 'No'}")
if api_key:
    print(f"   Primeros caracteres: {api_key[:20]}...")

# Intentar configurar Gemini
try:
    genai.configure(api_key=api_key)
    print("2. Gemini configurado: Sí")

    # Crear modelo
    model = genai.GenerativeModel('gemini-pro')
    print("3. Modelo creado: Sí")

    # Probar generación
    print("\n4. Probando generación de respuesta...")
    response = model.generate_content("Di 'Hola' en una palabra")
    print(f"   Respuesta: {response.text}")

    print("\n✅ ¡Gemini funciona correctamente!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"   Tipo: {type(e).__name__}")
