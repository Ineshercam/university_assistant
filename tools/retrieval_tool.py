import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

from dotenv import load_dotenv 
import os

"""
se utiliza la librería gradio para hacer el front de una demo rápida 
"""

load_dotenv()
CHROMA_PATH =os.getenv("CHROMA_PATH") #PATH A LA BBDD
COLLECTION=os.getenv("COLLECTION") #Nombre de la colección

"""
La recuperación de docs de la bbdd chroma se hace como una herramienta.
la bbdd vectorial no se debería cargar en memoria, pero al ser una prueba simple la cargamos desde un path local
"""

CHROMA_PATH = CHROMA_PATH #path a la bbdd
COLLECTION_NAME = COLLECTION

# Cargamos el modelo de embeddings en este caso Qwen3-Embedding-4B
model = SentenceTransformer("Qwen/Qwen3-Embedding-4B")

# Cargamos chroma, la base de datos vectorial
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection(COLLECTION_NAME)


# función de la tool
def retrieve_docs(query: str, k: int = 5) -> List[Dict[str, Any]]:
    print("\n===== TOOL: retrieve_docs =====") #log
    print("Query:", query)

    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k
    )

    # aplanamos el output
    docs = []
    for i in range(len(results["documents"][0])):
        docs.append({
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "id": results["ids"][0][i]
        })
    print("Retrieved docs:", len(docs))
    print("Preview:", docs[0]["content"][:200] if docs else "EMPTY")

    return docs
