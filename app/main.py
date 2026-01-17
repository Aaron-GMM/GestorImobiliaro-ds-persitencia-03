from fastapi import FastAPI
from app.database.database import init_db
from contextlib import asynccontextmanager
from app.api import proprietario, imovel# Certifique-se de importar suas rotas

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conecta ao banco ao iniciar a API
    await init_db()
    yield

app = FastAPI(
    title="Gestor Imobiliário NoSQL",
    lifespan=lifespan,
    description="API para o Trabalho Prático de Persistência - MongoDB"
)

# Incluindo as rotas que você criou no Ponto 1
app.include_router(proprietario.router)
app.include_router(imovel.router)