import gradio as gr
import requests
import uuid
import json
from dotenv import load_dotenv 
import os

"""
se utiliza la librería gradio para hacer el front de una demo rápida 
"""

load_dotenv()
URL =os.getenv("STREAM_URL") #URL del endpoint

STREAM_URL = URL


def respond(message: str, history: list, thread_id: str):
    """
    Función que Gradio ejecuta cada vez que el usuario envía un mensaje.

    - Envía el mensaje al endpoint /chat/stream.
    - Recibe tokens en tiempo real mediante Server-Sent Events (SSE).
    - Va acumulando la respuesta parcial y la muestra progresivamente.
    - Mantiene el thread_id para conservar el contexto conversacional.
    """

    # Si no existe thread_id, significa que es una conversación nueva
    if not thread_id:
        thread_id = str(uuid.uuid4())

    partial_reply = ""

    # Realizamos la petición POST en modo streaming
    with requests.post(
        STREAM_URL,
        json={"message": message, "thread_id": thread_id},
        stream=True,  # keep the HTTP connection open
    ) as response:
        response.raise_for_status()

        for raw_line in response.iter_lines():
            if not raw_line:
                continue  

            line = raw_line.decode("utf-8")
            if not line.startswith("data: "):
                continue # solo se procesan eventos SSE válidos

            data = json.loads(line[len("data: "):])
            # Primer mensaje: el servidor envía el thread_id
            if data["type"] == "thread_id":
                thread_id = data["value"]  
            # Tokens generados por el modelo en tiempo real
            elif data["type"] == "token":
                partial_reply += data["value"]
                yield partial_reply, thread_id  

            elif data["type"] == "done":
                break

# Interfaz Gradio
with gr.Blocks(title="Mingothings task - University Advisor") as demo:
    gr.Markdown("## Mingothings task - University Advisor")
    gr.Markdown("Pregunta sobre **grados**, **asignatuas**, o **salidas**.")

    thread_id_state = gr.State("")
    # ChatInterface simplifica la creación de un chatbot completo
    gr.ChatInterface(
        fn=respond, # función que procesa cada mensaje
        additional_inputs=[thread_id_state],
        additional_outputs=[thread_id_state],
        chatbot=gr.Chatbot(height=500, label="Mingo"),
        textbox=gr.Textbox(
            placeholder="e.g. ¿Qué asignaturas tiene enfermería?",
            label="",
            scale=7,
        ),
        submit_btn="Send",
        examples=[["¿Qué asignaturas tiene el grado de enfermería?"],
            ["¿Qué salidas laborales tiene derecho?"],
            ["¿Qué competencias se adquieren en medicina?"],
        ],
    )
# Lanzamos la interfaz en localhost:7860
if __name__ == "__main__":
    demo.launch(server_port=7860)