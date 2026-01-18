from fastapi import FastAPI
from app.database.database import init_db
from contextlib import asynccontextmanager
from app.api import proprietario, imovel, inquilino, contrato, dashboard, consultas

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

app.include_router(proprietario.router)
app.include_router(imovel.router)
app.include_router(inquilino.router)
app.include_router(contrato.router)
app.include_router(dashboard.router)
app.include_router(consultas.router)