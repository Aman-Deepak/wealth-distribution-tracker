import pandas as pd
from sqlalchemy.orm import Session
from app.db.models import Tax
from app.utils.helper_functions import compute_financial_year, to_decimal
from app.schemas.tax import TaxCreate
from app.services.summary import update_monthly_distributions, update_yearly_distributions, update_savings
from app.services.recon import reconcile_bank
from datetime import datetime
from app.services.config import *


def create_tax(data: TaxCreate, db: Session, user_id: int):
    new_tax = Tax(**data.dict(), user_id=user_id)
    db.add(new_tax)
    db.commit()
    db.refresh(new_tax)
    fy = compute_financial_year(new_tax.year,new_tax.month)
    update_monthly_distributions(user_id, db, fy)
    reconcile_bank(user_id, db, fy, f"{new_tax.year}-{new_tax.month}-{new_tax.day}")
    update_yearly_distributions(user_id, db, fy)
    update_savings(user_id, db)
    return new_tax

# ---------- Data Fetch ----------
def fetch_tax_data(user_id: int, db: Session):
    print(f'Fetching Taxes of user {user_id}')
    tax_rows = db.query(Tax).filter(Tax.user_id == user_id).all()

    if not tax_rows:
        print("No tax data found.")
        return pd.DataFrame(columns=["FISCAL_YEAR", "DATE", "TYPE", "NAME", "AMOUNT", "REFUND"])

    df = pd.DataFrame([{
        "DATE": datetime(int(i.year), int(i.month), int(i.day)),
        "FISCAL_YEAR": i.financial_year,
        "TYPE": (i.type or "").upper(),
        "NAME": (i.name or "").upper(),
        "AMOUNT": float(to_decimal(i.amount)),
        "REFUND": float(to_decimal(i.refund)),
    } for i in tax_rows])
    df.sort_values(by="DATE", inplace=True)
    print(f'Fetched {len(df)} records')
    return df