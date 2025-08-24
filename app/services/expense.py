from sqlalchemy.orm import Session
from app.db.models import (
    Expense
)
import pandas as pd
from decimal import Decimal
from datetime import date, datetime
from app.utils.helper_functions import compute_financial_year, get_current_financial_year, to_decimal
from app.schemas.expense import ExpenseCreate
from app.services.summary import update_monthly_distributions, update_yearly_distributions, update_savings
from app.services.recon import reconcile_bank


def create_expense(data: ExpenseCreate, db: Session, user_id: int):
    new_expense = Expense(**data.dict(), user_id=user_id)
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    fy = compute_financial_year(new_expense.year,new_expense.month)
    update_monthly_distributions(user_id, db, fy)
    reconcile_bank(user_id, db, fy, f"{new_expense.year}-{new_expense.month}-{new_expense.day}")
    update_yearly_distributions(user_id, db, fy)
    update_savings(user_id, db)
    return new_expense


def process_expense_file(filepath: str, user_id: int, db: Session, last_updated_date: date):
    print(f"📂 Reading expense file: {filepath} for user: {user_id}")
    xl = pd.ExcelFile(filepath)
    inserted_fys = set()

    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        print(f"📄 Processing sheet: {sheet} with {len(df)} rows")

        df.columns = df.columns.str.upper()
        required_cols = {"DATE", "CATEGORY", "COST"}
        if not required_cols.issubset(df.columns):
            raise Exception(f"Missing required columns in sheet: {sheet}")

        # Drop empty rows and ensure DATE is a date object
        df = df.dropna(subset=["DATE", "CATEGORY", "COST"])
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce").dt.date

        # Filter out older records
        df = df[df["DATE"] > last_updated_date]
        df["TYPE"] = sheet.upper()
        print(f"📄 Inserting {len(df)} rows that matched condition (date > {last_updated_date}) for sheet: {sheet}.")

        for _, row in df.iterrows():
            year = str(row["DATE"].year)
            month = str(row["DATE"].month).zfill(2)
            day = str(row["DATE"].day).zfill(2)
            fy = compute_financial_year(year, month)
            inserted_fys.add(fy)

            exp = Expense(
                user_id=user_id,
                financial_year=fy,
                year=year,
                month=month,
                day=day,
                type=row["TYPE"],
                category=row["CATEGORY"],
                cost=Decimal(str(row["COST"])),
            )
            db.add(exp)

    db.commit()
    if inserted_fys:
        sorted_fys = sorted(inserted_fys, key=lambda x: int(x.split('-')[0]))
        print(f"✅ Expenses inserted successfully for FYs: {', '.join(sorted_fys)}")
    else:
        print("ℹ️ No new expenses found after last updated date.")
    return sorted_fys



# ---------- Data Fetch & Prep ----------
def fetch_expense_data(user_id: int, db: Session) -> pd.DataFrame:
    print(f'Fetching Expense of user {user_id}')
    expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
    if not expenses:
        print("No Expense data found")
        return pd.DataFrame(columns=["DATE","FISCAL_YEAR","TYPE","CATEGORY","COST"])

    df = pd.DataFrame([{
        "DATE": datetime(int(e.year), int(e.month), int(e.day)),
        "FISCAL_YEAR": e.financial_year,
        "TYPE": e.type,
        "CATEGORY": e.category,
        "COST": float(to_decimal(e.cost)),
    } for e in expenses])
    df.sort_values(by="DATE", inplace=True)
    print(f'fetched {len(df)} records.')
    return df



