from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Schema para resposta paginada."""
    previous: Optional[int] = Field(description="Página anterior")
    next: Optional[int] = Field(description="Próxima página")
    last: int = Field(description="Última página")
    start: int = Field(description="Índice inicial")
    content: List[T] = Field(description="Conteúdo da página")
    total: int = Field(description="Total de registros")
    pages: int = Field(description="Total de páginas")
