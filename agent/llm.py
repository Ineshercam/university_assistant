from tools_agent import tools  
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv 
import os

# Cargamos la open_api_key como variable de entorno. Debe ir en el fichero .env
load_dotenv()
OPEN_AI_KEY =os.getenv("OPENAI_API_KEY")


# Instaciamos el LLM, en este caso se usa la api de openAI el modelo gpt-4o
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0, #temperatura a 0 para evitar respuestas "creativas"
    streaming=True, #streaming para la experiencia de usuario
    api_key=OPEN_AI_KEY
).bind_tools(tools)
