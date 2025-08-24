import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models import Loan
from app.utils.helper_functions import compute_financial_year, to_decimal
from app.schemas.loan import LoanCreate
from app.services.summary import update_monthly_distributions, update_yearly_distributions, update_savings
from app.services.recon import reconcile_bank


def create_loan(data: LoanCreate, db: Session, user_id: int):
    new_loan_entry = Loan(**data.dict(), user_id=user_id)
    db.add(new_loan_entry)
    db.commit()
    db.refresh(new_loan_entry)
    fy = compute_financial_year(new_loan_entry.year,new_loan_entry.month)
    update_monthly_distributions(user_id, db, fy)
    reconcile_bank(user_id, db, fy, f"{new_loan_entry.year}-{new_loan_entry.month}-{new_loan_entry.day}")
    update_yearly_distributions(user_id, db, fy)
    update_savings(user_id, db)
    return new_loan_entry


# ---------- Data Fetch & Prep ----------
def fetch_loan_data(user_id: int, db: Session) -> pd.DataFrame:
    print(f'Fetching Loan of user {user_id}')
    loans_rows = db.query(Loan).filter(Loan.user_id == user_id).all()
    if not loans_rows:
        print("No Loan data found")
        return pd.DataFrame(columns=["DATE","LOAN_AMOUNT", "LOAN_REPAYMENT"])
    
    df = pd.DataFrame([{
        "DATE": datetime(int(l.year), int(l.month), int(l.day)) if getattr(l, "year", None) else None,
        "LOAN_AMOUNT": float(to_decimal(getattr(l, "loan_amount", 0))),
        "LOAN_REPAYMENT": float(to_decimal(getattr(l, "loan_repayment", 0))),
    } for l in loans_rows])
    df.sort_values(by="DATE", inplace=True)
    print(f'Fetched {len(df)} records')
    return df
