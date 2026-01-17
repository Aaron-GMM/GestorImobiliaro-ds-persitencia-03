from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query
from app.models.imovel import Imovel, ImovelCreate, ImovelUpdate
from app.models.proprietario import Proprietario

router = APIRouter(prefix="/imoveis", tags=["Imóveis"])


@router.post("/", response_model=Imovel)
async def criar_imovel(dados: ImovelCreate):
    """
    Cria um novo imóvel no sistema.
    
    Args:
        dados: Dados do imóvel a ser criado, incluindo ID do proprietário.
    
    Returns:
        Imóvel criado com ID gerado.
    
    Raises:
        HTTPException: Se o ID do proprietário for inválido ou não encontrado.
    """
    if not PydanticObjectId.is_valid(dados.id_proprietario):
        raise HTTPException(status_code=400, detail="ID de proprietário inválido")

    prop = await Proprietario.get(dados.id_proprietario)
    if not prop:
        raise HTTPException(status_code=404, detail="Proprietário não encontrado")

    novo_imovel = Imovel(
        **dados.model_dump(exclude={"id_proprietario"}),
        proprietario=prop
    )

    return await novo_imovel.insert()


@router.get("/", response_model=list[Imovel])
async def listar_imoveis(skip: int = Query(0), limit: int = Query(10)):
    """Lista todos os imóveis com paginação."""
    return await Imovel.find_all().skip(skip).limit(limit).to_list()


@router.get("/buscar", response_model=list[Imovel])
async def buscar_imoveis(
    apelido: str | None = Query(None, description="Busca parcial por apelido (case-insensitive)"),
    descricao: str | None = Query(None, description="Busca parcial na descrição (case-insensitive)"),
    tipo: str | None = Query(None, description="Filtrar por tipo de imóvel"),
    status: str | None = Query(None, description="Filtrar por status (Disponivel, Alugado)")
):
    """
    Busca imóveis por apelido, descrição, tipo ou status.
    Implementa busca por texto parcial e case-insensitive.
    
    Args:
        apelido: Texto para busca parcial no apelido.
        descricao: Texto para busca parcial na descrição.
        tipo: Tipo de imóvel (Casa, Apartamento, etc).
        status: Status do imóvel (Disponivel, Alugado).
    
    Returns:
        Lista de imóveis que correspondem aos critérios.
    """
    filtros = {}
    
    if apelido:
        filtros["apelido_imovel"] = {"$regex": apelido, "$options": "i"}
    if descricao:
        filtros["descricao"] = {"$regex": descricao, "$options": "i"}
    if tipo:
        filtros["tipo_imovel"] = tipo
    if status:
        filtros["status"] = status
    
    if not filtros:
        return []
    
    return await Imovel.find(filtros).to_list()


@router.get("/proprietario/{id_proprietario}", response_model=list[Imovel])
async def listar_imoveis_por_proprietario(id_proprietario: str):
    """
    Lista todos os imóveis de um proprietário específico.
    
    Args:
        id_proprietario: ID do proprietário.
    
    Returns:
        Lista de imóveis do proprietário.
    
    Raises:
        HTTPException: Se o ID for inválido.
    """
    if not PydanticObjectId.is_valid(id_proprietario):
        raise HTTPException(status_code=400, detail="ID de proprietário inválido")
    
    return await Imovel.find(
        {"proprietario.$id": PydanticObjectId(id_proprietario)}
    ).to_list()


@router.get("/{id}", response_model=Imovel)
async def obter_imovel(id: str):
    """
    Obtém um imóvel pelo ID.
    
    Args:
        id: ID do imóvel.
    
    Returns:
        Imóvel encontrado.
    
    Raises:
        HTTPException: Se o ID for inválido ou imóvel não encontrado.
    """
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")

    imovel = await Imovel.get(id)
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    return imovel


@router.put("/{id}", response_model=Imovel)
async def atualizar_imovel(id: str, dados: ImovelUpdate):
    """
    Atualiza um imóvel existente.
    
    Args:
        id: ID do imóvel.
        dados: Dados a serem atualizados.
    
    Returns:
        Imóvel atualizado.
    
    Raises:
        HTTPException: Se o ID for inválido ou imóvel não encontrado.
    """
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")

    imovel = await Imovel.get(id)
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    await imovel.set(dados.model_dump(exclude_unset=True))
    return imovel


@router.delete("/{id}")
async def deletar_imovel(id: str):
    """
    Remove um imóvel do sistema.
    
    Args:
        id: ID do imóvel.
    
    Returns:
        Mensagem de confirmação.
    
    Raises:
        HTTPException: Se o ID for inválido ou imóvel não encontrado.
    """
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")

    imovel = await Imovel.get(id)
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    await imovel.delete()
    return {"message": "Imóvel deletado com sucesso"}