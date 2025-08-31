from pydantic import BaseModel
from typing import Any, Dict, List

class TableRequest(BaseModel):
    table_name: str
    params: Dict[str, Any] = {}

class TableResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]

    class Config:
        orm_mode = True
