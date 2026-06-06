from beanie import PydanticObjectId
from fastapi import HTTPException


def validar_object_id(valor: str, campo: str) -> PydanticObjectId:
    if not PydanticObjectId.is_valid(valor):
        raise HTTPException(status_code=400, detail=f"{campo} inválido")
    return PydanticObjectId(valor)


def extrair_link_id(valor) -> str:
    if not valor:
        return ""

    if hasattr(valor, "id") and valor.id:
        return str(valor.id)

    ref = getattr(valor, "ref", None)
    if ref and getattr(ref, "id", None):
        return str(ref.id)

    return ""