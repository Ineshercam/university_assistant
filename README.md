# Pipeline de Asistente con LangGraph

Este repositorio implementa un asistente agéntico básico basado en LLMs construido con **LangGraph**, organizado como un pipeline donde cada componente cumple una función: interacción con el modelo, razonamiento basado en grafos, ingestión de datos, recuperación de información, ejecución de herramientas y exposición mediante API y frontend.

---

## Estructura del Proyecto

```
.
├── agent/
│   └── llm.py                    # Wrapper del modelo LLM (inicialización)
│
├── graph/
│   ├── nodes.py                  # Nodos del grafo: nodo agente principal y prompt genérico
│   ├── state.py                  # Definición del estado compartido para LangGraph
│   └── workflow.py               # Construcción y ejecución del grafo
│
├── ingestion/
│   ├── scrap.py                  # Descarga dípticos de titulaciones de la web de la UCM
│   ├── extract_pdf_data.py       # Extracción de información de los PDFs
│   ├── generate_questions.py     # Generación de preguntas a partir de transcripciones de audio
│   └── ingest_data.py            # Ingestión de datos a ChromaDB (acepta audio o JSON)
│
├── tools/
│   ├── get_subject.py            # Herramienta para extraer asignaturas de un grado
│   ├── retrieval_tool.py         # Herramienta de recuperación (vector search)
│   └── tool_definition.py        # Definición y registro de herramientas
│
├── api.py                        # API backend para exponer el asistente
├── frontend.py                   # Frontend basado en Gradio
├── requirements.txt              # Dependencias del proyecto
└── README.md
```

---

## Descripción General

El asistente está construido como un **grafo de LangGraph**, donde cada nodo representa un paso del razonamiento, una llamada al modelo o la ejecución de una herramienta.

---

## Instalación

### 1. Crear y activar un entorno Conda

```bash
conda create -n assistant python=3.11
conda activate assistant
pip install -r requirements.txt
```

### 2. Ejecutar la API y el frontend

```bash
uvicorn api:app --reload --port 8000
python frontend.py
```

### 3. Variables de entorno

Es necesario disponer de un archivo `.env` con las siguientes variables:

```
OPENAI_API_KEY=...
CHROMA_PATH =...
COLLECTION=...
```

> **Nota:** Se usan tanto modelos locales (Qwen) como APIs externas. Es necesario disponer de al menos **10 GB** de espacio libre para poder ejecutar el asistente.
