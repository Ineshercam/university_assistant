import os
import json
import uuid
import math
import chromadb
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

from pydub import AudioSegment
import torch
from qwen_asr import Qwen3ASRModel


# Rutas y nombres de archivos
JSON_DIR = "filtered_output"      # Carpeta con los JSON generados desde los PDFs
QA_FILE = "qa.json"               # Archivo con pares pregunta–respuesta
CHROMA_PATH = "chroma_ucm"        # Carpeta donde se guardará la base vectorial
COLLECTION_NAME = "ucm_grados"    # Nombre de la colección en ChromaDB

# Modelos utilizados
AUDIO_MODEL_NAME = "Qwen/Qwen3-ASR-1.7B"          # Modelo de transcripción
EMBED_MODEL_NAME = "Qwen/Qwen3-Embedding-4B"      # Modelo de embeddings


def transcribe_audio(audio_path):
    """
    Divide el audio en fragmentos de 30 segundos, los transcribe con Qwen ASR
    y devuelve un único texto concatenado.
    """
    audio = AudioSegment.from_file(audio_path)
    chunk_ms = 30_000
    chunks = math.ceil(len(audio) / chunk_ms)

    model = Qwen3ASRModel.from_pretrained(
        AUDIO_MODEL_NAME,
        dtype=torch.bfloat16,
        device_map="cuda:1",
        max_new_tokens=512,
    )

    full_text = []

    for i in range(chunks):
        chunk = audio[i * chunk_ms : (i + 1) * chunk_ms]
        chunk_path = f"/tmp/chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")

        result = model.transcribe(chunk_path, language=None)
        full_text.append(result[0].text)

    return " ".join(full_text)


def load_json_grados(texts, metadatas, ids):
    """
    Lee todos los JSON de grados y genera textos y metadatos
    para conocimientos y salidas profesionales.
    """
    print("Cargando JSONs de grados...")

    for file in os.listdir(JSON_DIR):
        if not file.endswith(".json"):
            continue

        path = os.path.join(JSON_DIR, file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        degree = data.get("degree_title", "")
        degree_type = data.get("degree_type", "")
        faculties = data.get("faculties", [])
        conocimientos = data.get("conocimientos", "")
        salidas = data.get("salidas_profesionales", "")

        # Texto para conocimientos
        t1 = f"Conocimientos para el grado de {degree}: {conocimientos}"
        texts.append(t1)
        metadatas.append({
            "degree": degree,
            "type": degree_type,
            "faculties": faculties,
            "section": "conocimientos",
            "source_file": file
        })
        ids.append(str(uuid.uuid4()))

        # Texto para salidas profesionales
        t2 = f"Salidas profesionales para el grado de {degree}: {salidas}"
        texts.append(t2)
        metadatas.append({
            "degree": degree,
            "type": degree_type,
            "faculties": faculties,
            "section": "salidas_profesionales",
            "source_file": file
        })
        ids.append(str(uuid.uuid4()))


def load_qa(texts, metadatas, ids):
    """
    Carga pares de pregunta–respuesta desde qa.json
    y los añade como documentos a indexar.
    """
    if not os.path.exists(QA_FILE):
        return

    print("Cargando pares de QA...")

    with open(QA_FILE, "r", encoding="utf-8") as f:
        qa_pairs = json.load(f)

    for pair in qa_pairs:
        question = pair.get("question", "")
        answer = pair.get("answer", "")
        degree = pair.get("degree", "Enfermería")

        page = (
            f"Pregunta: {question}\n"
            f"Respuesta: {answer}\n"
            f"Grado: {degree}"
        )

        texts.append(page)
        metadatas.append({
            "degree": degree,
            "section": "qa"
        })
        ids.append(str(uuid.uuid4()))


def load_audio(texts, metadatas, ids, audio_path):
    """
    Transcribe un archivo de audio y lo añade como documento.
    """
    print("Transcribiendo audio...")
    transcript = transcribe_audio(audio_path)

    texts.append(f"Transcripción de audio: {transcript}")
    metadatas.append({
        "section": "audio_transcript",
        "source_file": audio_path
    })
    ids.append(str(uuid.uuid4()))


def generate_embeddings(texts):
    """
    Genera embeddings para todos los textos usando Qwen Embeddings.
    """
    print("Cargando modelo de embeddings...")
    model = SentenceTransformer(EMBED_MODEL_NAME, device="cuda")

    embeddings = []
    batch_size = 1

    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
        batch = texts[i : i + batch_size]
        batch_embeddings = model.encode(batch)
        embeddings.extend(batch_embeddings)

    return embeddings


def save_to_chroma(texts, metadatas, ids, embeddings):
    """
    Crea una colección persistente en ChromaDB y añade todos los documentos.
    """
    print(f"Creando base de datos persistente en: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection(COLLECTION_NAME)
    except:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    print("Insertando documentos...")

    for i in tqdm(range(len(texts)), desc="Insertando"):
        collection.add(
            embeddings=[embeddings[i]],
            documents=[texts[i]],
            metadatas=[metadatas[i]],
            ids=[ids[i]]
        )

    print("Ingesta completada.")
    print(f"Base de datos guardada en: {os.path.abspath(CHROMA_PATH)}")


def main(audio=False, audio_path=None):
    """
    Orquesta todo el proceso de ingesta:
    - JSONs de grados
    - QA
    - Audio opcional
    - Embeddings
    - Inserción en ChromaDB
    """
    texts = []
    metadatas = []
    ids = []

    load_json_grados(texts, metadatas, ids)
    load_qa(texts, metadatas, ids)

    if audio and audio_path:
        load_audio(texts, metadatas, ids, audio_path)

    print(f"Total de fragmentos a indexar: {len(texts)}")

    embeddings = generate_embeddings(texts)
    save_to_chroma(texts, metadatas, ids, embeddings)


if __name__ == "__main__":
    # Ejemplos de uso:
    # main()
    # main(audio=True, audio_path="/ruta/audio.m4a")
    main()
