"""
Formateador de instrucciones - Genera formato PERFECTO independientemente del modelo.
"""
import re
from typing import List, Dict

class InstructionFormatter:
    """Genera respuestas con formato perfecto para preguntas de instrucciones"""

    # Base de conocimientos de herramientas por tarea
    TOOLS_DATABASE = {
        'taza de baño': {
            'tools': 'taza de baño, anclajes, tornillos, sellador sanitario, llave inglesa, nivel, cinta métrica, lápiz, trapos, cubeta',
            'steps': [
                'Desconecta el suministro de agua y cierra la llave de paso',
                'Retira la taza de baño antigua y limpia la superficie',
                'Coloca la taza nueva en posición y marca ubicación de anclajes',
                'Taladra agujeros e inserta los anclajes',
                'Fija la taza con tornillos, asegurándote de que esté nivelada',
                'Conecta las tuberías de agua y desagüe',
                'Aplica sellador alrededor de la base',
                'Espera el tiempo de secado recomendado'
            ],
            'precaution': 'Asegúrate de que todas las conexiones estén bien selladas para evitar fugas. Usa guantes y protección ocular.'
        },
        'cerámica': {
            'tools': 'baldosas, adhesivo para cerámica, espátula dentada, nivel, cortador de cerámica, lechada, esponja, trapo, rodillo de goma',
            'steps': [
                'Prepara la superficie limpia y nivelada',
                'Mezcla el adhesivo según instrucciones',
                'Aplica adhesivo con espátula dentada formando estrías',
                'Coloca las baldosas presionando firmemente',
                'Usa separadores para mantener uniformidad',
                'Deja secar 24 horas',
                'Aplica la lechada entre las juntas',
                'Limpia el exceso de lechada con esponja húmeda'
            ],
            'precaution': 'Usa el adhesivo y lechada adecuados para el tipo de cerámica y superficie.'
        },
        'repisa': {
            'tools': 'repisa, tornillos, anclajes, taladro, broca, nivel, cinta métrica, lápiz, destornillador',
            'steps': [
                'Mide y marca la posición en la pared con lápiz',
                'Usa nivel para asegurar que las marcas estén rectas',
                'Taladra agujeros en las marcas',
                'Inserta anclajes en los agujeros',
                'Coloca la repisa y fíjala con tornillos',
                'Verifica que esté segura y nivelada'
            ],
            'precaution': 'Verifica que la pared soporte el peso y usa anclajes adecuados.'
        },
        'pintar': {
            'tools': 'pintura, rodillo, bandeja, brocha, cinta de carrocero, lija, trapos, cubiertas para piso, guantes',
            'steps': [
                'Protege el área con cubiertas y aplica cinta de carrocero',
                'Limpia y lija la superficie',
                'Aplica imprimante si es necesario',
                'Mezcla la pintura uniformemente',
                'Aplica primera mano y deja secar',
                'Aplica segunda mano para cobertura completa',
                'Retira cinta de carrocero antes de que seque completamente'
            ],
            'precaution': 'Trabaja en área ventilada, usa mascarilla y protege ojos y piel.'
        },
        'grifo': {
            'tools': 'grifo nuevo, llave inglesa, llave de tubo, teflón, destornillador, trapos, cubeta',
            'steps': [
                'Cierra llave de paso de agua',
                'Desconecta el grifo antiguo',
                'Limpia las roscas de la tubería',
                'Envuélvelas con teflón en sentido horario',
                'Instala el grifo nuevo y aprieta con llave',
                'Conecta las mangueras de agua',
                'Abre llave de paso y verifica que no haya fugas'
            ],
            'precaution': 'Asegúrate de que todas las conexiones estén bien ajustadas para evitar fugas.'
        },
        'enchufe': {
            'tools': 'tomacorriente nuevo, destornillador eléctrico, cinta aislante, probador de corriente, guantes de seguridad',
            'steps': [
                'DESCONECTA LA CORRIENTE en el tablero principal',
                'Retira la tapa del tomacorriente antiguo',
                'Desconecta los cables (nota colores y posición)',
                'Conecta los cables al nuevo tomacorriente en la misma posición',
                'Fija el tomacorriente en la caja',
                'Coloca la tapa',
                'Reactiva la corriente y prueba con probador'
            ],
            'precaution': 'SIEMPRE desconecta la corriente antes de trabajar. Si no estás seguro, consulta a un electricista.'
        }
    }

    # Palabras clave para detectar tareas
    KEYWORDS = {
        'taza de baño': ['taza', 'inodoro', 'sanitario', 'wc', 'retrete'],
        'cerámica': ['cerámica', 'baldosa', 'azulejo', 'piso cerámico'],
        'repisa': ['repisa', 'estante', 'anaquel', 'mueble de pared'],
        'pintar': ['pintar', 'pintura', 'pintar pared', 'pintar casa'],
        'grifo': ['grifo', 'llave de agua', 'canilla', 'mezcladora'],
        'enchufe': ['enchufe', 'tomacorriente', 'contacto', 'corriente', 'eléctrico']
    }

    @classmethod
    def detect_task(cls, user_message: str) -> str:
        """Detecta la tarea específica en el mensaje del usuario"""
        user_lower = user_message.lower()

        for task, keywords in cls.KEYWORDS.items():
            for keyword in keywords:
                if keyword in user_lower:
                    return task

        # Si no encuentra tarea específica, pero es pregunta de instrucciones
        instruction_keywords = ['instalar', 'instrucciones', 'como hacer', 'pasos para', 'reparar', 'montar']
        if any(k in user_lower for k in instruction_keywords):
            return 'general'

        return None

    @classmethod
    def format_response(cls, user_message: str, groq_response: str = None) -> str:
        """Genera respuesta con formato perfecto"""
        task = cls.detect_task(user_message)

        if not task:
            return groq_response or "¿En qué puedo ayudarte hoy?"

        if task == 'general':
            # Formato genérico para instrucciones
            return cls._format_general_instruction(user_message, groq_response)

        # Usar base de conocimientos para tarea específica
        if task in cls.TOOLS_DATABASE:
            return cls._format_specific_instruction(task)

        # Fallback
        return cls._format_general_instruction(user_message, groq_response)

    @classmethod
    def _format_specific_instruction(cls, task: str) -> str:
        """Formatea instrucción específica desde base de conocimientos"""
        data = cls.TOOLS_DATABASE[task]

        formatted = f"Herramientas/materiales necesarios: {data['tools']}\n\n"

        for i, step in enumerate(data['steps'], 1):
            formatted += f"{i}. {step}\n"

        formatted += f"\nPrecaución: {data['precaution']}"

        return formatted

    @classmethod
    def _format_general_instruction(cls, user_message: str, groq_response: str = None) -> str:
        """Formatea instrucción general"""
        # Extraer herramientas mencionadas si hay respuesta de Groq
        tools = "herramientas básicas, materiales específicos según la tarea"
        if groq_response:
            # Intentar extraer herramientas de la respuesta
            tools_match = re.search(r'(?:Herramientas|Materiales|necesitas)[:\-]?\s*(.*?)(?=\d+\.|$|Precaución)',
                                   groq_response, re.IGNORECASE | re.DOTALL)
            if tools_match:
                tools = tools_match.group(1).strip()

        # Pasos genéricos pero bien estructurados
        steps = [
            "Prepara todas las herramientas y materiales necesarios",
            "Lee cuidadosamente las instrucciones del fabricante",
            "Prepara el área de trabajo y toma medidas de seguridad",
            "Sigue el procedimiento paso a paso con paciencia",
            "Verifica que la instalación sea segura y funcional",
            "Limpia el área de trabajo y desecha los materiales sobrantes apropiadamente"
        ]

        formatted = f"Herramientas/materiales necesarios: {tools}\n\n"

        for i, step in enumerate(steps, 1):
            formatted += f"{i}. {step}\n"

        formatted += "\nPrecaución: Sigue siempre las instrucciones del fabricante, usa equipo de protección adecuado y toma todas las precauciones de seguridad."

        return formatted

    @classmethod
    def force_correction(cls, response_text: str) -> str:
        """Fuerza corrección de formato en cualquier texto"""
        # 1. Corregir "Herramientasmateriales" SIEMPRE
        if 'Herramientasmateriales' in response_text:
            response_text = response_text.replace('Herramientasmateriales', 'Herramientas/materiales')

        # 2. Asegurar formato de herramientas
        if 'Herramientas/materiales necesarios:' not in response_text:
            # Buscar cualquier mención de herramientas
            patterns = [
                r'(?:Materiales|Herramientas|Necesitas).*?:?(.*?)(?=\d+\.|Paso|$|Precaución)',
                r'para (?:esta tarea|instalar).*?necesitas (.*?)(?=\.|$)'
            ]

            for pattern in patterns:
                match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
                if match:
                    tools = match.group(1).strip()
                    response_text = f"Herramientas/materiales necesarios: {tools}\n\n" + response_text
                    break

        # 3. Formatear pasos numerados
        # Buscar números de pasos y poner cada uno en línea separada
        lines = response_text.split('\n')
        formatted_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Si la línea tiene múltiples pasos (ej: "1. paso 2. paso")
            if re.search(r'\d+\.\s*[^.]+\s+\d+\.', line):
                # Separar pasos
                parts = re.split(r'(\d+\.\s*)', line)[1:]  # Split pero mantener números
                for i in range(0, len(parts), 2):
                    if i+1 < len(parts):
                        formatted_lines.append(f"{parts[i]}{parts[i+1].strip()}")
            else:
                formatted_lines.append(line)

        response_text = '\n'.join(formatted_lines)

        # 4. Asegurar precaución
        if 'Precaución:' not in response_text:
            response_text += "\n\nPrecaución: Sigue las instrucciones del fabricante y toma precauciones de seguridad."

        return response_text