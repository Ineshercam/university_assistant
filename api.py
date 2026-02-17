from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from graph.workflow import build_graph
import uuid
import json

app = FastAPI(title="University agent")

# se construye el grafo del agente (LangGraph) una sola vez al arrancar la API.
graph = build_graph()

#Modelo pydantic de entrada y salida
class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    thread_id: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint de chat estándar (respuesta completa).
    
    - Si el cliente no envía thread_id, se crea uno nuevo.
    - Se envía el mensaje del usuario al grafo.
    - El grafo ejecuta el flujo (agent → tools → agent...).
    - Se devuelve la última respuesta generada por el agente.
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    # se ejecuta el grafo con el mensaje del usuario
    result = graph.invoke(
        {"messages": [HumanMessage(content=request.message)]},
        config={"configurable": {"thread_id": thread_id}},
    )

    reply = result["messages"][-1].content
    return ChatResponse(reply=reply, thread_id=thread_id)


from langchain_core.messages import AIMessageChunk

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Endpoint de chat con streaming (Server-Sent Events).
    
    Envía tokens a medida que el LLM los genera.
    Permite interfaces tipo "chat en tiempo real" (para una mejor UX).
    También envía el thread_id al inicio del stream.
    """
    
    thread_id = request.thread_id or str(uuid.uuid4())

    def token_generator():
        yield f"data: {json.dumps({'type': 'thread_id', 'value': thread_id})}\n\n"

        for message_chunk, metadata in graph.stream(
            {"messages": [HumanMessage(content=request.message)]},
            config={"configurable": {"thread_id": thread_id}},
            stream_mode="messages",
        ):
            # streaming los tokens de mensajes
            if isinstance(message_chunk, AIMessageChunk):
                token = message_chunk.content
                if token:
                    yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")


# healthcheck
@app.get("/health") 
async def health():
    return {"status": "ok"}