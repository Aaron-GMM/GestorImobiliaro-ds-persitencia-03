from pydantic import BaseModel

class Statistics(BaseModel):
    imoveis_alugados: int
    imoveis_disponiveis: int
    pagamentos_pendentes: int

class RecentActivity(BaseModel):
    imovel_alugado: str
    inquilino: str
    imovel_disponivel: str