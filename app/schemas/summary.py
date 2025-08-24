from pydantic import BaseModel
from typing import Optional


# -----------------------------
# Savings Schemas
# -----------------------------
class SavingBase(BaseModel):
    TYPE: Optional[str] = None
    NAME: str
    T_BUY: Optional[float] = 0.0
    T_SELL: Optional[float] = 0.0
    PROFIT_BOOKED: Optional[float] = 0.0
    CURRENT_INVESTED: Optional[float] = 0.0
    CURRENT_VALUE: Optional[float] = 0.0
    PROFIT_LOSS: Optional[float] = 0.0
    RETURN_PERCENTAGE: Optional[float] = 0.0


class SavingCreate(SavingBase):
    pass


class SavingOut(SavingBase):
    class Config:
        orm_mode = True

from pydantic import BaseModel, Field
from typing import Optional


# -----------------------------
# Monthly Distribution Schemas
# -----------------------------
class MonthlyDistributionBase(BaseModel):
    FISCAL_YEAR: Optional[str] = None
    YEAR: Optional[str] = None
    MONTH: Optional[str] = None
    INCOME: Optional[float] = 0.0
    INV_BUY: Optional[float] = 0.0
    INV_SELL: Optional[float] = 0.0
    EXPENSE: Optional[float] = 0.0
    BANK: Optional[float] = 0.0
    TAX: Optional[float] = 0.0
    INTEREST_IN: Optional[float] = 0.0
    INTEREST_OUT: Optional[float] = 0.0
    LOAN_AMOUNT: Optional[float] = 0.0
    LOAN_REPAYMENT: Optional[float] = 0.0


class MonthlyDistributionCreate(MonthlyDistributionBase):
    class Config:
        allow_population_by_field_name = True  # lets you send "financial_year" instead of "FISCAL_YEAR"


class MonthlyDistributionOut(MonthlyDistributionBase):
    class Config:
        orm_mode = True
        allow_population_by_field_name = True


# -----------------------------
# Yearly Distribution Schemas
# -----------------------------
class YearlyDistributionBase(BaseModel):
    FISCAL_YEAR: str = Field(...)
    INCOME: Optional[float] = 0.0
    INV_BUY: Optional[float] = 0.0
    INV_SELL: Optional[float] = 0.0
    EXPENSE: Optional[float] = 0.0
    BANK: Optional[float] = 0.0
    TAX: Optional[float] = 0.0
    INTEREST_IN: Optional[float] = 0.0
    INTEREST_OUT: Optional[float] = 0.0
    LOAN_AMOUNT: Optional[float] = 0.0
    LOAN_REPAYMENT: Optional[float] = 0.0


class YearlyDistributionCreate(YearlyDistributionBase):
    class Config:
        allow_population_by_field_name = True


class YearlyDistributionOut(YearlyDistributionBase):
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
