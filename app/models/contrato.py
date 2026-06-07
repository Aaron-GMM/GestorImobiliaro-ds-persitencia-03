from datetime import date
from beanie import Document, Link
from pydantic import BaseModel, Field
from .inquilino import Inquilino
from .imovel import Imovel


class ContratoMetrics(BaseModel):
    """Métricas de contratos."""
    contratos_ativos: int
    contratos_vencendo: int
    imoveis_disponiveis: int

class ContratoCreate(BaseModel):
    """Schema para criação de contrato."""
    id_inquilino: str = Field(description="ID do inquilino")
    id_imovel: str = Field(description="ID do imóvel")
    data_inicio: date
    data_fim: date
    valor_aluguel: float = Field(gt=0)
    dia_vencimento: int = Field(ge=1, le=31)


class ContratoUpdate(BaseModel):
    """Schema para atualização parcial de contrato."""
    data_inicio: date | None = None
    data_fim: date | None = None
    valor_aluguel: float | None = None
    status: str | None = None
    dia_vencimento: int | None = None


class Contrato(Document):
    """
    Documento que representa um contrato de aluguel.
    Estabelece a relação Muitos-para-Muitos entre Inquilino e Imóvel.
    """
    inquilino: Link[Inquilino]
    imovel: Link[Imovel]
    data_inicio: date
    data_fim: date
    valor_aluguel: float = Field(gt=0)
    dia_vencimento: int = Field(ge=1, le=31)
    status: str = "Ativo"  # Ativo, Encerrado, Cancelado

    class Settings:
        name = "contratos"