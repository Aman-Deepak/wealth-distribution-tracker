from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from app.db.models import Interest
from app.schemas.interest import InterestCreate, InterestOut
from app.api.v1.auth import get_current_user, get_db
from app.db.models import User
from app.services.interest import create_interest
router = APIRouter(prefix="/interest", tags=["Interest"])

@router.post("/", response_model=InterestOut)
def create_inrst(
    data: InterestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return create_interest(data, db, current_user.id)


@router.get("/", response_model=list[InterestOut])
def get_interests(
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
    query = db.query(Interest).filter(Interest.user_id == current_user.id)

    if year:
        query = query.filter(Interest.year == year)
    if month:
        query = query.filter(Interest.month == month)
    if financial_year:
        query = query.filter(Interest.financial_year == financial_year)
    if start_date:
        query = query.filter(
            (Interest.year + "-" + Interest.month + "-" + Interest.day) >= start_date.isoformat()
        )
    if end_date:
        query = query.filter(
            (Interest.year + "-" + Interest.month + "-" + Interest.day) <= end_date.isoformat()
        )

    total = query.count()
    items = query.order_by(Interest.year.desc(), Interest.month.desc(), Interest.day.desc()) \
                 .offset(skip).limit(limit).all()
    return items

