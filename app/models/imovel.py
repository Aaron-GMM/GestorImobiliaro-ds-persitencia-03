from beanie import Document, Link
from pydantic import BaseModel, Field
from .proprietario import Proprietario


class ImovelCreate(BaseModel):
    apelido_imovel: str = Field(min_length=3, max_length=100)
    descricao: str | None = None
    endereco: str
    valor_aluguel_base: float = Field(gt=0)
    tipo_imovel: str
    status: str = "Disponivel"
    id_proprietario: str # Recebe a string do ID para buscar depois

class ImovelUpdate(BaseModel):
    apelido_imovel: str | None = None
    descricao: str | None = None
    endereco: str | None = None
    valor_aluguel_base: float | None = None
    tipo_imovel: str | None= None
    status: str | None = None



class Imovel(Document):
    apelido_imovel: str
    descricao: str | None = None
    endereco: str
    valor_aluguel_base: float
    tipo_imovel: str
    status: str
    proprietario: Link[Proprietario]

    class Settings:
        name = "imoveis"