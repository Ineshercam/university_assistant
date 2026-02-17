import json
from glob import glob
import unicodedata
from dotenv import load_dotenv 
import os

"""
Aquí se define la función de get_subjects. Idealmente se guarfaría en una base de datos, sin embargo por hacerlo de manera muy
simple usamos un diccionario que se carga en memoria y se consulta cuando es necesario
"""
load_dotenv()

folder_path = os.getenv("PATH_DICT_SUBJECTS") #path a los jsons
data_list = []

#Se leen todos los jsons del path y se guardan en una lista
for file_path in glob(f"{folder_path}/*.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        data_list.append(json.load(f))


def normalize(text: str) -> str:
    """
    Para asegurarnos de que el nombre de los grados puede ir con tildes, sin tildes, mayusculas etc, se normaliza el texto
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower().strip()

def degree_matches(query, title):
    print("AQUI", query)
    q = normalize(query).split()
    print(q)
    t = normalize(title)

    return all(word in t for word in q)

def retrieve_subjects(query):
    
    print("TOOL RETRIEVE_SUBJECT") #log
    print(query)
    matches = []

    for degree in data_list:
        if degree_matches(query, degree["degree_title"]):
            subjects = []
            for year, items in degree["plan_estudios"].items():
                for item in items:
                    subjects.append(item["subject"])

            matches.append({
                "degree_title": degree["degree_title"],
                "subjects": subjects
            })
    # se aplana la info ya que el LLM se confundía al ver el dict y tendía a llamar la tool varias veces
    lines= [] 
    for match in matches:
        lines.append(f"Grado: {match['degree_title']}")
        lines.append("Asignaturas:")
        for subject in match["subjects"]:
            lines.append(f"  - {subject}")
        lines.append("") 

    return "\n".join(lines)

print(retrieve_subjects("turismo"))




