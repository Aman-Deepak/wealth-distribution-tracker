from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from app.db.models import Expense
from app.schemas.expense import ExpenseCreate, ExpenseOut
from app.api.v1.auth import get_current_user, get_db
from app.db.models import User
from app.services.expense import create_expense

router = APIRouter(prefix="/expense", tags=["Expense"])

@router.post("/", response_model=ExpenseOut)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return create_expense(data, db, current_user.id)


@router.get("/", response_model=list[ExpenseOut])
def get_expenses(
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
    query = db.query(Expense).filter(Expense.user_id == current_user.id)

    if year:
        query = query.filter(Expense.year == year)
    if month:
        query = query.filter(Expense.month == month)
    if financial_year:
        query = query.filter(Expense.financial_year == financial_year)
    if start_date:
        query = query.filter(
            (Expense.year + "-" + Expense.month + "-" + Expense.day) >= start_date.isoformat()
        )
    if end_date:
        query = query.filter(
            (Expense.year + "-" + Expense.month + "-" + Expense.day) <= end_date.isoformat()
        )

    total = query.count()
    items = query.order_by(Expense.year.desc(), Expense.month.desc(), Expense.day.desc()) \
                 .offset(skip).limit(limit).all()
    return items


