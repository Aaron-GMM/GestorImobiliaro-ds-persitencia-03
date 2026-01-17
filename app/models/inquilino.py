from beanie import Document
from pydantic import Field

class Inquilino(Document):
    nome: str = Field(min_length=3, max_length=200)
    cpf: str = Field(min_length=11, max_length=14)
    email: str
    telefone: str
    renda_mensal: float = Field(gt=0)

    class Settings:
        name = "inquilinos"

