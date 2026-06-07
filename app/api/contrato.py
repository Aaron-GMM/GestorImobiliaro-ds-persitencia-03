"""
Rotas da API para gerenciamento de Contratos.
Implementa a relação Muitos-para-Muitos entre Inquilino e Imóvel.
"""
from datetime import date, timedelta
from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query
from app.models.contrato import Contrato, ContratoCreate, ContratoMetrics, ContratoUpdate
from app.models.inquilino import Inquilino
from app.models.imovel import Imovel
from app.models.pagamento import Pagamento

router = APIRouter(prefix="/contratos", tags=["Contratos"])


async def _gerar_pagamentos_contrato(contrato: Contrato):
    """
    Gera automaticamente todos os pagamentos mensais de um contrato.
    
    Args:
        contrato: Contrato criado.
    """
    # Calcular número de meses entre as datas
    inicio = contrato.data_inicio
    fim = contrato.data_fim
    
    # Calcular diferença em meses
    diff_months = (fim.year - inicio.year) * 12 + (fim.month - inicio.month) + 1
    
    # Gerar pagamentos para cada mês
    pagamentos = []
    for i in range(diff_months):
        # Calcular data de vencimento para este mês
        data_vencimento = date(
            inicio.year + (inicio.month + i - 1) // 12,
            (inicio.month + i - 1) % 12 + 1,
            contrato.dia_vencimento
        )
        
        # Formatar número da parcela
        numero_parcela = f"{i + 1:02d}/{diff_months:02d}"
        
        # Criar pagamento
        pagamento = Pagamento(
            contrato=contrato,
            numero_parcela=numero_parcela,
            data_vencimento=data_vencimento,
            valor_original=contrato.valor_aluguel,
            multa=0.0,
            juros=0.0,
            valor_total=contrato.valor_aluguel,
            status="Pendente"
        )
        pagamentos.append(pagamento)
    
    # Inserir todos os pagamentos em lote
    if pagamentos:
        await Pagamento.insert_many(pagamentos)


@router.post("/", response_model=Contrato)
async def criar_contrato(dados: ContratoCreate):
    """
    Cria um novo contrato de aluguel.
    
    Regras de negócio:
    - O inquilino deve existir
    - O imóvel deve existir
    - O imóvel não pode estar com status "Alugado" (já possui contrato ativo)
    
    Args:
        dados: Dados do contrato a ser criado.
    
    Returns:
        Contrato criado com ID gerado.
    
    Raises:
        HTTPException: Se inquilino/imóvel não existir ou imóvel já alugado.
    """
    # Validar ID do inquilino
    if not PydanticObjectId.is_valid(dados.id_inquilino):
        raise HTTPException(status_code=400, detail="ID de inquilino inválido")
    
    # Validar ID do imóvel
    if not PydanticObjectId.is_valid(dados.id_imovel):
        raise HTTPException(status_code=400, detail="ID de imóvel inválido")
    
    # Buscar inquilino
    inquilino = await Inquilino.get(dados.id_inquilino)
    if not inquilino:
        raise HTTPException(status_code=404, detail="Inquilino não encontrado")
    
    # Buscar imóvel
    imovel = await Imovel.get(dados.id_imovel)
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    
    # Verificar se o imóvel já está alugado
    if imovel.status == "Alugado":
        raise HTTPException(
            status_code=400, 
            detail="Este imóvel já está alugado. Encerre o contrato atual antes de criar um novo."
        )
    
    # Validar datas
    if dados.data_fim <= dados.data_inicio:
        raise HTTPException(
            status_code=400, 
            detail="A data de fim deve ser posterior à data de início"
        )
    
    # Criar contrato
    novo_contrato = Contrato(
        inquilino=inquilino,
        imovel=imovel,
        data_inicio=dados.data_inicio,
        data_fim=dados.data_fim,
        valor_aluguel=dados.valor_aluguel,
        dia_vencimento=dados.dia_vencimento,
        status="Ativo"
    )
    
    # Inserir contrato
    contrato_inserido = await novo_contrato.insert()
    
    # Atualizar status do imóvel para "Alugado"
    await imovel.set({"status": "Alugado"})
    
    # Gerar pagamentos mensais automaticamente
    await _gerar_pagamentos_contrato(contrato_inserido)
    
    return contrato_inserido


