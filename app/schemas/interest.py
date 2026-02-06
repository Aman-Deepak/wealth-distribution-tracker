from pydantic import BaseModel
from typing import Optional

class InterestBase(BaseModel):
    financial_year: str
    year: str
    month: str
    day: str
    type: str
    name: str
    cost_in: float
    cost_in: float
    

class InterestCreate(InterestBase):
    pass

class InterestOut(InterestBase):
    id: int

    class Config:
        orm_mode = True