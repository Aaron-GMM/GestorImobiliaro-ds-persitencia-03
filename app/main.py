from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import init_db
from contextlib import asynccontextmanager
from app.api import proprietario, imovel, inquilino, contrato, dashboard, consultas, pagamento

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação, conectando ao banco ao iniciar."""
    await init_db()
    yield

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