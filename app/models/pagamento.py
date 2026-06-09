from datetime import date
from beanie import Document, Link
from pydantic import BaseModel, Field

from app.models.imovel import Imovel
from .proprietario import Proprietario
from .contrato import Contrato
from .inquilino import Inquilino

class ConfigEncargo(BaseModel):
    """Schema para configuração de encargos de pagamento em atraso."""
    multa_percentual: float = Field(default=2.0, ge=0, le=100, description="Percentual de multa por atraso")
    juros_mora: float = Field(default=0.33, ge=0, le=100, description="Percentual de juros de mora ao dia")
    tolerancia_dias: int = Field(default=0, ge=0, le=30, description="Dias de tolerância antes de cobrar encargos")
    valor_minimo_multa: float = Field(default=0.0, ge=0, description="Valor mínimo da multa")
    id_proprietario: str = Field(description="ID do proprietário associado ao encargo")
class Encargo(Document):
    """Schema para configuração de encargos de pagamento em atraso."""
    multa_percentual: float = Field(default=2.0, ge=0, le=100, description="Percentual de multa por atraso")
    juros_mora: float = Field(default=0.33, ge=0, le=100, description="Percentual de juros de mora ao dia")
    tolerancia_dias: int = Field(default=0, ge=0, le=30, description="Dias de tolerância antes de cobrar encargos")
    valor_minimo_multa: float = Field(default=0.0, ge=0, description="Valor mínimo da multa")
    proprietario: Link[Proprietario] = Field(description="Proprietário associado ao encargo")

class PagamentoResponse(BaseModel):
    """
    Schema para resposta de pagamento.
    """
    id: str = Field(description="ID do pagamento")
    imovel: Imovel = Field(description="Imóvel associado ao pagamento")
    inquilino: Inquilino = Field(description="Inquilino associado ao pagamento")
    proprietario: Proprietario | None = Field(default=None, description="Proprietário associado ao pagamento")
    numero_parcela: str = Field(description="Número da parcela (ex: 01/12)")
    data_vencimento: date = Field(description="Data de vencimento da parcela")
    valor_original: float = Field(gt=0, description="Valor original da parcela")
    multa: float = Field(default=0.0, ge=0, description="Valor da multa aplicada")
    juros: float = Field(default=0.0, ge=0, description="Valor dos juros aplicados")
    valor_total: float = Field(gt=0, description="Valor total a ser pago")
    status: str = Field(default="Pendente", description="Pendente, Atrasado, Pago")
    data_pagamento: date | None = None
    
class PagamentoMetrics(BaseModel):
    """
    Schema para métricas de pagamentos.
    """
    pendentes: int
    atrasados: int
    pagos_mes: int

class Pagamento(Document):
    """
    Documento que representa uma parcela de pagamento de aluguel.
    Criado automaticamente a partir de um contrato.
    """
    contrato: Link[Contrato] = Field(description="Contrato associado ao pagamento")
    numero_parcela: str = Field(description="Número da parcela (ex: 01/12)")
    data_vencimento: date = Field(description="Data de vencimento da parcela")
    valor_original: float = Field(gt=0, description="Valor original da parcela")
    multa: float = Field(default=0.0, ge=0, description="Valor da multa aplicada")
    juros: float = Field(default=0.0, ge=0, description="Valor dos juros aplicados")
    valor_total: float = Field(gt=0, description="Valor total a ser pago")
    status: str = Field(default="Pendente", description="Pendente, Atrasado, Pago")
    data_pagamento: date | None = Field(default=None, description="Data de pagamento")
    proprietario: Link[Proprietario] = Field(description="Proprietário associado ao pagamento")

    class Settings:
        name = "pagamentos"
