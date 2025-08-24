import pandas as pd
from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal
from app.db.models import Invest
from app.utils.helper_functions import compute_financial_year, to_decimal
from app.schemas.invest import InvestCreate
from app.services.summary import update_monthly_distributions, update_yearly_distributions, update_savings
from app.services.recon import reconcile_bank
from decimal import Decimal
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from app.db.models import Invest
from app.services.config import *


def create_invest(data: InvestCreate, db: Session, user_id: int):
    new_invest = Invest(**data.dict(), user_id=user_id)
    db.add(new_invest)
    db.commit()
    db.refresh(new_invest)
    fy = compute_financial_year(new_invest.year,new_invest.month)
    update_monthly_distributions(user_id, db, fy)
    reconcile_bank(user_id, db, fy, f"{new_invest.year}-{new_invest.month}-{new_invest.day}")
    update_yearly_distributions(user_id, db, fy)
    update_savings(user_id, db)
    return new_invest


def process_mutualfund_file(filepath: str, user_id: int, db: Session, last_updated_date: date):
    print(f"📂 Reading mutual fund CSV file: {filepath}")
    df = pd.read_csv(filepath)
    inserted_fys = set()
    df.columns = df.columns.str.upper().str.strip()
    print(f"📄 Processing mutual fund file with {len(df)} rows")
    required_cols = {'DATE', 'FOLIO NUMBER', 'NAME OF THE FUND', 'ORDER', 'UNITS', 'NAV',
       'CURRENT NAV', 'AMOUNT (INR)'}

    if not required_cols.issubset(df.columns):
        raise Exception(f"Missing required columns in mutual fund CSV")

    df = df.dropna(subset=["DATE"])
    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce").dt.date
    df = df[df["DATE"] > last_updated_date]
    print(f"📄 Inserting {len(df)} rows that matched condition (date > {last_updated_date}) for mutual fund file.")

    for _, row in df.iloc[::-1].iterrows():
        year = str(row["DATE"].year)
        month = str(row["DATE"].month).zfill(2)
        day = str(row["DATE"].day).zfill(2)
        fy = compute_financial_year(year, month)
        inserted_fys.add(fy)

        invest = Invest(
            user_id=user_id,
            financial_year=fy,
            year=year,
            month=month,
            day=day,
            type="MUTUALFUND",
            folio_number=row["FOLIO NUMBER"],
            name=row["NAME OF THE FUND"],
            type_of_order=row["ORDER"],
            units=Decimal(str(row["UNITS"])),
            nav=Decimal(str(row["NAV"])),
            cost=Decimal(str(row["AMOUNT (INR)"])),
        )
        db.add(invest)

    db.commit()
    if inserted_fys:
        sorted_fys = sorted(inserted_fys, key=lambda x: int(x.split('-')[0]))
        print(f"✅ Mutualfund data inserted successfully for FYs: {', '.join(sorted_fys)}")
        return sorted_fys
    else:
        print("ℹ️ No new Mutualfund data found after last updated date.")
        return []


# ---------- Data Fetch ----------
def fetch_invest_data(user_id: int, db: Session):
    print(f'Fetching Invest of user {user_id}')
    invest_rows = db.query(Invest).filter(Invest.user_id == user_id).all()

    if not invest_rows:
        print("No invest data found.")
        return pd.DataFrame(columns=["DATE","FISCAL_YEAR","TYPE_OF_ORDER","COST"])

    df = pd.DataFrame([{
        "DATE": datetime(int(i.year), int(i.month), int(i.day)),
        "FISCAL_YEAR": i.financial_year,
        "TYPE_OF_ORDER": (i.type_of_order or "").upper(),
        "COST": float(to_decimal(i.cost)),
    } for i in invest_rows])
    df.sort_values(by="DATE", inplace=True)
    print(f'Fetched {len(df)} records')
    return df