import os
import json
import re
import pdfplumber
import tabula
from itertools import groupby

"""
extraer información de los pdfs de modo que se guarde un json por pdf con la estructura:

{
        "degree_title": titulo,
        "degree_type": tipo,
        "faculties": facultades,
        "plan_estudios": plan_estudios,
        "conocimientos": conocimientos,
        "salidas_profesionales": salidas
    }
"""

# ---------------------------------------------------------
# CONFIGURACIÓN DE DIRECTORIOS
# ---------------------------------------------------------
PDF_DIR = "filtered"              # Carpeta donde están los PDFs filtrados
OUTPUT_DIR = "filtered_output"    # Carpeta donde guardaremos los JSON
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------
def clean(text):
    """Elimina saltos de línea y espacios sobrantes."""
    return text.replace("\n", " ").strip()


# ---------------------------------------------------------
# 1. EXTRAER LÍNEAS DE TEXTO AGRUPADAS POR ALTURA (Y)
# ---------------------------------------------------------
def extract_lines(page):
    """
    Agrupa caracteres por su posición vertical (top) para reconstruir líneas.
    """
    chars = page.chars
    lines = []

    for y, line_chars in groupby(chars, key=lambda c: round(c["top"], 1)):
        line_chars = list(line_chars)
        text = "".join(c["text"] for c in line_chars).strip()
        if not text:
            continue
        lines.append(text)

    return lines


# ---------------------------------------------------------
# 1B. EXTRAER LÍNEAS + TAMAÑO DE FUENTE
# ---------------------------------------------------------
def extract_lines_with_font_sizes(page):
    """
    Devuelve una lista de tuplas (texto, tamaño de fuente promedio)
    ordenadas de arriba a abajo.
    """
    chars = page.chars
    lines = {}

    # Agrupar por coordenada Y
    for c in chars:
        y = round(c["top"], 1)
        lines.setdefault(y, []).append(c)

    results = []
    for y in sorted(lines.keys()):
        line_chars = sorted(lines[y], key=lambda c: c["x0"])
        text = "".join(c["text"] for c in line_chars).strip()
        if not text:
            continue
        avg_size = sum(c["size"] for c in line_chars) / len(line_chars)
        results.append((text, avg_size))

    return results


# ---------------------------------------------------------
# 2. EXTRAER INFORMACIÓN DEL GRADO (TÍTULO, TIPO, FACULTADES)
# ---------------------------------------------------------
def extract_degree_info(lines):
    """
    A partir de las líneas con tamaños de fuente, identifica:
    - Título del grado (fuente más grande)
    - Tipo de grado (línea que contiene "grado")
    - Facultades (líneas que contienen "facultad")
    """
    if not lines:
        return "", "", []

    # Tamaño máximo fijo (ajustado manualmente)
    max_size = 32

    # Título del grado = líneas con tamaño >= max_size
    degree_title_parts = [text for text, size in lines if size >= max_size]
    degree_title = " ".join(degree_title_parts).strip()

    # Tipo de grado = primera línea con "grado"
    degree_type = ""
    for text, size in lines:
        if size < max_size and "grado" in text.lower():
            degree_type = text.strip()
            break

    # Facultades
    faculties = [text.strip() for text, size in lines if "facultad" in text.lower()]

    return degree_title, degree_type, faculties


# ---------------------------------------------------------
# 3. EXTRAER PLAN DE ESTUDIOS (TABLA DE ASIGNATURAS)
# ---------------------------------------------------------
def extract_plan_estudios(page):
    """
    Extrae las asignaturas y créditos del plan de estudios.
    Devuelve un diccionario por curso.
    """
    lines = extract_lines(page)
    plan = {}
    current_year = None
    buffer_subject = ""

    year_pattern = re.compile(r"(PRIMER|SEGUNDO|TERCER|CUARTO|QUINTO|SEXTO)\s+CURSO", re.IGNORECASE)
    ects_pattern = re.compile(r"(\d+[.,]?\d*(?:\s*\+\s*\d+[.,]?\d*)*)$")

    for line in lines:
        line = line.strip()

        # Detectar encabezado de curso
        year_match = year_pattern.search(line)
        if year_match:
            current_year = year_match.group(0).upper()
            plan[current_year] = []
            continue

        # Ignorar encabezados
        if "ECTS" in line.upper():
            continue

        if not current_year:
            continue

        # Detectar créditos al final de la línea
        ects_match = ects_pattern.search(line)

        if ects_match:
            ects = ects_match.group(1)
            subject_part = line[:ects_match.start()].strip()

            # Unir líneas partidas
            if buffer_subject:
                subject_part = buffer_subject + " " + subject_part
                buffer_subject = ""

            plan[current_year].append({
                "subject": subject_part.strip(),
                "ects": ects.strip()
            })

        else:
            # Nombre de asignatura partido en varias líneas
            buffer_subject = buffer_subject + " " + line if buffer_subject else line

    return plan


