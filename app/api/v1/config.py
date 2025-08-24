from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.services import config
from app.schemas.config import NAVCreate, NAVOut, YearlyClosingBankBalanceOut, ConfigOut, YearlyClosingBankBalanceCreate, ConfigCreate
from app.api.v1.auth import get_current_user, get_db

router = APIRouter(prefix="/config", tags=["Config"])


# ------------------- Nav -------------------
@router.get("/nav", response_model=List[NAVOut])
def get_navs(db: Session = Depends(get_db)):
    return config.get_navs(db)

@router.post("/nav", response_model=NAVOut)
def add_nav(nav_data: NAVCreate, db: Session = Depends(get_db)):
    return config.add_nav(nav_data.dict(), db)

@router.put("/nav/update", response_model=List[NAVOut])
def update_navs(db: Session = Depends(get_db)):
    return config.update_navs(db)


# ------------------- Yearly Closing Bank Balance -------------------

@router.get("/yearly-closing-bank-balance", response_model=YearlyClosingBankBalanceOut)
def get_yearly_closing_balance(
    financial_year: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return config.get_yearly_closing_balance(current_user.id, db, financial_year)

@router.post("/yearly-closing-bank-balance", response_model=YearlyClosingBankBalanceOut)
def create_yearly_closing_balance(
    payload: YearlyClosingBankBalanceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return config.create_yearly_closing_balance(
        current_user.id,
        payload.FINANCIAL_YEAR,
        payload.CLOSING_BALANCE,
        db
    )

@router.put("/yearly-closing-bank-balance", response_model=YearlyClosingBankBalanceOut)
def update_yearly_closing_balance(
    payload: YearlyClosingBankBalanceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return config.update_yearly_closing_balance(
        current_user.id,
        payload.FINANCIAL_YEAR,
        payload.CLOSING_BALANCE,
        db
    )



# ------------------- config date -------------------

@router.put("/config/update", response_model=ConfigOut)
def update_config_date(
    payload: ConfigCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return config.update_config_date(db, current_user.id, field_name=payload.FIELD_NAME, value=payload.VALUE)

@router.get("/config/", response_model=ConfigOut)
def get_config_last_updated_date(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return config.get_config_last_updated_date(db, current_user.id)

