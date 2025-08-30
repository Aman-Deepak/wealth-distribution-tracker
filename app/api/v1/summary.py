from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.api.v1.auth import get_current_user, get_db
from app.services.summary import update_savings, fetch_monthly_distribution_data, fetch_yearly_distribution_data, fetch_savings_data
from app.schemas.summary import MonthlyDistributionOut, YearlyDistributionOut, SavingOut, DashboardSummaryOut, DashboardInsightsOut
from typing import List
from typing import Dict
from app.api.v1.auth import get_current_user, get_db
from app.services.expense import fetch_expense_data
from app.services.income import fetch_income_data
from app.services.loan import fetch_loan_data
from app.services.insights import calculate_summary, calculate_insights
from app.services.config import get_yearly_closing_balance


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



# ------------------- Dashboard Summary -------------------
@router.get("/dashboard", response_model=DashboardSummaryOut)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user.id
    # Fetch dataframes
    exp_df = fetch_expense_data(user_id=user_id, db=db)
    sav_df = fetch_savings_data(user_id=user_id, db=db)
    loan_df = fetch_loan_data(user_id=user_id, db=db)
    # Bank balance from config service
    bank_balance = None
    try:
        bank_balance = get_yearly_closing_balance(user_id=user_id, db=db).closing_balance
    except:
        pass

    # Calculate all metrics in one shot
    summary = calculate_summary(
        exp_df=exp_df,
        sav_df=sav_df,
        loans_df=loan_df,
        bank_balance=bank_balance
    )
    # Map keys to friendly names
    return summary

@router.get("/dashboard/insights", response_model=DashboardInsightsOut)
def get_dashboard_insights(
    db: Session = Depends(get_db), 
    current_user=Depends(get_current_user)
):
    user_id = current_user.id
    # Fetch dataframes
    exp_df = fetch_expense_data(user_id=user_id, db=db)
    sav_df = fetch_savings_data(user_id=user_id, db=db)
    inv_df = fetch_income_data(user_id=user_id, db=db)
    insight_data = calculate_insights(exp_df=exp_df, sav_df=sav_df, inv_df=inv_df)
    return insight_data
