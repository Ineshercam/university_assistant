import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# URL base de la UCM
BASE_URL = "https://www.ucm.es"
# Página inicial donde están todos los grados
START_URL = "https://www.ucm.es/estudios/grado"

# Carpeta donde se guardarán los PDFs
OUTPUT_DIR = "dipticos_all"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Cabeceras para evitar bloqueos del servidor
headers = {
    "User-Agent": "Mozilla/5.0 (compatible; UCM-PDF-Scraper/1.0)"
}

def get_soup(url):
    """
    Descarga una página y devuelve un objeto BeautifulSoup.
    """
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def sanitize_filename(name):
    """
    Limpia un nombre para que sea válido como nombre de archivo.
    """
    return "".join(c for c in name if c.isalnum() or c in " -_").rstrip()

print("Cargando página principal...")
soup = get_soup(START_URL)

# -------------------------------------------------------------------
# PASO 1 — Extraer todos los enlaces a los grados y sus títulos
# -------------------------------------------------------------------
degree_links = []

for ul in soup.select("ul.menu_pag"):
    for a in ul.select("a"):
        href = a.get("href", "")
        title = a.get("title", "").strip()

        # Convertir enlaces relativos a absolutos
        if href.startswith("http"):
            degree_links.append((href, title))
        else:
            degree_links.append((urljoin(BASE_URL, href), title))

print(f"Encontradas {len(degree_links)} páginas de grados.")

# -------------------------------------------------------------------
# PASO 2 — Visitar cada página de grado y descargar el PDF del díptico
# -------------------------------------------------------------------
for link, title in degree_links:
    print(f"\nVisitando: {link}")
    soup = get_soup(link)

    # Intentar obtener el nombre del grado desde el encabezado
    title_block = soup.select_one(".titulo-estudio h2")
    if title_block:
        degree_name = title_block.text.strip()
    else:
        h2 = soup.find("h2")
        degree_name = h2.text.strip() if h2 else "unknown_degree"

    # Buscar el enlace al PDF del díptico
    pdf_link = None
    for a in soup.select("a"):
        text = (a.text or "").lower()
        href = a.get("href", "")
        # Buscar enlaces que contengan "díptico" y terminen en .pdf
        if "díptico" in text and href.endswith(".pdf"):
            pdf_link = urljoin(BASE_URL, href)
            break

    if not pdf_link:
        print("  No se encontró el 'Díptico de la titulación'.")
        continue

    # Elegir nombre del archivo: preferir el atributo title del enlace
    if title:
        filename = sanitize_filename(title) + ".pdf"
    else:
        filename = sanitize_filename(degree_name) + ".pdf"

    filepath = os.path.join(OUTPUT_DIR, filename)

    print(f"  Descargando: {filename}")
    pdf_resp = requests.get(pdf_link, headers=headers)
    pdf_resp.raise_for_status()

    # Guardar el PDF
    with open(filepath, "wb") as f:
        f.write(pdf_resp.content)

    # Pausa para no saturar el servidor
    time.sleep(1)

print("\n¡Listo! Todos los PDFs están en la carpeta 'dipticos_all'.")
