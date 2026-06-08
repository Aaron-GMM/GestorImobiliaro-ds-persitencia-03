from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import init_db
from contextlib import asynccontextmanager
from app.api import proprietario, imovel, inquilino, contrato, dashboard, consultas, pagamento
from app.models.pagamento import Pagamento
from datetime import datetime
import asyncio


async def verificar_pagamentos_atrasados():
    """
    Verifica pagamentos que ultrapassaram a data de vencimento
    e atualiza o status para 'Atrasado'.
    Executa a cada 10 segundos.
    """
    while True:
        print("Verificando pagamentos atrasados...")
        try:
            hoje = datetime.today()
            # Buscar pagamentos pendentes com data de vencimento anterior a hoje
            pagamentos_atrasados = await Pagamento.find({
                "status": "Pendente",
                "data_vencimento": {"$lt": hoje}
            }).to_list()
            
            # Atualizar status para 'Atrasado'
            for pagamento in pagamentos_atrasados:
                await pagamento.set({"status": "Atrasado"})
            
            if pagamentos_atrasados:
                print(f"{len(pagamentos_atrasados)} pagamento(s) atualizado(s) para 'Atrasado'")
        except Exception as e:
            print(f"Erro ao verificar pagamentos atrasados: {e}")
        
        # Aguardar 10 segundos antes da próxima verificação
        await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação, conectando ao banco ao iniciar."""
    await init_db()
    
    # Iniciar tarefa de verificação de pagamentos atrasados
    task = asyncio.create_task(verificar_pagamentos_atrasados())
    
    yield
    
    # Cancelar tarefa ao encerrar a aplicação
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Gestor Imobiliário NoSQL",
    lifespan=lifespan,
    description="API para o Trabalho Prático de Persistência - MongoDB"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite requisições de qualquer origem (no caso, do seu HTML). Em produção, defina o domínio correto.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proprietario.router)
app.include_router(imovel.router)
app.include_router(inquilino.router)
app.include_router(contrato.router)
app.include_router(pagamento.router)
app.include_router(dashboard.router)
app.include_router(consultas.router)