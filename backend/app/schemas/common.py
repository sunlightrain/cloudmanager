from typing import Any, Optional
from pydantic import BaseModel


class ResponseModel(BaseModel):
    code: int = 200
    message: str = "Success"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    code: int = 400
    message: str
    detail: Optional[Any] = None


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 20
