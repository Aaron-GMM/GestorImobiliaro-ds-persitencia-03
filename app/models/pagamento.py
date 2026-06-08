from datetime import date
from beanie import Document, Link
from pydantic import BaseModel, Field
from .contrato import Contrato


class PagamentoMetrics(BaseModel):
    pendentes: int
    atrasados: int
    pagos_mes: int

class Pagamento(Document):
    """
    Documento que representa uma parcela de pagamento de aluguel.
    Criado automaticamente a partir de um contrato.
    """
    contrato: Link[Contrato]
    numero_parcela: str = Field(description="Número da parcela (ex: 01/12)")
    data_vencimento: date
    valor_original: float = Field(gt=0)
    multa: float = Field(default=0.0, ge=0)
    juros: float = Field(default=0.0, ge=0)
    valor_total: float = Field(gt=0)
    status: str = Field(default="Pendente", description="Pendente, Atrasado, Pago")
    data_pagamento: date | None = None

    class Settings:
        name = "pagamentos"
