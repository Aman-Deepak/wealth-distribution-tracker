from pydantic import BaseModel
from typing import Optional

class InvestBase(BaseModel):
    financial_year: str
    year: str
    month: str
    day: str
    type: str
    folio_number: Optional[str] = None
    name: str
    type_of_order: str
    units: Optional[float] = None
    nav: Optional[float] = None
    cost: float

class InvestCreate(InvestBase):
    pass

class InvestOut(InvestBase):
    id: int

    class Config:
        orm_mode = True