@router.get("/", response_model=list[Contrato])
async def listar_contratos(
    skip: int = Query(0, ge=0), 
    limit: int = Query(10, ge=1, le=100),
    status: str | None = Query(None, description="Filtrar por status (Ativo, Encerrado, Cancelado)")
):
    """
    Lista todos os contratos com paginação e filtro opcional por status.
    
    Args:
        skip: Número de registros a pular.
        limit: Número máximo de registros a retornar.
        status: Filtrar por status do contrato.
    
    Returns:
        Lista de contratos.
    """
    if status:
        contratos = await Contrato.find(
            {"status": status}
        ).skip(skip).limit(limit).to_list()
    else:
        contratos = await Contrato.find_all().skip(skip).limit(limit).to_list()
    
    return contratos


@router.get("/inquilino/{id_inquilino}", response_model=list[Contrato])
async def listar_contratos_por_inquilino(id_inquilino: str):
    """
    Lista todos os contratos de um inquilino específico.
    
    Args:
        id_inquilino: ID do inquilino.
    
    Returns:
        Lista de contratos do inquilino.
    
    Raises:
        HTTPException: Se o ID for inválido.
    """
    if not PydanticObjectId.is_valid(id_inquilino):
        raise HTTPException(status_code=400, detail="ID de inquilino inválido")
    
    return await Contrato.find(
        {"inquilino.$id": PydanticObjectId(id_inquilino)}
    ).to_list()


@router.get("/imovel/{id_imovel}", response_model=list[Contrato])
async def listar_contratos_por_imovel(id_imovel: str):
    """
    Lista todos os contratos de um imóvel específico.
    
    Args:
        id_imovel: ID do imóvel.
    
    Returns:
        Lista de contratos do imóvel.
    
    Raises:
        HTTPException: Se o ID for inválido.
    """
    if not PydanticObjectId.is_valid(id_imovel):
        raise HTTPException(status_code=400, detail="ID de imóvel inválido")
    
    return await Contrato.find(
        {"imovel.$id": PydanticObjectId(id_imovel)}
    ).to_list()


