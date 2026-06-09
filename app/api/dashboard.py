from fastapi import APIRouter
from app.models.imovel import Imovel
from app.models.contrato import Contrato
from app.models.proprietario import Proprietario
from app.models.inquilino import Inquilino
from app.models.statistics import Statistics, RecentActivity
from app.models.pagamento import Pagamento
from fastapi import Query, HTTPException
from beanie import PydanticObjectId
from datetime import datetime, timedelta

router = APIRouter(prefix="/dashboard", tags=["Dashboard e Agregações"])


@router.get("/estatisticas", response_model=Statistics)
async def get_estatisticas(id_proprietario: str = Query(None, description="ID do proprietário")):
    pipeline_imoveis = [
        {"$match": {
            "status": {
                "$in": ["Alugado", "Disponivel"]
            }
        }},
        {"$group": {
            "_id": "$status",
            "total": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "status": "$_id",
            "total": 1
        }}
    ]

    primeiro_dia = datetime.now().replace(day=1, month=7)
    ultimo_dia = primeiro_dia.replace(month=primeiro_dia.month)

    pipeline_pagamentos_pendentes = [
        {"$match": {
            "status": "Pendente",
            "data_vencimento": {"$gte": primeiro_dia, "$lt": ultimo_dia}
        }},
        {"$count": "total"}
    ]

    if id_proprietario:
        if not PydanticObjectId.is_valid(id_proprietario):
            raise HTTPException(status_code=400, detail="ID do proprietário inválido")
        
        proprietario = await Proprietario.get(PydanticObjectId(id_proprietario))

        if not proprietario:
            raise HTTPException(status_code=404, detail="Proprietário não encontrado")

        pipeline_imoveis[0]["$match"]["proprietario.$id"] = proprietario.id
        pipeline_pagamentos_pendentes[0]["$match"]["proprietario.$id"] = proprietario.id


    imoveis = await Imovel.aggregate(pipeline_imoveis).to_list()

    pagamentos = await Pagamento.aggregate(pipeline_pagamentos_pendentes).to_list()

    return Statistics(
        imoveis_alugados=imoveis[0]["total"] if imoveis[0] else 0,
        imoveis_disponiveis=imoveis[1]["total"] if imoveis[1] else 0,
        pagamentos_pendentes=pagamentos[0]["total"] if pagamentos else 0
    )
   
@router.get("/atividade-recente")
async def get_atividade_recente(id_proprietario: str = Query(None, description="ID do proprietário")):
    filtro_base = {}
    if id_proprietario:
        if not PydanticObjectId.is_valid(id_proprietario):
            raise HTTPException(status_code=400, detail="ID do proprietário inválido")

        proprietario = await Proprietario.get(PydanticObjectId(id_proprietario))

        if not proprietario:
            raise HTTPException(status_code=404, detail="Proprietário não encontrado")

        filtro_base["proprietario.$id"] = proprietario.id
    
    inquilino = await Inquilino.find_one(filtro_base, sort={"_id": -1})
    contrato = await Contrato.find_one(filtro_base, sort={"_id": -1})
    imovel_alugado = await contrato.imovel.fetch() if contrato else None
    
    filtro_base["status"] = "Disponivel"
    imovel_disponivel = await Imovel.find_one(filtro_base, sort={"_id": -1})
    
    return RecentActivity(
        imovel_alugado=imovel_alugado.apelido_imovel if imovel_alugado else "N/A",
        inquilino=inquilino.nome if inquilino else "N/A",
        imovel_disponivel=imovel_disponivel.apelido_imovel if imovel_disponivel else "N/A"
    )

@router.get("/completo")
async def get_dashboard_completo():
    proprietarios = await Proprietario.find_all().to_list()
    relatorio = []
    
    for prop in proprietarios:
        imoveis = await Imovel.find(Imovel.proprietario.id == prop.id).to_list()
        dados_prop = {
            "proprietario": prop.nome,
            "email": prop.email,
            "total_imoveis": len(imoveis),
            "imoveis": []
        }
        
        for imovel in imoveis:
            contrato = await Contrato.find_one(
                Contrato.imovel.id == imovel.id,
                Contrato.status == "Ativo",
                fetch_links=True 
            )
            
            info_imovel = {
                "apelido": imovel.apelido_imovel,
                "tipo": imovel.tipo_imovel,
                "endereco": imovel.endereco,
                "status": "Alugado" if contrato else "Disponivel",
                "valor_atual": contrato.valor_aluguel if contrato else imovel.valor_aluguel_base
            }

            if contrato:
                info_imovel["inquilino"] = contrato.inquilino.nome if contrato.inquilino else "N/A"
                info_imovel["vencimento"] = contrato.data_fim
            
            dados_prop["imoveis"].append(info_imovel)
        relatorio.append(dados_prop)

    return relatorio