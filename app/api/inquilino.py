"""
Rotas da API para gerenciamento de Inquilinos.
"""
from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query
from app.models.inquilino import Inquilino, InquilinoCreate, InquilinoUpdate

router = APIRouter(prefix="/inquilinos", tags=["Inquilinos"])


@router.post("/", response_model=Inquilino)
async def criar_inquilino(dados: InquilinoCreate):
    """
    Cria um novo inquilino no sistema.
    
    Args:
        dados: Dados do inquilino a ser criado.
    
    Returns:
        Inquilino criado com ID gerado.
    """
    novo_inquilino = Inquilino(**dados.model_dump())
    return await novo_inquilino.insert()


@router.get("/", response_model=list[Inquilino])
async def listar_inquilinos(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    """
    Lista todos os inquilinos com paginação.
    
    Args:
        skip: Número de registros a pular.
        limit: Número máximo de registros a retornar.
    
    Returns:
        Lista de inquilinos.
    """
    return await Inquilino.find_all().skip(skip).limit(limit).to_list()


@router.get("/buscar", response_model=list[Inquilino])
async def buscar_inquilinos(
    nome: str | None = Query(None, description="Busca parcial por nome"),
    cpf: str | None = Query(None, description="Busca por CPF")
):
    """
    Busca inquilinos por nome (parcial, case-insensitive) ou CPF.
    
    Args:
        nome: Nome para busca parcial.
        cpf: CPF para busca exata.
    
    Returns:
        Lista de inquilinos encontrados.
    """
    if nome:
        return await Inquilino.find(
            {"nome": {"$regex": nome, "$options": "i"}}
        ).to_list()
    if cpf:
        return await Inquilino.find({"cpf": cpf}).to_list()
    return []


@router.get("/{id}", response_model=Inquilino)
async def obter_inquilino(id: str):
    """
    Obtém um inquilino pelo ID.
    
    Args:
        id: ID do inquilino.
    
    Returns:
        Inquilino encontrado.
    
    Raises:
        HTTPException: Se o ID for inválido ou inquilino não encontrado.
    """
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    inquilino = await Inquilino.get(id)
    if not inquilino:
        raise HTTPException(status_code=404, detail="Inquilino não encontrado")
    return inquilino


@router.put("/{id}", response_model=Inquilino)
async def atualizar_inquilino(id: str, dados: InquilinoUpdate):
    """
    Atualiza um inquilino existente.
    
    Args:
        id: ID do inquilino.
        dados: Dados a serem atualizados.
    
    Returns:
        Inquilino atualizado.
    
    Raises:
        HTTPException: Se o ID for inválido ou inquilino não encontrado.
    """
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    inquilino = await Inquilino.get(id)
    if not inquilino:
        raise HTTPException(status_code=404, detail="Inquilino não encontrado")
    
    await inquilino.set(dados.model_dump(exclude_unset=True))
    return inquilino


@router.delete("/{id}")
async def deletar_inquilino(id: str):
    """
    Remove um inquilino do sistema.
    
    Args:
        id: ID do inquilino.
    
    Returns:
        Mensagem de confirmação.
    
    Raises:
        HTTPException: Se o ID for inválido ou inquilino não encontrado.
    """
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    inquilino = await Inquilino.get(id)
    if not inquilino:
        raise HTTPException(status_code=404, detail="Inquilino não encontrado")
    
    await inquilino.delete()
    return {"message": "Inquilino deletado com sucesso"}
