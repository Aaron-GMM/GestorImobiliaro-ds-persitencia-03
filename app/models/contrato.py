from datetime import date
from beanie import Document, Link
from .inquilino import Inquilino
from .imovel import Imovel

class Contrato(Document):
    inquilino: Link[Inquilino]
    imovel: Link[Imovel]
    data_inicio: date
    data_fim: date
    valor_aluguel: float
    status: str = "Ativo" # Ativo, Encerrado, Cancelado

    class Settings:
        name = "contratos"