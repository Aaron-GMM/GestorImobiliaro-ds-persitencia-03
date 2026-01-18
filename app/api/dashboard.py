from fastapi import APIRouter
from app.models.imovel import Imovel
from app.models.contrato import Contrato
from app.models.proprietario import Proprietario
from app.models.inquilino import Inquilino

router = APIRouter(prefix="/dashboard", tags=["Dashboard e Agregações"])


@router.get("/estatisticas")
async def get_estatisticas():
    """
    Retorna estatísticas agregadas usando Aggregation Pipeline do MongoDB via Beanie.
    Requisito: e) Agregações e contagens utilizando aggregation pipeline
    """

    # 1. Agregação: Quantidade de imóveis por tipo
    # Sintaxe nativa do Beanie: Model.aggregate(pipeline).to_list()
    pipeline_imoveis = [
        {"$group": {"_id": "$tipo_imovel", "quantidade": {"$sum": 1}}}
    ]

    # Com o motor<3.7, o 'await' aqui volta a funcionar corretamente
    qtd_por_tipo = await Imovel.aggregate(pipeline_imoveis).to_list()

    # 2. Agregação: Receita Total (Soma de valor_aluguel onde status='Ativo')
    pipeline_receita = [
        {"$match": {"status": "Ativo"}},
        {"$group": {"_id": None, "receita_total": {"$sum": "$valor_aluguel"}}}
    ]

    resultado_receita = await Contrato.aggregate(pipeline_receita).to_list()

    # Tratamento para caso não haja contratos (lista vazia)
    receita_total = resultado_receita[0]["receita_total"] if resultado_receita else 0.0

    return {
        "imoveis_por_categoria": qtd_por_tipo,
        "receita_mensal_atual": receita_total
    }
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