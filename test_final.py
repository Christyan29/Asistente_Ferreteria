"""
Prueba final de Gemini con el modelo correcto
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

print("=== Prueba Final de Gemini ===\n")

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL")

print(f"Modelo a usar: {model_name}\n")

genai.configure(api_key=api_key)

# Crear modelo
model = genai.GenerativeModel(model_name)

# Probar conversación
print("Probando conversación...\n")
chat = model.start_chat(history=[])

# Mensaje 1
response = chat.send_message("Hola, soy un cliente de una ferretería")
print(f"Usuario: Hola, soy un cliente de una ferretería")
print(f"Gabo: {response.text}\n")

# Mensaje 2
response = chat.send_message("¿Tienen martillos?")
print(f"Usuario: ¿Tienen martillos?")
print(f"Gabo: {response.text}\n")

print("✅ ¡Gemini funciona perfectamente!")
