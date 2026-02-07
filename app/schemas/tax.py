from pydantic import BaseModel
from typing import Optional

class TaxBase(BaseModel):
    financial_year: str
    year: str
    month: str
    day: str
    name: str
    type: str
    amount: Optional[float] = None
    refund: Optional[float] = None

class TaxCreate(TaxBase):
    pass

class TaxOut(TaxBase):
    id: int

    class Config:
        orm_mode = True