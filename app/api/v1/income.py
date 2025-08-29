from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from app.db.models import Income
from app.schemas.income import IncomeCreate, IncomeOut
from app.api.v1.auth import get_current_user, get_db
from app.db.models import User
from app.services.income import create_income
router = APIRouter(prefix="/income", tags=["Income"])

@router.post("/", response_model=IncomeOut)
def create_income(
    data: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return create_income(data, db, current_user.id)


@router.get("/", response_model=list[IncomeOut])
def get_incomes(
    skip: int = 0,
    limit: int = 25,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    year: Optional[str] = None,
    month: Optional[str] = None,
    financial_year: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Income).filter(Income.user_id == current_user.id)

    if year:
        query = query.filter(Income.year == year)
    if month:
        query = query.filter(Income.month == month)
    if financial_year:
        query = query.filter(Income.financial_year == financial_year)
    if start_date:
        query = query.filter(
            (Income.year + "-" + Income.month + "-" + Income.day) >= start_date.isoformat()
        )
    if end_date:
        query = query.filter(
            (Income.year + "-" + Income.month + "-" + Income.day) <= end_date.isoformat()
        )

    total = query.count()
    items = query.order_by(Income.year.desc(), Income.month.desc(), Income.day.desc()) \
                 .offset(skip).limit(limit).all()
    return items

