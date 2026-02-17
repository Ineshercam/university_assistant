# Pipeline de Asistente con LangGraph

Este repositorio implementa un asistente agentico MUY básico basado en LLMs construido con **LangGraph**, organizado como un pipeline donde cada componente cumple una función: interacción con el modelo, razonamiento basado en grafos, ingestión de datos, recuperación de información, ejecución de herramientas y exposición mediante API y frontend.

---

## Estructura del Proyecto

.
├── agent/
│   └── llm.py                 # Wrapper del modelo LLM (inicialización)
│
├── graph/
│   ├── nodes.py               # Nodos del grafo: nodo agente principal y prompt generico
│   ├── state.py               # Definición del estado compartido para LangGraph
│   └── workflow.py            # Construcción y ejecución del grafo
│
├── ingestion/
│   ├── scrap.py               # fichero básico para descargar dipticos de titulaciones de la página web de la UCM
│   ├── extract_pdf_data.py    # Extracción de información de los pdfs, ajustado a ese tipo de pdf
│   └── generate_questions.py # Si queremos generar preguntas dada una transcripción de audio, en este proyecto se uso para generar preguntas a partir de la transcripción de un video de youtube sobre preguntas y respuestas de la carrera de enfermería
    └── ingest_data.py        # ingestar data a la bbdd vectorial, en este caso chromadb en local. Acepta audios (se transcribe) o texto en formato json
│                 
│
├── tools/
│   ├── get_subject.py         # Herramienta para extraer el las asignaturas de un grado especifico.
│   ├── retrieval_tool.py      # Herramienta de recuperación (vector search)
│   └── tool_definition.py     # Definición y registro de herramientas
│
├── api.py                     # API backend para exponer el asistente
├── frontend.py                # Frontend sencillo basado en gradio para interactuar con el asistente
├── requirements.txt           # Dependencias del proyecto
└── README.md