"""
Rotas da API para gerenciamento de Pagamentos.
"""
from beanie import PydanticObjectId
from dns.zonefile import read_rrsets
from fastapi import APIRouter, HTTPException, Query
from app.models.pagamento import Pagamento, PagamentoMetrics, PagamentoResponse, Encargo, ConfigEncargo
from app.models.pagination import PaginatedResponse
from app.models.proprietario import Proprietario

from datetime import date, datetime, timedelta

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])


@router.get("/", response_model=PaginatedResponse[PagamentoResponse])
async def listar_pagamentos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: str | None = Query(None, description="Filtrar por status (Pendente, Atrasado, Pago)"),
    id_contrato: str | None = Query(None, description="Filtrar por contrato"),
    id_proprietario: str | None = Query(None, description="Filtrar por proprietário")
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
    
    if id_proprietario:
        if not PydanticObjectId.is_valid(id_proprietario):
            raise HTTPException(status_code=400, detail="ID de proprietário inválido")
        filtros["proprietario.$id"] = PydanticObjectId(id_proprietario)
    
    # Buscar total de registros
    if filtros:
        total = await Pagamento.find(filtros).count()
    else:
        total = await Pagamento.find_all().count()
    
    # Buscar pagamentos com paginação
    if filtros:
        pagamentos = await Pagamento.find(filtros).skip(skip).limit(limit).to_list()
    else:
        pagamentos = await Pagamento.find_all().skip(skip).limit(limit).to_list()
    
    # Construir resposta com dados relacionados
    content = []
    for pagamento in pagamentos:
        # Buscar contrato relacionado
        contrato = await pagamento.contrato.fetch()
        
        # Buscar inquilino e imóvel através do contrato
        inquilino = await contrato.inquilino.fetch()
        imovel = await contrato.imovel.fetch()
        proprietario = await contrato.proprietario.fetch()

        content.append(PagamentoResponse(
            id=str(pagamento.id),
            imovel=imovel,
            inquilino=inquilino,
            numero_parcela=pagamento.numero_parcela,
            data_vencimento=pagamento.data_vencimento,
            valor_original=pagamento.valor_original,
            multa=pagamento.multa,
            juros=pagamento.juros,
            valor_total=pagamento.valor_total,
            status=pagamento.status,
            proprietario=proprietario,
            data_pagamento=pagamento.data_pagamento,
        ))
    
    # Calcular metadados de paginação
    pages = (total + limit - 1) // limit if total > 0 else 0
    current_page = (skip // limit) + 1 if total > 0 else 1
    
    previous = current_page - 1 if current_page > 1 else None
    next_page = current_page + 1 if current_page < pages else None
    
    return PaginatedResponse(
        previous=previous,
        next=next_page,
        last=pages,
        start=skip,
        content=content,
        total=total,
        pages=pages
    )


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


@router.get("/{id}", response_model=PagamentoResponse)
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
    
    contrato = await pagamento.contrato.fetch()
    
    inquilino = await contrato.inquilino.fetch()
    imovel = await contrato.imovel.fetch()
    
    return PagamentoResponse(
        id=str(pagamento.id),
        imovel=imovel,
        inquilino=inquilino,
        numero_parcela=pagamento.numero_parcela,
        data_vencimento=pagamento.data_vencimento,
        valor_original=pagamento.valor_original,
        multa=pagamento.multa,
        juros=pagamento.juros,
        valor_total=pagamento.valor_total,
        status=pagamento.status,
        proprietario=None,
        data_pagamento=pagamento.data_pagamento,
    )


@router.put("/{id}/confirmar", response_model=Pagamento)
async def confirmar_pagamento(id: str):
    """
    Confirma o pagamento de uma parcela.
    
    Define a data de pagamento para hoje e altera o status para 'Pago'.
    
    Args:
        id: ID do pagamento.
    
    Returns:
        Pagamento confirmado.
    
    Raises:
        HTTPException: Se o ID for inválido ou pagamento não encontrado.
    """
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    pagamento = await Pagamento.get(id)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    
    await pagamento.set({
        "data_pagamento": date.today(),
        "status": "Pago"
    })
    
    return pagamento


@router.post("/configurar-encargos", response_model=Encargo)
async def configurar_encargos(dados: ConfigEncargo):
    """
    Configura os parâmetros de cálculo de encargos para pagamentos em atraso.
    
    Args:
        dados: Configuração dos encargos (multa, juros, tolerância, valor mínimo).
    
    Returns:
        Configuração salva.
    """
    encargo_exists = await Encargo.find_one({"proprietario.$id": dados.id_proprietario})
    
    if encargo_exists:
        raise HTTPException(status_code=400, detail="Já existe uma configuração de encargos para este proprietário")
    
    # Validar ID do proprietário
    proprietario = await Proprietario.get(dados.id_proprietario)
    if not proprietario:
        raise HTTPException(status_code=404, detail="Proprietário não encontrado")
    
    encargo = Encargo(
        multa_percentual=dados.multa_percentual,
        juros_mora=dados.juros_mora,
        tolerancia_dias=dados.tolerancia_dias,
        valor_minimo_multa=dados.valor_minimo_multa,
        proprietario=proprietario
    )

    response = await encargo.insert()
    
    return response

@router.get("/metrics/geral")
async def obter_metricas_pagamentos(id_proprietario: str = Query(None, description="ID do proprietário")):
    """
    Retorna métricas gerais de pagamentos.
    
    Métricas:
    - pendentes: Número de pagamentos pendentes
    - atrasados: Número de pagamentos atrasados
    - pagos_mes: Número de pagamentos realizados no mês atual
    
    Returns:
        Dicionário com as métricas solicitadas.
    """    
    hoje = datetime.now()
    data_inicio = datetime(hoje.year, hoje.month, 1)
    data_fim = data_inicio + timedelta(days=30)

    pipeline_pendentes_match = {"status": "Pendente", "data_vencimento": {"$gte": data_inicio, "$lt": data_fim}}
    pipeline_atrasados_match = {"status": "Atrasado"}
    pipeline_pagos_mes_match = {"status": "Pago", "data_pagamento": {"$gte": data_inicio, "$lt": data_fim}}

    if id_proprietario:
        if not PydanticObjectId.is_valid(id_proprietario):
            raise HTTPException(status_code=400, detail="ID do proprietário inválido")
        
        proprietario = await Proprietario.get(id_proprietario)
        
        if not proprietario:
            raise HTTPException(status_code=404, detail="Proprietário não encontrado")

        pipeline_pendentes_match["proprietario.$id"] = proprietario.id
        pipeline_atrasados_match["proprietario.$id"] = proprietario.id
        pipeline_pagos_mes_match["proprietario.$id"] = proprietario.id
    
    pipeline_pendentes = [
        {"$match": pipeline_pendentes_match},
        {"$count": "total"}
    ]
    
    pipeline_atrasados = [
        {"$match": pipeline_atrasados_match},
        {"$count": "total"}
    ]
    
        
    pipeline_pagos_mes = [
        {"$match": pipeline_pagos_mes_match},
        {"$count": "total"}
    ]
    
    response = PagamentoMetrics(
        pendentes=0,
        atrasados=0,
        pagos_mes=0
    )
    try:
        try:
            resultado_pendentes = await Pagamento.aggregate(pipeline_pendentes).to_list()
            response.pendentes = resultado_pendentes[0]["total"] if resultado_pendentes else 0
        except Exception as error:
            print("Erro ao buscar pagamentos pendentes:", error)
        try:
            resultado_atrasados = await Pagamento.aggregate(pipeline_atrasados).to_list()
            response.atrasados = resultado_atrasados[0]["total"] if resultado_atrasados else 0
        except Exception as error:
            print("Erro ao buscar pagamentos atrasados:", error)
        try:
            resultado_pagos_mes = await Pagamento.aggregate(pipeline_pagos_mes).to_list()
            response.pagos_mes = resultado_pagos_mes[0]["total"] if resultado_pagos_mes else 0
        except Exception as error:
            print("Erro ao buscar pagamentos do mês:", error)
        
    except Exception as error:
        response.pendentes = 0
        response.atrasados = 0
        response.pagos_mes = 0
        print("Erro ao buscar métricas de pagamentos:", error)
    
    return response
