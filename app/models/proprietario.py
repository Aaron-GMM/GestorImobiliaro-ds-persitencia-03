from beanie import Document
from pydantic import BaseModel, Field

class ProprietarioCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=200)
    email: str
    senha: str = Field(min_length=8)
    endereco: str | None = None

class ProprietarioUpdate(BaseModel):
    nome: str | None = None
    email: str | None = None
    senha: str | None = None
    endereco: str | None = None

class Proprietario(Document):
    nome: str
    email: str
    senha: str
    endereco: str | None = None

    class Settings:
        name = "proprietarios"