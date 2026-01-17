import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    MONGODB_URL: str
    DATABASE_NAME: str

    # Isso garante que ele procure o .env na raiz do projeto
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore' # Ignora outras variáveis que possam estar no .env
    )

settings = Settings()