@router.get("/{id}", response_model=Contrato)
async def obter_contrato(id: str):
    """
    Obtém um contrato pelo ID.
    
    Args:
        id: ID do contrato.
    
    Returns:
        Contrato encontrado.
    
    Raises:
        HTTPException: Se o ID for inválido ou contrato não encontrado.
    """
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    contrato = await Contrato.get(id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    return contrato


@router.put("/{id}", response_model=Contrato)
async def atualizar_contrato(id: str, dados: ContratoUpdate):
    """
    Atualiza um contrato existente.
    
    Args:
        id: ID do contrato.
        dados: Dados a serem atualizados.
    
    Returns:
        Contrato atualizado.
    
    Raises:
        HTTPException: Se o ID for inválido ou contrato não encontrado.
    """
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    contrato = await Contrato.get(id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    
    dados_atualizacao = dados.model_dump(exclude_unset=True)
    
    # Se estiver encerrando ou cancelando o contrato, liberar o imóvel
    if dados.status in ["Encerrado", "Cancelado"] and contrato.status == "Ativo":
        imovel_id = contrato.imovel.ref.id if hasattr(contrato.imovel, 'ref') else contrato.imovel.id
        imovel = await Imovel.get(imovel_id)
        if imovel:
            await imovel.set({"status": "Disponivel"})
    
    await contrato.set(dados_atualizacao)
    return contrato


@router.delete("/{id}")
async def deletar_contrato(id: str):
    """
    Remove um contrato do sistema.
    Se o contrato estiver ativo, libera o imóvel.
    
    Args:
        id: ID do contrato.
    
    Returns:
        Mensagem de confirmação.
    
    Raises:
        HTTPException: Se o ID for inválido ou contrato não encontrado.
    """
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    contrato = await Contrato.get(id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    
    # Se contrato ativo, liberar o imóvel
    if contrato.status == "Ativo":
        imovel_id = contrato.imovel.ref.id if hasattr(contrato.imovel, 'ref') else contrato.imovel.id
        imovel = await Imovel.get(imovel_id)
        if imovel:
            await imovel.set({"status": "Disponivel"})
    
    await contrato.delete()
    return {"message": "Contrato deletado com sucesso"}


@router.post("/{id}/encerrar", response_model=Contrato)
async def encerrar_contrato(id: str):
    """
    Encerra um contrato ativo e libera o imóvel.
    
    Args:
        id: ID do contrato.
    
    Returns:
        Contrato encerrado.
    
    Raises:
        HTTPException: Se o ID for inválido, contrato não encontrado ou já encerrado.
    """
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    contrato = await Contrato.get(id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    
    if contrato.status != "Ativo":
        raise HTTPException(status_code=400, detail="Este contrato já foi encerrado ou cancelado")
    
    # Liberar o imóvel
    imovel_id = contrato.imovel.ref.id if hasattr(contrato.imovel, 'ref') else contrato.imovel.id
    imovel = await Imovel.get(imovel_id)
    if imovel:
        await imovel.set({"status": "Disponivel"})
    
    # Encerrar contrato
    await contrato.set({"status": "Encerrado"})
    return contrato


@router.get("/metrics/geral", response_model=ContratoMetrics)
async def obter_metricas_gerais():
    """
    Retorna métricas gerais de contratos e imóveis.
    
    Métricas:
    - contrato_ativo: Número de contratos ativos e não vencidos
    - contrato_vencendo: Número de contratos vencendo nos próximos 30 dias
    - imovel_disponivel: Número de imóveis disponíveis para locação
    
    Returns:
        Dicionário com as métricas solicitadas.
    """
    hoje = date.today()
    vencendo = (hoje + timedelta(days=30)).strftime("%Y-%m-%d")
        
    pipeline_vigencia = [
        {"$match": {
            "status": "Ativo"
        }},
        {"$count": "total"}
    ]
    
    pipeline_vencendo = [
        {"$match": {
            "status": "Ativo",
            "data_fim": {"$lte": vencendo}
        }},
        {"$count": "total"}
    ]
 
    pipeline_disponiveis = [
        {"$match": {"status": "Disponivel"}},
        {"$count": "total"}
    ]
    
    response = ContratoMetrics(
        contratos_ativos=0,
        contratos_vencendo=0,
        imoveis_disponiveis=0
    )
    
    try:
        try:
            resultado_vigencia = await Contrato.aggregate(pipeline_vigencia).to_list()
            response.contratos_ativos = resultado_vigencia[0]["total"] if resultado_vigencia else 0
        except Exception as e:
            print(f"Erro ao buscar contratos ativos: {e}")
        
        try:
            resultado_vencendo = await Contrato.aggregate(pipeline_vencendo).to_list()
            response.contratos_vencendo = resultado_vencendo[0]["total"] if resultado_vencendo else 0
        except Exception as e:
            print(f"Erro ao buscar contratos vencendo: {e}")
        
        try:
            resultado_disponiveis = await Imovel.aggregate(pipeline_disponiveis).to_list()
            response.imoveis_disponiveis = resultado_disponiveis[0]["total"] if resultado_disponiveis else 0
        except Exception as e:
            print(f"Erro ao buscar imóveis disponíveis: {e}")
            
    except Exception as e:
        print(f"Erro geral ao buscar métricas: {e}")

    return response
