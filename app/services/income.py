import pandas as pd
from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal
from app.db.models import Income, Invest, Interest, Loan, Tax
from app.utils.helper_functions import compute_financial_year, to_decimal
from app.schemas.income import IncomeCreate
from app.services.summary import update_monthly_distributions, update_yearly_distributions, update_savings
from app.services.recon import reconcile_bank


def create_income(data: IncomeCreate, db: Session, user_id: int):
    new_income = Income(**data.dict(), user_id=user_id)
    db.add(new_income)
    db.commit()
    db.refresh(new_income)
    fy = compute_financial_year(new_income.year,new_income.month)
    update_monthly_distributions(user_id, db, fy)
    reconcile_bank(user_id, db, fy, f"{new_income.year}-{new_income.month}-{new_income.day}")
    update_yearly_distributions(user_id, db, fy)
    update_savings(user_id, db)
    return new_income


def process_financial_data_file(filepath: str, user_id: int, db: Session, last_updated_date: date):
    print(f"✨ Reading FinancialData file: {filepath}")
    xl = pd.ExcelFile(filepath)
    inserted_fys = set()
    latest_date = None

    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        sheet_upper = sheet.strip().upper()
        print(f"📄 Processing sheet: {sheet_upper} with {len(df)} rows")

        df.columns = df.columns.str.upper().str.strip()

        if sheet_upper == "INCOME":
            required_cols = {"DATE", "NAME", "TYPE", "AMOUNT", "EPF", "EPS"}
            if not required_cols.issubset(df.columns):
                raise Exception(f"Missing required columns in sheet: {sheet_upper}")

            df = df.dropna(subset=["DATE"])
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce").dt.date
            df = df[df["DATE"] > last_updated_date]
            print(f"📄 Inserting {len(df)} rows that matched condition (date > {last_updated_date}) for sheet: {sheet}.")

            for _, row in df.iterrows():
                row_date = row["DATE"]
                # Track the latest date
                if latest_date is None or row_date > latest_date:
                    latest_date = row_date
                year = str(row["DATE"].year)
                month = str(row["DATE"].month).zfill(2)
                day = str(row["DATE"].day).zfill(2)
                fy = compute_financial_year(year, month)
                inserted_fys.add(fy)
                income_amount = Decimal(str(row.get("AMOUNT", 0)))
                income_type = str(row.get("TYPE"))
                income_name = str(row.get("NAME"))

                if row.get("EPF", 0):
                    db.add(Invest(
                        user_id=user_id, financial_year=fy, year=year, month=month, day=day,
                        type="PROVIDENTFUND", folio_number="", name="EPF", type_of_order="BUY",
                        units=Decimal("0.0"), nav=Decimal("0.0"), cost=Decimal(str(row["EPF"]))))
                if row.get("EPS", 0):
                    db.add(Invest(
                        user_id=user_id, financial_year=fy, year=year, month=month, day=day,
                        type="PROVIDENTFUND", folio_number="", name="EPS", type_of_order="BUY",
                        units=Decimal("0.0"), nav=Decimal("0.0"), cost=Decimal(str(row["EPS"]))))

                db.add(Income(
                    user_id=user_id, financial_year=fy, year=year, month=month, day=day,
                    type=income_type,name = income_name, amount=income_amount))

        elif sheet_upper == "INVEST":
            required_cols = {"DATE", "TYPE", "FOLIO_NUMBER", "NAME", "TYPE_OF_ORDER", "UNITS", "NAV", "COST"}
            if not required_cols.issubset(df.columns):
                raise Exception(f"Missing required columns in sheet: {sheet_upper}")

            df = df.dropna(subset=["DATE"])
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce").dt.date
            df = df[df["DATE"] > last_updated_date]
            print(f"📄 Inserting {len(df)} rows that matched condition (date > {last_updated_date}) for sheet: {sheet}.")

            for _, row in df.iterrows():
                row_date = row["DATE"]
                # Track the latest date
                if latest_date is None or row_date > latest_date:
                    latest_date = row_date
                year = str(row["DATE"].year)
                month = str(row["DATE"].month).zfill(2)
                day = str(row["DATE"].day).zfill(2)
                fy = compute_financial_year(year, month)
                inserted_fys.add(fy)

                db.add(Invest(
                    user_id=user_id, financial_year=fy, year=year, month=month, day=day,
                    type=row["TYPE"], folio_number=row["FOLIO_NUMBER"], name=row["NAME"],
                    type_of_order=row["TYPE_OF_ORDER"], units=Decimal(str(row["UNITS"])),
                    nav=Decimal(str(row["NAV"])), cost=Decimal(str(row["COST"]))))

        elif sheet_upper == "INTEREST":
            required_cols = {"FINANCIAL_YEAR", "DATE", "TYPE", "NAME", "COST_IN", "COST_OUT", "CREDIT_IN"}
            if not required_cols.issubset(df.columns):
                raise Exception(f"Missing required columns in sheet: {sheet_upper}")

            df = df.dropna(subset=["DATE"])
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce").dt.date
            df = df[df["DATE"] > last_updated_date]
            print(f"📄 Inserting {len(df)} rows that matched condition (date > {last_updated_date}) for sheet: {sheet}.")

            for _, row in df.iterrows():
                print(row)
                row_date = row["DATE"]
                # Track the latest date
                if latest_date is None or row_date > latest_date:
                    latest_date = row_date
                year = str(row["DATE"].year)
                month = str(row["DATE"].month).zfill(2)
                day = str(row["DATE"].day).zfill(2)
                fy = compute_financial_year(year, month)
                inserted_fys.add(fy)

                db.add(Interest(
                    user_id=user_id, financial_year=fy, year=year, month=month, day=day,
                    type=row["TYPE"], name=row["NAME"],
                    cost_in=Decimal(str(row.get("COST_IN", 0))), cost_out=Decimal(str(row.get("COST_OUT", 0))), credit_in=int(row.get("CREDIT_IN"))))

        elif sheet_upper == "LOAN":
            required_cols = {"FINANCIAL_YEAR", "DATE", "TYPE", "NAME", "INTEREST", "LOAN_AMOUNT", "LOAN_REPAYMENT"}
            if not required_cols.issubset(df.columns):
                raise Exception(f"Missing required columns in sheet: {sheet_upper}")

            df = df.dropna(subset=["DATE"])
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce").dt.date
            df = df[df["DATE"] > last_updated_date]
            print(f"📄 Inserting {len(df)} rows that matched condition (date > {last_updated_date}) for sheet: {sheet}.")

            for _, row in df.iterrows():
                row_date = row["DATE"]
                # Track the latest date
                if latest_date is None or row_date > latest_date:
                    latest_date = row_date
                year = str(row["DATE"].year)
                month = str(row["DATE"].month).zfill(2)
                day = str(row["DATE"].day).zfill(2)
                fy = compute_financial_year(year, month)
                inserted_fys.add(fy)

                db.add(Loan(
                    user_id=user_id, financial_year=fy, year=year, month=month, day=day,
                    type=row["TYPE"], name=row["NAME"], interest=row["INTEREST"],
                    loan_amount=Decimal(str(row["LOAN_AMOUNT"])),
                    loan_repayment=Decimal(str(row["LOAN_REPAYMENT"])), cost=Decimal("0.0")))
        
        elif sheet_upper == "TAX":
            required_cols = {"DATE", "NAME", "TYPE", "AMOUNT", "REFUND"}
            if not required_cols.issubset(df.columns):
                raise Exception(f"Missing required columns in sheet: {sheet_upper}")

            df = df.dropna(subset=["DATE"])
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce").dt.date
            df = df[df["DATE"] > last_updated_date]
            print(f"📄 Inserting {len(df)} rows that matched condition (date > {last_updated_date}) for sheet: {sheet}.")

            for _, row in df.iterrows():
                row_date = row["DATE"]
                # Track the latest date
                if latest_date is None or row_date > latest_date:
                    latest_date = row_date
                year = str(row["DATE"].year)
                month = str(row["DATE"].month).zfill(2)
                day = str(row["DATE"].day).zfill(2)
                fy = compute_financial_year(year, month)
                inserted_fys.add(fy)
                tax_amount = Decimal(str(row.get("AMOUNT", 0)))
                tax_refund = Decimal(str(row.get("REFUND", 0)))
                tax_type = str(row.get("TYPE"))
                tax_name = str(row.get("NAME"))

                db.add(Tax(
                    user_id=user_id, financial_year=fy, year=year, month=month, day=day,
                    type=tax_type,name = tax_name, amount=tax_amount, refund=tax_refund))

    db.commit()
    if inserted_fys:
        sorted_fys = sorted(inserted_fys, key=lambda x: int(x.split('-')[0]))
        print(f"✅ FinancialData inserted successfully for FYs: {', '.join(sorted_fys)}")
        print(f"📅 Latest Mutualfund date: {latest_date}")
        return sorted_fys, latest_date
    else:
        print("ℹ️ No new FinancialData found after last updated date.")
        return [], latest_date
    

# ---------- Data Fetch & Prep ----------
def fetch_income_data(user_id: int, db: Session) -> pd.DataFrame:
    print(f'Fetching Income of user {user_id}')
    income = db.query(Income).filter(Income.user_id == user_id).all()
    if not income:
        print("No Income data found")
        return pd.DataFrame(columns=["FISCAL_YEAR", "DATE", "TYPE", "NAME", "AMOUNT"])
    
    df = pd.DataFrame([{
        "DATE": datetime(int(i.year), int(i.month), int(i.day)),
        "FISCAL_YEAR": i.financial_year,
        "TYPE": (i.type or "").upper(),
        "NAME": (i.name or "").upper(),
        "AMOUNT": float(to_decimal(i.amount)),
    } for i in income])
    df.sort_values(by="DATE", inplace=True)
    print(f'Fetched {len(df)} records')
    return df

