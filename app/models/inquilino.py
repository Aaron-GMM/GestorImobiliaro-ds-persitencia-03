from beanie import Document
from pydantic import BaseModel, Field


class InquilinoCreate(BaseModel):
    """Schema para criação de inquilino."""
    nome: str = Field(min_length=3, max_length=200)
    cpf: str = Field(min_length=11, max_length=14)
    email: str
    telefone: str
    renda_mensal: float = Field(gt=0)


class InquilinoUpdate(BaseModel):
    """Schema para atualização parcial de inquilino."""
    nome: str | None = None
    cpf: str | None = None
    email: str | None = None
    telefone: str | None = None
    renda_mensal: float | None = None


class Inquilino(Document):
    """Documento que representa um inquilino no sistema."""
    nome: str = Field(min_length=3, max_length=200)
    cpf: str = Field(min_length=11, max_length=14)
    email: str
    telefone: str
    renda_mensal: float = Field(gt=0)

    class Settings:
        name = "inquilinos"

