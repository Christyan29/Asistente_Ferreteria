# Script para agregar métodos faltantes a asistente_view.py
import sys

# Leer el archivo actual
with open('app/presentation/asistente_view.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Métodos que necesitamos agregar
metodos_faltantes = '''
    def procesar_mensaje(self, mensaje):
        """
        Procesa el mensaje del usuario y genera una respuesta.
        Usa Groq AI si está disponible, sino usa modo básico.
        """
        try:
            # Intentar usar Groq AI primero
            if self.groq_service.is_available():
                return self.procesar_con_groq(mensaje)
            else:
                # Fallback a modo básico
                return self.procesar_modo_basico(mensaje)
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {e}")
            # Si falla Groq, intentar modo básico
            try:
                return self.procesar_modo_basico(mensaje)
            except:
                return "Lo siento, ocurrió un error al procesar tu consulta. Por favor, intenta de nuevo."

    def procesar_con_groq(self, mensaje):
        """
        Procesa el mensaje usando Groq AI.
        """
        try:
            # Obtener contexto del inventario
            productos = self.producto_repo.get_all()
            productos_nombres = [p.nombre for p in productos[:20]]  # Primeros 20
            contexto = f"Productos disponibles: {', '.join(productos_nombres)}"

            # Obtener respuesta de Groq
            respuesta = self.groq_service.chat_with_context(mensaje, contexto)
            return respuesta

        except Exception as e:
            logger.error(f"Error con Groq: {e}")
            raise

    def procesar_modo_basico(self, mensaje):
        """
        Procesa el mensaje del usuario en modo básico (sin IA).
        Esta es una versión simple que busca en la base de datos.
        """
        mensaje_lower = mensaje.lower()

        try:
            # Comandos específicos con más variaciones
            if any(palabra in mensaje_lower for palabra in ["stock bajo", "stock mínimo", "poco stock", "productos bajos"]):
                return self.responder_stock_bajo()

            elif any(palabra in mensaje_lower for palabra in ["categoría", "categorias", "tipos de productos", "secciones"]):
                return self.responder_categorias()

            elif any(palabra in mensaje_lower for palabra in ["cuántos productos", "total", "cantidad", "qué productos tienes", "que productos", "productos disponibles"]):
                return self.responder_total_productos()

            elif any(palabra in mensaje_lower for palabra in ["buscar", "busca", "necesito", "quiero", "tienes", "tienen", "hay"]):
                # Extraer término de búsqueda - remover palabras comunes
                palabras_ignorar = ["buscar", "busca", "necesito", "quiero", "tienes", "tienen", "hay", "un", "una", "el", "la", "los", "las", "de", "para"]
                palabras = mensaje_lower.split()
                terminos = [p for p in palabras if p not in palabras_ignorar and len(p) > 2]

                if terminos:
                    termino = " ".join(terminos)
                    return self.responder_busqueda(termino)
                else:
                    # Si no hay términos específicos, mostrar productos
                    return self.responder_total_productos()

            # Búsqueda general por palabras clave
            else:
                return self.responder_busqueda(mensaje)

        except Exception as e:
            logger.error(f"Error al procesar mensaje en modo básico: {e}")
            return "Lo siento, ocurrió un error al procesar tu consulta. Por favor, intenta de nuevo."

    def responder_stock_bajo(self):
        """Responde con productos de stock bajo"""
        productos = self.producto_repo.get_stock_bajo()

        if not productos:
            return "✅ ¡Excelente! No hay productos con stock bajo en este momento."

        respuesta = f"⚠️ Encontré {len(productos)} producto(s) con stock bajo:<br><br>"
        for p in productos[:5]:  # Máximo 5
            respuesta += f"• <b>{p.nombre}</b>: {p.stock} {p.unidad_medida} (mínimo: {p.stock_minimo})<br>"

        if len(productos) > 5:
            respuesta += f"<br>... y {len(productos) - 5} más."

        return respuesta
'''

# Verificar si los métodos ya existen
if 'def procesar_mensaje' not in content:
    # Encontrar la última línea antes del final
    lines = content.split('\n')

    # Insertar antes de la última línea (que probablemente esté vacía)
    lines.insert(-1, metodos_faltantes)

    # Guardar el archivo
    with open('app/presentation/asistente_view.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print("✅ Métodos agregados exitosamente")
else:
    print("⚠️ Los métodos ya existen en el archivo")
