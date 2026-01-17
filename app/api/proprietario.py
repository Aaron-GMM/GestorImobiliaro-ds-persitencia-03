from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query
from app.models.proprietario import Proprietario, ProprietarioCreate, ProprietarioUpdate

router = APIRouter(prefix="/proprietarios", tags=["Proprietários"])


@router.post("/", response_model=Proprietario)
async def criar_proprietario(dados: ProprietarioCreate):
    # Como o Create e o Document tem os mesmos campos, podemos converter direto
    novo_prop = Proprietario(**dados.model_dump())
    return await novo_prop.insert()


@router.get("/", response_model=list[Proprietario])
async def listar_proprietarios(skip: int = Query(0), limit: int = Query(10)):
    return await Proprietario.find_all().skip(skip).limit(limit).to_list()


@router.get("/{id}", response_model=Proprietario)
async def obter_proprietario(id: str):
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    prop = await Proprietario.get(id)
    if not prop:
        raise HTTPException(status_code=404, detail="Proprietário não encontrado")
    return prop


@router.put("/{id}", response_model=Proprietario)
async def atualizar_proprietario(id: str, dados: ProprietarioUpdate):
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")

    prop = await Proprietario.get(id)
    if not prop:
        raise HTTPException(status_code=404, detail="Proprietário não encontrado")

    await prop.set(dados.model_dump(exclude_unset=True))
    return prop


@router.delete("/{id}")
async def deletar_proprietario(id: str):
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")

    prop = await Proprietario.get(id)
    if not prop:
        raise HTTPException(status_code=404, detail="Proprietário não encontrado")

    await prop.delete()
    return {"message": "Proprietário deletado com sucesso"}