from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from app.db.models import Tax
from app.schemas.tax import TaxCreate, TaxOut
from app.api.v1.auth import get_current_user, get_db
from app.db.models import User
from app.services.tax import create_tax
router = APIRouter(prefix="/tax", tags=["Tax"])

@router.post("/", response_model=TaxOut)
def create_taxes(
    data: TaxCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return create_tax(data, db, current_user.id)


@router.get("/", response_model=list[TaxOut])
def get_taxes(
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
    query = db.query(Tax).filter(Tax.user_id == current_user.id)

    if year:
        query = query.filter(Tax.year == year)
    if month:
        query = query.filter(Tax.month == month)
    if financial_year:
        query = query.filter(Tax.financial_year == financial_year)
    if start_date:
        query = query.filter(
            (Tax.year + "-" + Tax.month + "-" + Tax.day) >= start_date.isoformat()
        )
    if end_date:
        query = query.filter(
            (Tax.year + "-" + Tax.month + "-" + Tax.day) <= end_date.isoformat()
        )

    total = query.count()
    items = query.order_by(Tax.year.desc(), Tax.month.desc(), Tax.day.desc()) \
                 .offset(skip).limit(limit).all()
    return items

