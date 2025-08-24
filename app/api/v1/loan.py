from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.models import Loan
from app.schemas.income import LoanCreate, LoanOut
from app.api.v1.auth import get_current_user, get_db
from app.db.models import User
from app.services.loan import create_loan
router = APIRouter(prefix="/loan", tags=["Loan"])

@router.post("/", response_model=LoanOut)
def create_loan(
    data: LoanCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return create_loan(data, db, current_user.id)


@router.get("/", response_model=list[LoanOut])
def get_loans(
    year: str = None,
    month: str = None,
    financial_year: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Loan).filter(Loan.user_id == current_user.id)

    if year:
        query = query.filter(Loan.year == year)
    if month:
        query = query.filter(Loan.month == month)
    if financial_year:
        query = query.filter(Loan.financial_year == financial_year)

    return query.all()
