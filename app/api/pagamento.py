"""
Rotas da API para gerenciamento de Pagamentos.
"""
from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query
from app.models.pagamento import Pagamento
from app.models.contrato import Contrato

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])


@router.get("/", response_model=list[Pagamento])
async def listar_pagamentos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: str | None = Query(None, description="Filtrar por status (Pendente, Atrasado, Pago)"),
    id_contrato: str | None = Query(None, description="Filtrar por contrato")
):
    """
    Lista todos os pagamentos com paginação e filtros opcionais.
    
    Args:
        skip: Número de registros a pular.
        limit: Número máximo de registros a retornar.
        status: Filtrar por status do pagamento.
        id_contrato: Filtrar por contrato específico.
    
    Returns:
        Lista de pagamentos.
    """
    filtros = {}
    
    if status:
        filtros["status"] = status
    
    if id_contrato:
        if not PydanticObjectId.is_valid(id_contrato):
            raise HTTPException(status_code=400, detail="ID de contrato inválido")
        filtros["contrato.$id"] = PydanticObjectId(id_contrato)
    
    if filtros:
        pagamentos = await Pagamento.find(filtros).skip(skip).limit(limit).to_list()
    else:
        pagamentos = await Pagamento.find_all().skip(skip).limit(limit).to_list()
    
    return pagamentos


@router.get("/contrato/{id_contrato}", response_model=list[Pagamento])
async def listar_pagamentos_por_contrato(id_contrato: str):
    """
    Lista todos os pagamentos de um contrato específico.
    
    Args:
        id_contrato: ID do contrato.
    
    Returns:
        Lista de pagamentos do contrato.
    
    Raises:
        HTTPException: Se o ID for inválido.
    """
    if not PydanticObjectId.is_valid(id_contrato):
        raise HTTPException(status_code=400, detail="ID de contrato inválido")
    
    return await Pagamento.find(
        {"contrato.$id": PydanticObjectId(id_contrato)}
    ).to_list()


@router.get("/{id}", response_model=Pagamento)
async def obter_pagamento(id: str):
    """
    Obtém um pagamento pelo ID.
    
    Args:
        id: ID do pagamento.
    
    Returns:
        Pagamento encontrado.
    
    Raises:
        HTTPException: Se o ID for inválido ou pagamento não encontrado.
    """
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    pagamento = await Pagamento.get(id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return pagamento


@router.get("/metrics/geral")
async def obter_metricas_pagamentos():
    """
    Retorna métricas gerais de pagamentos.
    
    Métricas:
    - pendentes: Número de pagamentos pendentes
    - atrasados: Número de pagamentos atrasados
    - pagos_mes: Número de pagamentos realizados no mês atual
    
    Returns:
        Dicionário com as métricas solicitadas.
    """
    from datetime import date, timedelta
    
    hoje = date.today()
    primeiro_dia_mes = date(hoje.year, hoje.month, 1)
    
    # Pipeline para contar pendentes
    pipeline_pendentes = [
        {"$match": {"status": "Pendente"}},
        {"$count": "total"}
    ]
    
    # Pipeline para contar atrasados
    pipeline_atrasados = [
        {"$match": {"status": "Atrasado"}},
        {"$count": "total"}
    ]
    
    # Pipeline para contar pagos no mês
    pipeline_pagos_mes = [
        {"$match": {
            "status": "Pago",
            "data_pagamento": {"$gte": primeiro_dia_mes}
        }},
        {"$count": "total"}
    ]
    
    try:
        resultado_pendentes = await Pagamento.aggregate(pipeline_pendentes).to_list()
        resultado_atrasados = await Pagamento.aggregate(pipeline_atrasados).to_list()
        resultado_pagos_mes = await Pagamento.aggregate(pipeline_pagos_mes).to_list()
        
        pendentes = resultado_pendentes[0]["total"] if resultado_pendentes else 0
        atrasados = resultado_atrasados[0]["total"] if resultado_atrasados else 0
        pagos_mes = resultado_pagos_mes[0]["total"] if resultado_pagos_mes else 0
    except Exception:
        pendentes = 0
        atrasados = 0
        pagos_mes = 0
    
    return {
        "pendentes": pendentes,
        "atrasados": atrasados,
        "pagos_mes": pagos_mes
    }
