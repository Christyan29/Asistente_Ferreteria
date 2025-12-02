"""
Prueba rápida de Groq
"""
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

print("=== Prueba de Groq ===\n")

api_key = os.getenv("GROQ_API_KEY")
print(f"API Key: {api_key[:20]}...\n")

client = Groq(api_key=api_key)

messages = [
    {"role": "system", "content": "Eres Gabo, un asistente amigable de ferretería. Responde en español de forma concisa."},
print("✅ ¡Groq funciona perfectamente!")
