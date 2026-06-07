from fastapi import APIRouter, HTTPException, Query
from app.api.common import validar_object_id, extrair_link_id
from app.models.imovel import Imovel, ImovelCreate, ImovelUpdate, ImovelResponse
from app.models.proprietario import Proprietario

router = APIRouter(prefix="/imoveis", tags=["Imóveis"])



def _imovel_to_response(imovel: Imovel) -> ImovelResponse:
    proprietario_id = extrair_link_id(imovel.proprietario)
    return ImovelResponse(
        id=str(imovel.id),
        apelido_imovel=imovel.apelido_imovel,
        descricao=imovel.descricao,
        endereco=imovel.endereco,
        valor_aluguel_base=imovel.valor_aluguel_base,
        tipo_imovel=imovel.tipo_imovel,
        status=imovel.status,
        id_proprietario=proprietario_id
    )


async def _buscar_imovel_ou_404(id_imovel: str) -> Imovel:
    _ = validar_object_id(id_imovel, "ID")
    imovel = await Imovel.get(id_imovel)
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    return imovel


def _garantir_proprietario_do_imovel(imovel: Imovel, id_proprietario: str | None):
    if not id_proprietario:
        return
    owner_id = validar_object_id(id_proprietario, "ID de proprietário")
    imovel_owner = extrair_link_id(imovel.proprietario)
    if imovel_owner != str(owner_id):
        raise HTTPException(status_code=403, detail="Imóvel não pertence ao proprietário informado")


@router.post("/", response_model=ImovelResponse)
async def criar_imovel(dados: ImovelCreate):
    owner_id = validar_object_id(dados.id_proprietario, "ID de proprietário")
    prop = await Proprietario.get(owner_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Proprietário não encontrado")

    novo_imovel = Imovel(**dados.model_dump(exclude={"id_proprietario"}), proprietario=prop)
    imovel = await novo_imovel.insert()
    return _imovel_to_response(imovel)


@router.get("/", response_model=list[ImovelResponse])
async def listar_imoveis(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    imoveis = await Imovel.find_all().skip(skip).limit(limit).to_list()
    return [_imovel_to_response(imovel) for imovel in imoveis]


@router.get("/buscar", response_model=list[ImovelResponse])
async def buscar_imoveis(
    apelido: str | None = Query(None),
    descricao: str | None = Query(None),
    tipo: str | None = Query(None),
    status: str | None = Query(None),
    id_proprietario: str | None = Query(None)
):
    filtros = {}

    if apelido:
        filtros["apelido_imovel"] = {"$regex": apelido, "$options": "i"}
    if descricao:
        filtros["descricao"] = {"$regex": descricao, "$options": "i"}
    if tipo:
        filtros["tipo_imovel"] = tipo
    if status:
        filtros["status"] = status
    if id_proprietario:
        owner_id = validar_object_id(id_proprietario, "ID de proprietário")
        filtros["proprietario.$id"] = owner_id

    if not filtros:
        return []

    imoveis = await Imovel.find(filtros).to_list()
    return [_imovel_to_response(imovel) for imovel in imoveis]


@router.get("/proprietario/{id_proprietario}", response_model=list[ImovelResponse])
async def listar_imoveis_por_proprietario(id_proprietario: str):
    owner_id = validar_object_id(id_proprietario, "ID de proprietário")
    imoveis = await Imovel.find({"proprietario.$id": owner_id}).to_list()
    return [_imovel_to_response(imovel) for imovel in imoveis]


@router.get("/{id}", response_model=ImovelResponse)
async def obter_imovel(id: str, id_proprietario: str | None = Query(None)):
    imovel = await _buscar_imovel_ou_404(id)
    _garantir_proprietario_do_imovel(imovel, id_proprietario)
    return _imovel_to_response(imovel)


@router.put("/{id}", response_model=ImovelResponse)
async def atualizar_imovel(id: str, dados: ImovelUpdate, id_proprietario: str | None = Query(None)):
    imovel = await _buscar_imovel_ou_404(id)
    _garantir_proprietario_do_imovel(imovel, id_proprietario)

    await imovel.set(dados.model_dump(exclude_unset=True))
    return _imovel_to_response(imovel)


@router.delete("/{id}")
async def deletar_imovel(id: str, id_proprietario: str | None = Query(None)):
    imovel = await _buscar_imovel_ou_404(id)
    _garantir_proprietario_do_imovel(imovel, id_proprietario)
    await imovel.delete()
    return {"message": "Imóvel deletado com sucesso"}
