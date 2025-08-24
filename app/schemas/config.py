from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


# -----------------------------
# Config Schemas
# -----------------------------
class ConfigBase(BaseModel):
    LAST_UPDATED_DATE: Optional[date] = Field(None, alias="last_updated_date")
    INVEST_LAST_UPDATED_DATE: Optional[date] = Field(None, alias="invest_last_updated_date")
    EXPENSE_LAST_UPDATED_DATE: Optional[date] = Field(None, alias="expense_last_updated_date")
    FINANCIAL_LAST_UPDATED_DATE: Optional[date] = Field(None, alias="financial_last_updated_date")


class ConfigCreate(BaseModel):
    FIELD_NAME: str
    VALUE: date
    class Config:
        allow_population_by_field_name = True
        orm_mode = True



class ConfigOut(ConfigBase):
    class Config:
        orm_mode = True
        allow_population_by_field_name = True


# -----------------------------
# Upload History Schemas
# -----------------------------
class UploadHistoryBase(BaseModel):
    FILENAME: str
    FILE_TYPE: str
    UPLOAD_TIME: Optional[datetime] = None


class UploadHistoryCreate(UploadHistoryBase):
    pass


class UploadHistoryOut(UploadHistoryBase):
    class Config:
        orm_mode = True


# -----------------------------
# NAV Schemas
# -----------------------------
class NAVBase(BaseModel):
    TYPE: str = Field(..., alias="type")
    FUND_NAME: str = Field(..., alias="fund_name")
    UNIQUE_IDENTIFIER: str = Field(..., alias="unique_identifier")
    NAV: Optional[float] = Field(None, alias="nav")
    LAST_UPDATED: Optional[datetime] = Field(None, alias="last_updated")


class NAVCreate(NAVBase):
    class Config:
        allow_population_by_field_name = True


class NAVOut(NAVBase):
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        by_alias = True
        


# -----------------------------
# Yearly Closing Bank Balance Schemas
# -----------------------------
class YearlyClosingBankBalanceBase(BaseModel):
    FINANCIAL_YEAR: str = Field(..., alias="financial_year")
    CLOSING_BALANCE: float = Field(..., alias="closing_balance")


class YearlyClosingBankBalanceCreate(YearlyClosingBankBalanceBase):
    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class YearlyClosingBankBalanceOut(YearlyClosingBankBalanceBase):
    class Config:
        orm_mode = True
        allow_population_by_field_name = True


