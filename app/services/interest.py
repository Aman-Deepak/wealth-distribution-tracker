import pandas as pd
from sqlalchemy.orm import Session
from app.db.models import Interest
from app.utils.helper_functions import compute_financial_year, to_decimal
from app.schemas.interest import InterestCreate
from app.services.summary import update_monthly_distributions, update_yearly_distributions, update_savings
from app.services.recon import reconcile_bank
from datetime import datetime
from app.services.config import *


def create_interest(data: InterestCreate, db: Session, user_id: int):
    new_interest = Interest(**data.dict(), user_id=user_id)
    db.add(new_interest)
    db.commit()
    db.refresh(new_interest)
    fy = compute_financial_year(new_interest.year,new_interest.month)
    update_monthly_distributions(user_id, db, fy)
    reconcile_bank(user_id, db, fy, f"{new_interest.year}-{new_interest.month}-{new_interest.day}")
    update_yearly_distributions(user_id, db, fy)
    update_savings(user_id, db)
    return new_interest

# ---------- Data Fetch ----------
def fetch_interest_data(user_id: int, db: Session):
    print(f'Fetching Interests of user {user_id}')
    interest_rows = db.query(Interest).filter(Interest.user_id == user_id).all()

    if not interest_rows:
        print("No interest data found.")
        return pd.DataFrame(columns=["FISCAL_YEAR", "DATE", "TYPE", "NAME", "COST_IN", "COST_OUT"])

    df = pd.DataFrame([{
        "DATE": datetime(int(i.year), int(i.month), int(i.day)),
        "FISCAL_YEAR": i.financial_year,
        "TYPE": (i.type or "").upper(),
        "NAME": (i.name or "").upper(),
        "COST_IN": float(to_decimal(i.cost_in)),
        "COST_OUT": float(to_decimal(i.cost_out)),
    } for i in interest_rows])
    df.sort_values(by="DATE", inplace=True)
    print(f'Fetched {len(df)} records')
    return df