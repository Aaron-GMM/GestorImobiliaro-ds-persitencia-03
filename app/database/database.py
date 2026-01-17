from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.models.proprietario import Proprietario
from app.models.imovel import Imovel
from app.models.inquilino import Inquilino
from app.models.contrato import Contrato


async def init_db():
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        await init_beanie(
            database=client[settings.DATABASE_NAME],
            document_models=[Proprietario, Imovel, Inquilino, Contrato],

        )
        print("Conexão com MongoDB estabelecida com sucesso!")
    except Exception as e:
        print(f"FALHA NA CONEXÃO COM O BANCO: {e}")
