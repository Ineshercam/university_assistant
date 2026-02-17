from typing import Annotated, List
from pydantic import BaseModel
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages



class AgentState(BaseModel):
    """
    El estado del agente contiene la lista de mensajes intercambiados
    durante la ejecución del grafo. Cada mensaje es un BaseMessage
    (puede ser SystemMessage, HumanMessage, AIMessage, ToolMessage, etc.).
    
    Se usa `Annotated` junto con `add_messages` para indicarle a LangGraph
    cómo debe combinar este campo cuando varios nodos producen mensajes.
    En concreto, `add_messages` define que los mensajes nuevos se agregan
    a la lista existente en lugar de sobrescribirla.
    """
    messages: Annotated[List[BaseMessage], add_messages]

