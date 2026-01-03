# Asistente Virtual Ferretería Disensa

Sistema integral de gestión de inventario con asistente virtual basado en IA para la Ferretería Disensa de Pomasqui, Ecuador.

## 🎯 Características

- **Asistente Virtual (Gabo):** IA conversacional con Groq AI (LLaMA 3.3 70B)
- **Gestión de Inventario:** CRUD completo de productos y categorías
- **Interacción por Voz:** Speech-to-Text y Text-to-Speech
- **Importación Masiva:** Carga de productos desde archivos Excel
- **Alertas Inteligentes:** Notificaciones de stock bajo
- **Interfaz Moderna:** Diseño profesional con PyQt5

## 📋 Requisitos Previos

- Python 3.12 o superior
- Windows 10/11 (para funcionalidades de voz)
- Conexión a internet (para IA y reconocimiento de voz)

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Christyan29/Asistente_Ferreteria.git
cd Asistente_Ferreteria
```

### 2. Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# API de Groq (obtener en https://console.groq.com)
GROQ_API_KEY=tu_api_key_aqui
GROQ_MODEL=llama-3.3-70b-versatile
```

### 5. Ejecutar la aplicación

```bash
python app/main.py
```

## 📖 Uso

### Acceso al Inventario

Para acceder a la gestión de inventario:
- Usuario: `admin`
- Contraseña: `admin123`

### Chat con Gabo

1. Abre la pestaña "Chat"
2. Escribe tu pregunta o usa el botón de micrófono
3. Gabo responderá por texto y voz

### Importar Productos desde Excel

1. Ve a la pestaña "Inventario"
2. Haz clic en "Importar Excel"
3. Selecciona un archivo .xlsx con las columnas:
   - Nombre (obligatorio)
   - Categoría (obligatorio)
   - Precio (obligatorio)
   - Stock (obligatorio)
   - Unidad (obligatorio)
   - Código, Stock Mínimo, Marca, Ubicación (opcionales)

## 🏗️ Arquitectura

El proyecto sigue una arquitectura en capas:

```
app/
├── presentation/     # Interfaz gráfica (PyQt5)
├── application/      # Lógica de aplicación
├── services/         # Servicios externos (IA, voz, Excel)
├── domain/           # Entidades de negocio
├── infrastructure/   # Acceso a datos (Repository Pattern)
└── config/           # Configuración
```

## 🛠️ Tecnologías

- **Python 3.12**
- **PyQt5** - Interfaz gráfica
- **Groq AI** - Inteligencia artificial (LLaMA 3.3 70B)
- **SQLite + SQLAlchemy** - Base de datos
- **SpeechRecognition** - Reconocimiento de voz
- **pyttsx3** - Síntesis de voz
- **Pandas + OpenPyXL** - Procesamiento de Excel

## 📚 Documentación

- [Guía Técnica Completa](docs/guia_tecnica_presentacion.md)
- [Manual de Usuario](docs/manual_usuario.md)
- [Arquitectura del Sistema](docs/arquitectura.md)

## 🧪 Scripts de Utilidad

```bash
# Ver contenido de la base de datos
python ver_base_datos.py

# Generar archivo Excel de prueba
python generar_excel_completo.py

# Probar micrófono
python test_microfono.py

# Probar TTS y Avatar
python test_tts_avatar.py
```



## ⚠️ Problemas Conocidos

- El reconocimiento de voz requiere buena conexión a internet
- En algunos sistemas el micrófono no se detecta automáticamente
- La primera carga puede tardar unos segundos
- Algunas respuestas de la IA pueden ser muy largas

## 🔧 En Desarrollo

- Sistema de reportes en PDF
- Gráficas de inventario
- Mejoras en la interfaz
- Más opciones de configuración

## 🤝 Contribuir

Este es un proyecto de tesis. Para sugerencias o mejoras, contactar al autor.

## 📄 Licencia

Este proyecto es de uso académico para la tesis de grado.

## 👤 Autor

**Christyan**
- GitHub: [@Christyan29](https://github.com/Christyan29)
- Proyecto: Asistente Virtual Ferretería Disensa
- Institución: [Tu Universidad]

## 🙏 Agradecimientos

- Ferretería Disensa de Pomasqui
- Groq AI por proporcionar acceso a LLaMA 3.3
- Comunidad de Python y PyQt5
