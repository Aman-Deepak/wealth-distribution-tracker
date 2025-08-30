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


# -----------------------------
# Dashboard Summary & Insights Schemas
# -----------------------------
class DashboardSummary(BaseModel):
    TOTAL_EXPENSES: str = "N/A"
    AVG_MONTHLY_EXPENSE: str = "N/A"
    HIGHEST_EXPENSE_MONTH: str = "N/A"
    LOWEST_EXPENSE_MONTH: str = "N/A"
    TOTAL_INVESTED: str = "N/A"
    TOTAL_VALUE: str = "N/A"
    TOTAL_PNL: str = "N/A"
    WEIGHTED_RETURN: str = "N/A"
    PROFIT_BOOKED_SUM: str = "N/A"
    TOTAL_WEALTH: str = "N/A"
    LIQUID_WEALTH: str = "N/A"
    TOTAL_LOANS: str = "N/A"
    BANK_BALANCE: str = "N/A"

class DashboardSummaryOut(DashboardSummary):
    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class DashboardInsights(BaseModel):
    # Expense insights
    HIGHEST_CATEGORY: str = "N/A"
    HIGHEST_TYPE: str = "N/A"
    AVG_MONTHLY_EXPENSE: str = "N/A"
    YOY_EXPENSE: str = "N/A"

    # Investment insights
    TOP_ASSET: str = "N/A"
    BOTTOM_ASSET: str = "N/A"
    LARGEST_HOLDING: str = "N/A"
    TOP_RETIREMENT_ASSET: str = "N/A"
    YOY_INVEST: str = "N/A"
    CONCENTRATION_RISK: str = "N/A"

    # Financial insights
    PORTFOLIO_RETURN: str = "N/A"
    RETIREMENT_RETURN: str = "N/A"

class DashboardInsightsOut(DashboardInsights):
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
