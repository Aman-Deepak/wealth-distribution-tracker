from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from app.db.models import Invest
from app.schemas.invest import InvestCreate, InvestOut
from app.api.v1.auth import get_current_user, get_db
from app.db.models import User
from app.services.invest import create_invest

router = APIRouter(prefix="/invest", tags=["Invest"])


@router.post("/", response_model=InvestOut)
def create_invest(
    data: InvestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return create_invest(data, db, current_user.id)

@router.get("/", response_model=list[InvestOut])
def get_investments(
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
    query = db.query(Invest).filter(Invest.user_id == current_user.id)

    if year:
        query = query.filter(Invest.year == year)
    if month:
        query = query.filter(Invest.month == month)
    if financial_year:
        query = query.filter(Invest.financial_year == financial_year)
    if start_date:
        query = query.filter(
            (Invest.year + "-" + Invest.month + "-" + Invest.day) >= start_date.isoformat()
        )
    if end_date:
        query = query.filter(
            (Invest.year + "-" + Invest.month + "-" + Invest.day) <= end_date.isoformat()
        )

    total = query.count()
    items = query.order_by(Invest.year.desc(), Invest.month.desc(), Invest.day.desc()) \
                 .offset(skip).limit(limit).all()
    return items

