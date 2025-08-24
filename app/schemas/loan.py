from pydantic import BaseModel
from typing import Optional

class LoanBase(BaseModel):
    financial_year: str
    year: str
    month: str
    day: str
    type: str
    name: str
    interest: float
    loan_amount: Optional[float] = None
    loan_repayment: Optional[float] = None
    cost: float

class LoanCreate(LoanBase):
    pass

class LoanOut(LoanBase):
    id: int

    class Config:
        orm_mode = True