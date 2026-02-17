from langchain_openai import ChatOpenAI
from graph.state import AgentState
from tools.tool_definition import tools
from agent.llm import llm

from langchain_core.messages import SystemMessage

#prompt general que se le pasará al LLM con las instrucciones básicas y sobre las herramientas que debe usar
SYSTEM_PROMPT = """
Eres un asistente experto en grados universitarios de la UCM.

REGLAS ESTRICTAS:
- Si el usuario pregunta por asignaturas, materias o plan de estudios → USA SIEMPRE retrieve_subjects.
- Si el usuario pregunta por salidas profesionales, competencias, o preguntas generales sobre una carrera→ USA SIEMPRE retrieve_docs.
- Si ya has recibido el resultado de una herramienta, NO vuelvas a llamarla.
- Analiza el contexto para saber si ya tienes la información.
- NUNCA respondas usando conocimiento propio sobre grados universitarios.
- NUNCA digas que no tienes acceso a información sin haber llamado primero a una herramienta.
"""

def agent_node(state: AgentState):
    """
    Nodo principal del agente.  
    Recibe el estado actual (mensajes, memoria, etc.).  
    Envía los mensajes al LLM.  
    Devuelve la respuesta del modelo para que el grafo continúe.
    """
    print("AGENT NODE")

    # Extraemos la lista de mensajes acumulados en el estado del agente.
    messages = state.messages

    # Log útil para depuración: muestra los mensajes recibidos y su tipo.
    print("Messages:")
    for i, m in enumerate(messages):
        # Mostramos solo los primeros 300 caracteres ya que puede ser muy extenso y confundir más que ayudar.
        print(f"{i}: {type(m).__name__}: {getattr(m, 'content', '')[:300]}")

    # Aseguramos que el mensaje de sistema se inyecta solo una vez.
    # Esto evita duplicar instrucciones del sistema en cada paso del grafo.
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    # Llamada al LLM con el historial de mensajes.
    # Aquí el agente decide si responde directamente o invoca herramientas.
    response = llm.invoke(messages)

    # Log de depuración para ver si el modelo ha solicitado herramientas.
    print("DEBUG tool_calls:", response.tool_calls)

    # Devolvemos la respuesta como nuevo mensaje
    return {"messages": [response]}


