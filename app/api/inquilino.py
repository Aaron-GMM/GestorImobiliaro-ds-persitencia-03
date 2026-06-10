from fastapi import APIRouter, HTTPException, Query
from app.api.common import validar_object_id, extrair_link_id
from app.models.inquilino import Inquilino, InquilinoCreate, InquilinoUpdate, InquilinoResponse
from app.models.pagination import PaginatedResponse
from app.models.proprietario import Proprietario

router = APIRouter(prefix="/inquilinos", tags=["Inquilinos"])


def _inquilino_to_response(inquilino: Inquilino) -> InquilinoResponse:
    proprietario_id = extrair_link_id(inquilino.proprietario)
    return InquilinoResponse(
        id=str(inquilino.id),
        nome=inquilino.nome,
        cpf=inquilino.cpf,
        email=inquilino.email,
        telefone=inquilino.telefone,
        renda_mensal=inquilino.renda_mensal,
        id_proprietario=proprietario_id
    )


async def _buscar_inquilino_ou_404(id_inquilino: str) -> Inquilino:
    _ = validar_object_id(id_inquilino, "ID")
    inquilino = await Inquilino.get(id_inquilino)
    if not inquilino:
        raise HTTPException(status_code=404, detail="Inquilino não encontrado")
    return inquilino


def _garantir_proprietario_do_inquilino(inquilino: Inquilino, id_proprietario: str | None):
    if not id_proprietario:
        return
    owner_id = validar_object_id(id_proprietario, "ID de proprietário")
    inquilino_owner = extrair_link_id(inquilino.proprietario)
    if inquilino_owner != str(owner_id):
        raise HTTPException(status_code=403, detail="Inquilino não pertence ao proprietário informado")


@router.post("/", response_model=InquilinoResponse)
async def criar_inquilino(dados: InquilinoCreate):
    owner_id = validar_object_id(dados.id_proprietario, "ID de proprietário")
    prop = await Proprietario.get(owner_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Proprietário não encontrado")

    novo_inquilino = Inquilino(**dados.model_dump(exclude={"id_proprietario"}), proprietario=prop)
    inquilino = await novo_inquilino.insert()
    return _inquilino_to_response(inquilino)


@router.get("/", response_model=list[InquilinoResponse])
async def listar_inquilinos(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    inquilinos = await Inquilino.find_all().skip(skip).limit(limit).to_list()
    return [_inquilino_to_response(inquilino) for inquilino in inquilinos]


@router.get("/buscar", response_model=list[InquilinoResponse])
async def buscar_inquilinos(
    nome: str | None = Query(None),
    cpf: str | None = Query(None),
    id_proprietario: str | None = Query(None)
):
    filtros = {}

    if nome:
        filtros["nome"] = {"$regex": nome, "$options": "i"}
    if cpf:
        filtros["cpf"] = cpf
    if id_proprietario:
        owner_id = validar_object_id(id_proprietario, "ID de proprietário")
        filtros["proprietario.$id"] = owner_id

    if not filtros:
        return []

    inquilinos = await Inquilino.find(filtros).to_list()
    return [_inquilino_to_response(inquilino) for inquilino in inquilinos]


@router.get("/proprietario/{id_proprietario}", response_model=PaginatedResponse[InquilinoResponse])
async def listar_inquilinos_por_proprietario(
    id_proprietario: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    owner_id = validar_object_id(id_proprietario, "ID de proprietário")
    filtros = {"proprietario.$id": owner_id}
    total = await Inquilino.find(filtros).count()
    inquilinos = await Inquilino.find(filtros).skip(skip).limit(limit).to_list()
    content = [_inquilino_to_response(inquilino) for inquilino in inquilinos]
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


@router.get("/{id}", response_model=InquilinoResponse)
async def obter_inquilino(id: str, id_proprietario: str | None = Query(None)):
    inquilino = await _buscar_inquilino_ou_404(id)
    _garantir_proprietario_do_inquilino(inquilino, id_proprietario)
    return _inquilino_to_response(inquilino)


@router.put("/{id}", response_model=InquilinoResponse)
async def atualizar_inquilino(id: str, dados: InquilinoUpdate, id_proprietario: str | None = Query(None)):
    inquilino = await _buscar_inquilino_ou_404(id)
    _garantir_proprietario_do_inquilino(inquilino, id_proprietario)

    await inquilino.set(dados.model_dump(exclude_unset=True))
    return _inquilino_to_response(inquilino)


@router.delete("/{id}")
async def deletar_inquilino(id: str, id_proprietario: str | None = Query(None)):
    inquilino = await _buscar_inquilino_ou_404(id)
    _garantir_proprietario_do_inquilino(inquilino, id_proprietario)

    await inquilino.delete()
    return {"message": "Inquilino deletado com sucesso"}
