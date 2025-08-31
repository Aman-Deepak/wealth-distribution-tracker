from pydantic import BaseModel
from typing import Any, Dict

class ChartRequest(BaseModel):
    chart_name: str
    params: Dict[str, Any] = {}

class ChartResponse(BaseModel):
    data: Any  # shape depends on chart_type
    meta: Dict[str, Any]  # any extra info

    class Config:
        orm_mode = True
