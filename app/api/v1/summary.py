from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.api.v1.auth import get_current_user, get_db
from app.services.summary import update_savings, fetch_monthly_distribution_data, fetch_yearly_distribution_data, fetch_savings_data
from app.schemas.summary import MonthlyDistributionOut, YearlyDistributionOut, SavingOut
from typing import List

router = APIRouter(prefix="/summary", tags=["Summary"])


# ------------------- Monthly Summary -------------------
@router.get("/monthly/", response_model=List[MonthlyDistributionOut])
def get_monthly_summary(
    financial_year: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    df = fetch_monthly_distribution_data(user_id=current_user.id, db=db, financial_year=financial_year)
    records = df.to_dict(orient="records")
    return records


# ------------------- Yearly Summary -------------------

@router.get("/yearly/", response_model=List[YearlyDistributionOut])
def get_yearly_summary(
    financial_year: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    df = fetch_yearly_distribution_data(user_id=current_user.id, db=db, financial_year=financial_year)
    records = df.to_dict(orient="records")
    return records


# ------------------- Savings -------------------

@router.get("/savings/", response_model=List[SavingOut])
def get_savings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    df = fetch_savings_data(user_id=current_user.id, db=db)
    records = df.to_dict(orient="records")
    return records

@router.put("/saving/update")
def update_savings_data(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return update_savings(user_id=current_user.id, db=db)

