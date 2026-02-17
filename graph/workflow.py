from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from graph.state import AgentState
from graph.nodes import agent_node
from tools.tool_definition import tools

def build_graph():
    """
    
    Se crea un grafo cuyo estado base es AgentState.
    Este grafo define cómo fluye la información entre nodos.
    """
    workflow = StateGraph(AgentState)

    # Nodo principal del agente: llama al LLM y decide qué hacer.
    workflow.add_node("agent", agent_node)

    # Nodo de herramientas: ejecuta las tool calls que el LLM solicite.
    # ToolNode es un nodo pre-generado que proporcionalanggraph que sabe cómo invocar herramientas.
    workflow.add_node("tools", ToolNode(tools))

    # El punto de entrada del grafo es el nodo "agent".
    workflow.set_entry_point("agent")

    # Condición que decide si el flujo va a herramientas o termina.
    # Si el último mensaje del agente contiene tool_calls → ir a "tools".
    # Si no hay tool_calls → finalizar el grafo (END).
    workflow.add_conditional_edges(
        "agent",
        lambda state: (
            "tools" if state.messages[-1].tool_calls else END
        ),
    )

    # Después de ejecutar herramientas, volvemos al agente para procesar la respuesta.
    workflow.add_edge("tools", "agent")

    # MemorySaver permite que el grafo mantenga checkpoints del estado.
    # Esto permite reanudar conversaciones o inspeccionar pasos previos.
    checkpointer = MemorySaver()

    # Compilamos el grafo con el checkpointer activado.
    return workflow.compile(checkpointer=checkpointer)
