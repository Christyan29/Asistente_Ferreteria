"""
Script para listar modelos disponibles de Gemini
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv()

print("=== Modelos Disponibles de Gemini ===\n")

# Configurar API
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Listar modelos
print("Listando modelos disponibles...\n")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   Descripción: {model.display_name}")
        print(f"   Métodos: {', '.join(model.supported_generation_methods)}")
        print()
