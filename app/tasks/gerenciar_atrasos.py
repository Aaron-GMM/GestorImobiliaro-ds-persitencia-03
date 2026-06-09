from datetime import date
from app.models.pagamento import Pagamento, Encargo
import asyncio

async def verificar_pagamentos_atrasados():
    """
    Verifica pagamentos que ultrapassaram a data de vencimento
    e atualiza o status para 'Atrasado' com cálculo de multa e juros
    baseado na configuração de encargos.
    Executa a cada 10 segundos.
    """
    while True:
        print("Verificando pagamentos atrasados...")
        try:
            hoje = date.today()
            
            encargos = await Encargo.find_all().to_list()
            
            if not encargos:
                pagamentos_atrasados = await Pagamento.find({
                    "status": "Pendente",
                    "data_vencimento": {"$lt": hoje}
                }).to_list()

                for pagamento in pagamentos_atrasados:
                    await pagamento.set({
                        "status": "Atrasado"
                    })

                print(f"Atualizados {len(pagamentos_atrasados)} pagamentos para 'Atrasado'")
                

            for encargo in encargos:
                pagamentos_atrasados = await Pagamento.find({
                    "proprietario": encargo.proprietario,
                    "status": "Pendente",
                    "data_vencimento": {"$lt": hoje}
                }).to_list()

                multa_percentual = encargo.multa_percentual if encargo.multa_percentual else 2.0
                juros_mora = encargo.juros_mora if encargo.juros_mora else 0.33
                tolerancia_dias = encargo.tolerancia_dias if encargo.tolerancia_dias else 1
                valor_minimo_multa = encargo.valor_minimo_multa if encargo.valor_minimo_multa else 5.0
                
                for pagamento in pagamentos_atrasados:
                    dias_atraso = (hoje - pagamento.data_vencimento).days
                    if dias_atraso <= tolerancia_dias:
                        continue
                    
                    valor_multa = pagamento.valor_original * (multa_percentual / 100)
                    if valor_multa < valor_minimo_multa:
                        valor_multa = valor_minimo_multa
                    
                    valor_juros = pagamento.valor_original * (juros_mora / 100) * dias_atraso
                    
                    valor_total = pagamento.valor_original + valor_multa + valor_juros
                    
                    await pagamento.set({
                        "status": "Atrasado",
                        "multa": valor_multa,
                        "juros": valor_juros,
                        "valor_total": valor_total
                    })
            
                if pagamentos_atrasados:
                    print(f"{len(pagamentos_atrasados)} pagamento(s) atualizado(s) para 'Atrasado' com encargos calculados")
        except Exception as e:
            print(f"Erro ao verificar pagamentos atrasados: {e}")
        
        # tempo = 24 * 60 * 60  # 24 horas em segundos
        tempo = 30  # 30 segundos para testes
        await asyncio.sleep(tempo)