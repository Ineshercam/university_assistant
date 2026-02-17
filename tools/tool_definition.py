

from langchain_core.tools import StructuredTool

from pydantic import BaseModel, Field
from tools.retrieval_tool import retrieve_docs
from tools.get_subjects import retrieve_subjects
from agent.tools_agent import RetrieveDocsInput, RetrieveSubjectsInput


class RetrieveDocsInput(BaseModel):
    """
    query: str  
    Representa la consulta del usuario. Es el texto que se va a utilizar para recuperar documentos de la bbdd vectorial

    k: int = 5  
    Indica cuántos documentos se desean recuperar.
    """
    query: str = Field(..., description="Query to search in ChromaDB")
    k: int = Field(5, description="Number of results to return")


class RetrieveSubjectsInput(BaseModel):
    """
    query: str
    como se indica abajo, es el nombre del grado del que se desea extraer información 
    (no necesariamente debe ser exacto porque se preprocesará pero debe acercarse lo mas posible)
    """
    query: str = Field(..., description="Degree name to extract subjects for, in spanish")

retrieve_docs_tool = StructuredTool.from_function(
    name="retrieve_docs",
    description=(
        "Retrieve information about possible jobs and skills acquired after completing a degree. "
        "Use this when the user asks about career opportunities or competencies of a degree."
        "Use this also for general questions about a degree for example 'Por qué elegir la carrera de diseño?' "
    ),
    func=retrieve_docs,
    args_schema=RetrieveDocsInput,
)

retrieve_subjects_tool = StructuredTool.from_function(
    name="retrieve_subjects",
    description=(
        "Retrieve the full list of subjects for a specific university degree at UCM. "
        "ALWAYS use this tool when the user asks about subjects, courses, or the study plan of any degree. "
        "Pass the degree name in Spanish (e.g. 'enfermería', 'derecho', 'medicina')."
    ),
    func=retrieve_subjects,
    args_schema=RetrieveSubjectsInput,
)

tools = [retrieve_docs_tool, retrieve_subjects_tool]