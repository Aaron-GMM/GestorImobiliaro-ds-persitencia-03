from beanie import Document
from pydantic import BaseModel, Field

class ProprietarioCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=200)
    cpf: str = Field(min_length=11, max_length=14)
    email: str | None = None
    telefone: str
    endereco: str | None = None

class ProprietarioUpdate(BaseModel):
    nome: str | None = None
    cpf: str | None = None
    email: str | None = None
    telefone: str | None = None
    endereco: str | None = None

# --- Document ---
class Proprietario(Document):
    nome: str
    cpf: str
    email: str | None = None
    telefone: str
    endereco: str | None = None

    class Settings:
        name = "proprietarios"