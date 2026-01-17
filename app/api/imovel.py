from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query
from app.models.imovel import Imovel, ImovelCreate, ImovelUpdate
from app.models.proprietario import Proprietario

router = APIRouter(prefix="/imoveis", tags=["Imóveis"])


@router.post("/", response_model=Imovel)
async def criar_imovel(dados: ImovelCreate):
    # Lógica de validação continua aqui (Regra de Negócio/Controller)
    if not PydanticObjectId.is_valid(dados.id_proprietario):
        raise HTTPException(status_code=400, detail="ID de proprietário inválido")

    prop = await Proprietario.get(dados.id_proprietario)
    if not prop:
        raise HTTPException(status_code=404, detail="Proprietário não encontrado")

    # Conversão Schema -> Document
    novo_imovel = Imovel(
        **dados.model_dump(exclude={"id_proprietario"}),
        proprietario=prop
    )

    return await novo_imovel.insert()


@router.get("/", response_model=list[Imovel])
async def listar_imoveis(skip: int = Query(0), limit: int = Query(10)):
    return await Imovel.find_all().skip(skip).limit(limit).fetch_links().to_list()


@router.get("/{id}", response_model=Imovel)
async def obter_imovel(id: str):
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")

    imovel = await Imovel.get(id, fetch_links=True)
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    return imovel


@router.put("/{id}", response_model=Imovel)
async def atualizar_imovel(id: str, dados: ImovelUpdate):
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")

    imovel = await Imovel.get(id)
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    await imovel.set(dados.model_dump(exclude_unset=True))
    return imovel


@router.delete("/{id}")
async def deletar_imovel(id: str):
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")

    imovel = await Imovel.get(id)
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    await imovel.delete()
    return {"message": "Imóvel deletado com sucesso"}