import requests
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models import (
    Config, NAV, YearlyClosingBankBalance
)
from decimal import Decimal, getcontext
from datetime import datetime, date
import os
from app.utils.helper_functions import get_today_datetime

getcontext().prec = 10 

# ------------------- Config variables -------------------
TEMPLATES_DIR = "app/templates"
GENERATED_DIR = "generated_reports"
UPLOAD_DIR = "uploaded_files"
os.makedirs(GENERATED_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

RETIREMENT_SET = {"PF", "PROVIDENTFUND", "LIC"}
PORTFOLIO_TYPES = {"MUTUALFUND", "BONDS", "RD", "BANK"}
SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
ALLOWED_FILENAMES = {
    "expenses": {"expenses.xlsx"},
    "financial_data": {"financialdata.xlsx"},
    "mutualfund": {"mutualfund.csv"},
}

# ------------------- Config dates -------------------

def update_config_date(db: Session, user_id: int, field_name: str=None, value: date=None):
    """
    Update a specific date field in Config (like invest_last_updated_date, expensel_last_updated_date, financial_last_updated_date)
    and also update last_updated_date to today.
    """
    print(f'Updating configs for user: {user_id}')
    config = db.query(Config).filter(Config.user_id == user_id).first()

    if not config:
        print(f'Creating configs for user: {user_id}')
        config = Config(
            user_id=user_id,
            last_updated_date=date(1970, 1, 1),
            invest_last_updated_date=date(1970, 1, 1),
            expense_last_updated_date=date(1970, 1, 1),
            financial_last_updated_date=date(1970, 1, 1),
        )
        db.add(config)

    # validate column
    if field_name and not hasattr(config, field_name):
        raise AttributeError(f"Config has no field '{field_name}'")

    # update the target field
    if field_name:
        setattr(config, field_name, value)

    # always update last_updated_date to today
    config.last_updated_date = get_today_datetime()

    db.commit()
    db.refresh(config)
    return config

def get_config_last_updated_date(db: Session, user_id: int):
    print(f"Fetching Config from DB for user: {user_id}")
    config = db.query(Config).filter(Config.user_id == user_id).first()

    if not config:
        print(f" Create a new Config row for {user_id} user with default values")
        config = Config(
            user_id=user_id,
            last_updated_date=date(1970, 1, 1),
            invest_last_updated_date=date(1970, 1, 1),
            expense_last_updated_date=date(1970, 1, 1),
            financial_last_updated_date=date(1970, 1, 1),
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


# ------------------- NAV -------------------

def get_navs(db: Session):
    print('Get funds Details')
    return db.query(NAV).all()

def add_nav(nav_data: dict, db: Session):
    print('Add new funds NAV')
    nav_entry = NAV(
        type=nav_data["type"].upper(),
        fund_name=nav_data["fund_name"],
        unique_identifier=nav_data["unique_identifier"],
        nav=Decimal(nav_data.get("nav", 0)),
        last_updated=datetime.now()
    )
    db.add(nav_entry)
    db.commit()
    db.refresh(nav_entry)
    return nav_entry

def fetch_nav_from_internet(identifier: str, type_: str):
    print("Fetch NAV from internet based on type.")
    if type_.upper() == "MUTUALFUND":
        # AMFI India API
        url = f"https://api.mfapi.in/mf/{identifier}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data and len(data["data"]) > 0:
                return float(data["data"][0]["nav"])
    elif type_.upper() == "STOCK":
        # Yahoo Finance
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{identifier}?interval=1d"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            chart = resp.json()
            try:
                return float(chart["chart"]["result"][0]["meta"]["regularMarketPrice"])
            except Exception:
                return None
    return None

def update_navs(db: Session):
    print("Update NAVs for all records in DB.")
    navs = get_navs(db)
    if not navs:
        return []

    updated_list = []
    for nav in navs:
        current_nav = fetch_nav_from_internet(nav.unique_identifier, nav.type)
        if current_nav is not None:
            nav.nav = Decimal(current_nav)
            nav.last_updated = datetime.now()
            updated_list.append(nav)
    db.commit()
    return updated_list


# ------------------- Yearly Closing Bank Balance -------------------

def get_yearly_closing_balance(user_id: int, db: Session, financial_year: str = None):
    print(f'fetch Yearly Closing Balance for user {user_id} for financial year {financial_year}')
    query = db.query(YearlyClosingBankBalance).filter_by(user_id=user_id)
    if financial_year:
        balance = query.filter_by(financial_year=financial_year).first()
        if not balance:
            raise ValueError(f"No data found for '{financial_year}'.")
        else:
            return balance
    balance = query.order_by(YearlyClosingBankBalance.financial_year.desc()).first()
    print(f"Yearly Closing Bank Balance: {balance.closing_balance}")
    return balance


def create_yearly_closing_balance(user_id: int, financial_year: str, closing_balance: Decimal, db: Session):
    print(f'Create Yearly Closing Balance for user {user_id} for financial year {financial_year}')
    existing = db.query(YearlyClosingBankBalance).filter_by(user_id=user_id, financial_year=financial_year).first()
    if existing:
        raise ValueError(f"Closing balance already exists for {financial_year}")

    entry = YearlyClosingBankBalance(
        user_id=user_id,
        financial_year=financial_year,
        closing_balance=closing_balance
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_yearly_closing_balance(user_id: int, financial_year: str, closing_balance: Decimal, db: Session):
    print(f'Updating Yearly Closing Balance for user {user_id} for financial year {financial_year}')
    entry = db.query(YearlyClosingBankBalance).filter_by(user_id=user_id, financial_year=financial_year).first()
    if not entry:
        # if not found, create
        entry = YearlyClosingBankBalance(
            user_id=user_id,
            financial_year=financial_year,
            closing_balance=closing_balance
        )
        db.add(entry)
    else:
        entry.closing_balance = closing_balance
    db.commit()
    db.refresh(entry)
    return entry