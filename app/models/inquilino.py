from beanie import Document, Link
from pydantic import BaseModel, Field
from .proprietario import Proprietario


class InquilinoCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=200)
    cpf: str = Field(min_length=11, max_length=14)
    email: str
    telefone: str
    renda_mensal: float = Field(gt=0)
    id_proprietario: str


class InquilinoUpdate(BaseModel):
    nome: str | None = None
    cpf: str | None = None
    email: str | None = None
    telefone: str | None = None
    renda_mensal: float | None = None


class InquilinoResponse(BaseModel):
    id: str
    nome: str
    cpf: str
    email: str
    telefone: str
    renda_mensal: float
    id_proprietario: str


class Inquilino(Document):
    nome: str = Field(min_length=3, max_length=200)
    cpf: str = Field(min_length=11, max_length=14)
    email: str
    telefone: str
    renda_mensal: float = Field(gt=0)
    proprietario: Link[Proprietario]

    class Settings:
        name = "inquilinos"
