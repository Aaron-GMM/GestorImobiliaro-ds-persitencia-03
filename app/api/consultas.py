from fastapi import APIRouter, Query
from typing import List
from app.models.contrato import Contrato
from app.models.imovel import Imovel

router = APIRouter(prefix="/consultas", tags=["Consultas Avançadas"])

@router.get("/contratos-por-vencimento")
async def filtrar_contratos_vencimento(
    ano: int,
    mes: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    skip = (page - 1) * page_size
    contratos = await Contrato.find(
        {
            "$expr": {
                "$and": [
                    {"$eq": [{"$year": "$data_fim"}, ano]},
                    {"$eq": [{"$month": "$data_fim"}, mes]}
                ]
            }
        },
        fetch_links=True
    ).skip(skip).limit(page_size).to_list()
    return contratos

@router.get("/imoveis-busca-texto")
async def busca_textual_imoveis(
    termo: str,
    ordenar_por: str = Query("valor_aluguel_base", enum=["valor_aluguel_base", "apelido_imovel"]),
    direcao: str = Query("asc", enum=["asc", "desc"]),
    page: int = 1,
    page_size: int = 10
):
    skip = (page - 1) * page_size
    query_filter = {
        "$or": [
            {"apelido_imovel": {"$regex": termo, "$options": "i"}},
            {"endereco": {"$regex": termo, "$options": "i"}}
        ]
    }
    sort_dir = 1 if direcao == "asc" else -1
    
    imoveis = await Imovel.find(query_filter)\
        .sort((ordenar_por, sort_dir))\
        .skip(skip).limit(page_size).to_list()
    return imoveis