# ---------------------------------------------------------
# 4. EXTRAER CONOCIMIENTOS Y SALIDAS PROFESIONALES
# ---------------------------------------------------------
def extract_lines_two_columns(page):
    """
    Divide la página en dos columnas y reconstruye las líneas de cada una.
    """
    width = page.width
    mid_x = width / 2

    left_chars = []
    right_chars = []

    # Separar caracteres por columna
    for c in page.chars:
        (left_chars if c["x0"] < mid_x else right_chars).append(c)

    def build_lines(chars):
        lines = {}
        for c in chars:
            y = round(c["top"], 2)
            lines.setdefault(y, []).append(c)

        ordered = []
        for y in sorted(lines.keys()):
            line_chars = sorted(lines[y], key=lambda c: c["x0"])
            text = "".join(c["text"] for c in line_chars).strip()
            if text:
                ordered.append(text)
        return ordered

    return build_lines(left_chars) + build_lines(right_chars)


def remove_heading_line(text, phrase):
    """Elimina encabezados como 'que se adquieren' o 'profesionales'."""
    pattern = r"^\s*" + re.escape(phrase) + r"\s*"
    return re.sub(pattern, "", text, count=1, flags=re.IGNORECASE)


def extract_sections(page):
    """
    Extrae los apartados:
    - Conocimientos que se adquieren
    - Salidas profesionales
    """
    lines = extract_lines_two_columns(page)
    full_text = "\n".join(lines)

    conocimientos = ""
    salidas = ""

    if "Conocimientos" in full_text and "Salidas" in full_text:
        conocimientos_part = full_text.split("Conocimientos", 1)[1].split("Salidas", 1)[0]
        salidas_part = full_text.split("Salidas", 1)[1]

        conocimientos = remove_heading_line(conocimientos_part, "que se adquieren")
        salidas = remove_heading_line(salidas_part, "profesionales")

    return conocimientos.strip(), salidas.strip()


# ---------------------------------------------------------
# 5. BUCLE PRINCIPAL: PROCESAR TODOS LOS PDFs
# ---------------------------------------------------------
for pdf_file in os.listdir(PDF_DIR):
    if not pdf_file.endswith(".pdf"):
        continue

    pdf_path = os.path.join(PDF_DIR, pdf_file)
    print(f"Processing {pdf_file}")

    with pdfplumber.open(pdf_path) as pdf:
        page1 = pdf.pages[0]
        page2 = pdf.pages[1]
        page3 = pdf.pages[2]

        # Extraer líneas con tamaños de fuente
        lines_page1 = extract_lines_with_font_sizes(page1)
        lines_page3 = extract_lines_with_font_sizes(page3)

        # Extraer texto normal
        page2_text = page2.extract_text()
        page3_text = page3.extract_text()

    # Extraer información del grado
    degree_title, degree_type, faculties = extract_degree_info(lines_page1)
    conocimientos, salidas = extract_sections(page3)

    # Extraer plan de estudios
    plan_estudios = extract_plan_estudios(page2)

    # Construir JSON final
    data = {
        "degree_title": degree_title,
        "degree_type": degree_type,
        "faculties": faculties,
        "plan_estudios": plan_estudios,
        "conocimientos": conocimientos,
        "salidas_profesionales": salidas
    }

    # Guardar JSON
    json_path = os.path.join(OUTPUT_DIR, pdf_file.replace(".pdf", ".json"))
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

print("Done! JSON files saved.")
