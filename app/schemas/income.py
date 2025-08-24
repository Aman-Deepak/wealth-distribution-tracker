from pydantic import BaseModel
from typing import Optional

class IncomeBase(BaseModel):
    financial_year: str
    year: str
    month: str
    day: str
    salary: float
    tax: float

class IncomeCreate(IncomeBase):
    pass

class IncomeOut(IncomeBase):
    id: int

    class Config:
        orm_mode = True