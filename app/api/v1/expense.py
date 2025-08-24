from fastapi import APIRouter, Depends
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
    year: str = None,
    month: str = None,
    financial_year: str = None,
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

    return query.all()
