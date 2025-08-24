from pydantic import BaseModel

class ExpenseBase(BaseModel):
    financial_year: str
    year: str
    month: str
    day: str
    type: str
    category: str
    cost: float

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseOut(ExpenseBase):
    id: int

    class Config:
        orm_mode = True