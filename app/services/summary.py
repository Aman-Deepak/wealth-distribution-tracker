from sqlalchemy.orm import Session
import pandas as pd
from sqlalchemy import func, case
from datetime import datetime
from decimal import Decimal
from app.db.models import (
    Income, Expense, Invest, Interest, Loan,
    MonthlyDistribution, YearlyDistribution, Savings
)
from collections import defaultdict
from app.utils.helper_functions import to_decimal
from app.services.config import *

# -----------------------------
# Monthly Distribution
# -----------------------------

def fetch_monthly_distribution_data(user_id: int, db: Session, financial_year: str=None) -> pd.DataFrame:
    print(f'Fetching Monthly Distribution of user {user_id} for Finanacial Year: {financial_year}')
    monthly_rows = db.query(MonthlyDistribution).filter(MonthlyDistribution.user_id == user_id)
    if financial_year:
        monthly_rows = monthly_rows.filter(MonthlyDistribution.financial_year == financial_year)
    if not monthly_rows:
        print("No Monthly Distribution data found.")
        return pd.DataFrame(columns=["FISCAL_YEAR","INCOME","INV_BUY","INV_SELL","EXPENSE","BANK","TAX","INTEREST_IN","INTEREST_OUT", "LOAN_AMOUNT", "LOAN_REPAYMENT"])
    df = pd.DataFrame([{
        "FISCAL_YEAR": row.financial_year,
        "INCOME": float(to_decimal(row.income)),
        "INV_BUY": float(to_decimal(row.inv_buy)),
        "INV_SELL": float(to_decimal(row.inv_sell)),
        "EXPENSE": float(to_decimal(row.expenses)),
        "BANK": float(to_decimal(row.bank)),
        "TAX": float(to_decimal(row.tax)),
        "INTEREST_IN": float(to_decimal(row.interest_in)),
        "INTEREST_OUT": float(to_decimal(row.interest_out)),
        "LOAN_AMOUNT": float(to_decimal(row.loan_amount)),
        "LOAN_REPAYMENT": float(to_decimal(row.loan_repayment)),
    } for row in monthly_rows])
    print(f'Fetched : {len(df)} records')
    return df

def update_monthly_distributions(user_id: int, db: Session, fy: str):
    print(f"♻️ Recomputing monthly distribution for FY {fy}")

    # Clear current FY monthly data
    deleted = db.query(MonthlyDistribution).filter(
        MonthlyDistribution.user_id == user_id,
        MonthlyDistribution.financial_year == fy
    ).delete()
    db.commit()
    print(f"🗑 Deleted {deleted} monthly records for FY {fy}")

    def sum_case(model, column, value):
        """Helper for SUM(CASE WHEN ...) in SQLAlchemy 2.x"""
        return func.sum(case((column == value, model.cost), else_=Decimal("0.0")))

    # ---- Gather data ----
    invest_data = db.query(
        Invest.year, Invest.month,
        sum_case(Invest, Invest.type_of_order, "BUY").label("inv_buy"),
        sum_case(Invest, Invest.type_of_order, "SELL").label("inv_sell")
    ).filter(
        Invest.user_id == user_id,
        Invest.financial_year == fy
    ).group_by(Invest.year, Invest.month).all()

    income_data = db.query(
        Income.year, Income.month,
        func.sum(Income.salary).label("income"),
        func.sum(Income.tax).label("tax")
    ).filter(
        Income.user_id == user_id,
        Income.financial_year == fy
    ).group_by(Income.year, Income.month).all()

    expense_data = db.query(
        Expense.year, Expense.month,
        func.sum(Expense.cost).label("expenses")
    ).filter(
        Expense.user_id == user_id,
        Expense.financial_year == fy
    ).group_by(Expense.year, Expense.month).all()

    interest_data = db.query(
        Interest.year, Interest.month,
        func.sum(Interest.cost_in).label("interest_in"),
        func.sum(Interest.cost_out).label("interest_out")
    ).filter(
        Interest.user_id == user_id,
        Interest.financial_year == fy
    ).group_by(Interest.year, Interest.month).all()

    interest_credit_data = db.query(
        Interest.year, Interest.month,
        func.sum(Interest.cost_in).label("credit_in")
    ).filter(
        Interest.user_id == user_id,
        Interest.financial_year == fy,
        Interest.type.in_(("BANK", "BONDS"))
    ).group_by(Interest.year, Interest.month).all()

    loan_data = db.query(
        Loan.year, Loan.month,
        func.sum(Loan.loan_amount).label("loan_amount"),
        func.sum(Loan.loan_repayment).label("loan_repayment")
    ).filter(
        Loan.user_id == user_id,
        Loan.financial_year == fy
    ).group_by(Loan.year, Loan.month).all()

    # ---- Merge into month_map ----
    month_map = {}
    for dataset in [invest_data, income_data, expense_data, interest_data, loan_data, interest_credit_data]:
        for row in dataset:
            key = (row.year, row.month)
            if key not in month_map:
                month_map[key] = {}
            month_map[key].update(row._asdict())

    # ---- Insert into MonthlyDistribution ----
    count = 0
    for (year, month), data in month_map.items():
        count += 1
        bank = Decimal(str(data.get("income", 0.0))) \
             + Decimal(str(data.get("inv_sell", 0.0))) \
             + Decimal(str(data.get("loan_amount", 0.0))) \
             + Decimal(str(data.get("credit_in", 0.0))) \
             - Decimal(str(data.get("inv_buy", 0.0))) \
             - Decimal(str(data.get("expenses", 0.0))) \
             - Decimal(str(data.get("loan_repayment", 0.0))) \
             - Decimal(str(data.get("interest_out", 0.0))) \
             - Decimal(str(data.get("tax", 0.0)))

        rec = MonthlyDistribution(
            user_id=user_id,
            financial_year=fy,
            year=year,
            month=month,
            income=Decimal(str(data.get("income", 0.0))),
            inv_buy=Decimal(str(data.get("inv_buy", 0.0))),
            inv_sell=Decimal(str(data.get("inv_sell", 0.0))),
            expenses=Decimal(str(data.get("expenses", 0.0))),
            bank=bank,
            tax=Decimal(str(data.get("tax", 0.0))),
            interest_in=Decimal(str(data.get("interest_in", 0.0))),
            interest_out=Decimal(str(data.get("interest_out", 0.0))),
            loan_amount=Decimal(str(data.get("loan_amount", 0.0))),
            loan_repayment=Decimal(str(data.get("loan_repayment", 0.0)))
        )
        db.add(rec)

    db.commit()
    print(f"✅ Monthly distribution updated for FY {fy} count: {count}")



# -----------------------------
# Yearly Distribution
# -----------------------------
def fetch_yearly_distribution_data(user_id: int, db: Session, financial_year: str=None) -> pd.DataFrame:
    print(f'Fetching Yearly Distribution of user {user_id} for Finanacial Year: {financial_year}')
    yearly_rows = db.query(YearlyDistribution).filter(YearlyDistribution.user_id == user_id)
    if financial_year:
        yearly_rows = yearly_rows.filter(YearlyDistribution.financial_year == financial_year)
    if not yearly_rows:
        print("No Yearly Distribution data found.")
        return pd.DataFrame(columns=["FISCAL_YEAR","INCOME","INV_BUY","INV_SELL","EXPENSE","BANK","TAX","INTEREST_IN","INTEREST_OUT", "LOAN_AMOUNT", "LOAN_REPAYMENT"])
    df = pd.DataFrame([{
        "FISCAL_YEAR": row.financial_year,
        "INCOME": float(to_decimal(row.income)),
        "INV_BUY": float(to_decimal(row.inv_buy)),
        "INV_SELL": float(to_decimal(row.inv_sell)),
        "EXPENSE": float(to_decimal(row.expenses)),
        "BANK": float(to_decimal(row.bank)),
        "TAX": float(to_decimal(row.tax)),
        "INTEREST_IN": float(to_decimal(row.interest_in)),
        "INTEREST_OUT": float(to_decimal(row.interest_out)),
        "LOAN_AMOUNT": float(to_decimal(row.loan_amount)),
        "LOAN_REPAYMENT": float(to_decimal(row.loan_repayment)),
    } for row in yearly_rows])
    print(f'Fetched {len(df)} records')
    return df

def update_yearly_distributions(user_id: int, db: Session, fy: str):
    print(f"♻️ Recomputing yearly distribution for FY {fy}")

    # Clear current FY yearly data
    deleted = db.query(YearlyDistribution).filter(
        YearlyDistribution.user_id == user_id,
        YearlyDistribution.financial_year == fy
    ).delete()
    db.commit()
    print(f"🗑 Deleted {deleted} yearly records for FY {fy}")

    sums = db.query(
        func.sum(MonthlyDistribution.income),
        func.sum(MonthlyDistribution.inv_buy),
        func.sum(MonthlyDistribution.inv_sell),
        func.sum(MonthlyDistribution.expenses),
        func.sum(MonthlyDistribution.bank),
        func.sum(MonthlyDistribution.tax),
        func.sum(MonthlyDistribution.interest_in),
        func.sum(MonthlyDistribution.interest_out),
        func.sum(MonthlyDistribution.loan_amount),
        func.sum(MonthlyDistribution.loan_repayment)
    ).filter(
        MonthlyDistribution.user_id == user_id,
        MonthlyDistribution.financial_year == fy
    ).first()

    yd = YearlyDistribution(
        user_id=user_id,
        financial_year=fy,
        income=sums[0] or Decimal("0.0"),
        inv_buy=sums[1] or Decimal("0.0"),
        inv_sell=sums[2] or Decimal("0.0"),
        expenses=sums[3] or Decimal("0.0"),
        bank=sums[4] or Decimal("0.0"),
        tax=sums[5] or Decimal("0.0"),
        interest_in=sums[6] or Decimal("0.0"),
        interest_out=sums[7] or Decimal("0.0"),
        loan_amount=sums[8] or Decimal("0.0"),
        loan_repayment=sums[9] or Decimal("0.0")
    )
    db.add(yd)
    db.commit()
    print(f"✅ Yearly distribution updated for FY {fy}")



# -----------------------------
# Savings
# -----------------------------

def fetch_savings_data(user_id: int, db: Session) -> pd.DataFrame:
    print(f'Fetching Savings of user {user_id}')
    savings_rows = db.query(Savings).filter(Savings.user_id == user_id).all()
    if not savings_rows:
        print("No savings data found.")
        return pd.DataFrame(columns=[
            "TYPE", "NAME", "T_BUY", "T_SELL", "PROFIT_BOOKED",
            "CURRENT_INVESTED", "CURRENT_VALUE", "PROFIT_LOSS", "RETURN_PERCENTAGE"
        ])
    
    df = pd.DataFrame([{
        "TYPE": s.type or "",
        "NAME": s.name or "",
        "T_BUY": float(to_decimal(s.t_buy)),
        "T_SELL": float(to_decimal(s.t_sell)),
        "PROFIT_BOOKED": float(to_decimal(s.profit_booked)),
        "CURRENT_INVESTED": float(to_decimal(s.current_invested)),
        "CURRENT_VALUE": float(to_decimal(s.current_value)),
        "PROFIT_LOSS": float(to_decimal(s.profit_loss)),
        "RETURN_PERCENTAGE": float(to_decimal(s.return_percentage)),
    } for s in savings_rows])
    print(f'Fetched {len(df)} records')
    return df

def update_savings(user_id: int, db: Session):
    """
    Master function:
    - Loads NAVs, investments and interests
    - Groups by (type, name)
    - Calls per-type handler (here: MF / STOCK via FIFO)
    - Writes Savings rows
    """
    print("♻️ Starting update_savings for user_id=%s" %(user_id))

    # 1) delete old savings rows
    deleted = db.query(Savings).filter(Savings.user_id == user_id).delete()
    db.commit()
    print("🗑 Deleted %d old savings rows" %(deleted))

    # 2) load NAVs into dict {fund_name: Decimal(nav) or None}
    nav_rows = get_navs(db)
    nav_map = {n.fund_name: (Decimal(str(n.nav)) if n.nav is not None else None) for n in nav_rows}

    # 3) load investments and interests for the user
    invests = db.query(Invest).filter(Invest.user_id == user_id).order_by(Invest.name, Invest.year, Invest.month, Invest.day).all()
    interests = db.query(Interest).filter(Interest.user_id == user_id).all()
    print("📥 Loaded %d invest rows and %d interest rows" %(len(invests), len(interests)))

    # 4) group invests by (type, name)
    invest_map = defaultdict(list)
    for inv in invests:
        invest_map[(inv.type, inv.name)].append(inv)

    # 5) aggregate interest in/out by (type, name)
    interest_map = defaultdict(lambda: {"in": Decimal(0), "out": Decimal(0)})
    for intr in interests:
        key = (intr.type, intr.name)
        interest_map[key]["in"] += Decimal(str(intr.cost_in or 0))
        interest_map[key]["out"] += Decimal(str(intr.cost_out or 0))
    
    #Process Bank
    print("➡ Processing Bank / HDFC")
    intr = interest_map[("Bank", "HDFC")]
    bank_balance =  get_yearly_closing_balance(user_id, db).closing_balance
    interest_in = intr["in"]
    interest_out = intr["out"]
    res = calc_bank("HDFC", bank_balance, interest_in, interest_out)
    s = Savings(
        user_id=user_id,
        name="HDFC",
        type="Bank",
        t_buy=res["t_buy"],
        t_sell=res["t_sell"],
        profit_booked=res["profit_booked"],
        current_invested=res["current_invested"],
        current_value=res["current_value"],
        profit_loss=res["profit_loss"]
    )
    db.add(s)
    
    # 6) process groups
    for (inv_type, name), txns in invest_map.items():
        print("➡ Processing %s / %s (%d txns)" %(inv_type, name, len(txns)))
        intr = interest_map[(inv_type, name)]
        interest_in = intr["in"]
        interest_out = intr["out"]

        if inv_type in ("MUTUALFUND", "STOCK"):
            # NAV exact match required
            nav_val = nav_map.get(name)
            if nav_val is None:
                raise ValueError(f"NAV not found for fund '{name}'. Aborting update_savings.")
            res = calc_mutualfund_fifo(name, txns, nav_val, interest_in, interest_out)
        elif inv_type in ("FD"):
            res = calc_fd(name, txns, interest_in, interest_out)
        elif inv_type in ('PROVIDENTFUND'):
            res = calc_pf(name, txns, interest_in, interest_out)
        elif inv_type in ("RD", "LIC"):
            res = calc_rd_lic(name, txns, interest_in, interest_out)
        elif inv_type in ("BONDS"):
            res = calc_bonds(name, txns, interest_in, interest_out)
        else:
            print("Skipping unsupported type '%s' for '%s' (implement later)" %(inv_type, name))
            continue

        # write Savings row
        s = Savings(
            user_id=user_id,
            name=name,
            type=inv_type,
            t_buy=res["t_buy"],
            t_sell=res["t_sell"],
            profit_booked=res["profit_booked"],
            current_invested=res["current_invested"],
            current_value=res["current_value"],
            profit_loss=res["profit_loss"],
            return_percentage=res["return_percentage"]
        )
        db.add(s)
        print("  ✔ Saved: t_buy=%s, t_sell=%s, profit_booked=%s, rem_units=%s, curr_inv=%s, curr_val=%s" % (
        res["t_buy"], res["t_sell"], res["profit_booked"], res.get("remaining_units"), res["current_invested"], res["current_value"],))


    db.commit()
    print("✅ Completed update_savings for user_id=%s" %(user_id))


def calc_mutualfund_fifo(name, txns, current_nav: Decimal, interest_in: Decimal, interest_out: Decimal):
    """
    FIFO calculation for MUTUALFUND / STOCK:
    - txns must be ordered by time (we used Invest.id ordering when fetching)
    - returns dict with keys used in Savings
    NOTES:
    - profit_booked = interest_in - interest_out
    - current_invested = cost of remaining units (computed from FIFO queue)
    - t_buy = total cash spent on buys (sum of BUY.cost)
    - t_sell = total cash received on sells (sum of SELL.cost)
    """
    t_buy = Decimal(0)
    t_sell = Decimal(0)
    fifo_queue = []          # list of [units:Decimal, buy_price_per_unit:Decimal]
    remaining_units = Decimal(0)

    for txn in txns:
        units = Decimal(str(txn.units or 0))
        cost = Decimal(str(txn.cost or 0))

        if txn.type_of_order.upper() == "BUY":
            # price per unit guard against zero units
            price_per_unit = (cost / units) if units != 0 else Decimal(0)
            fifo_queue.append([units, price_per_unit])
            t_buy += cost
            remaining_units += units

        elif txn.type_of_order.upper() == "SELL":
            t_sell += cost
            sell_units = units
            sell_cost_total = Decimal(0)
            remaining_units -= units

            # FIFO consume
            while sell_units > 0 and fifo_queue:
                buy_units, buy_price = fifo_queue[0]
                if buy_units <= sell_units:
                    sell_cost_total += buy_units * buy_price
                    sell_units -= buy_units
                    fifo_queue.pop(0)
                else:
                    sell_cost_total += sell_units * buy_price
                    fifo_queue[0][0] = buy_units - sell_units
                    sell_units = Decimal(0)

    # current_invested is cost of remaining units in FIFO queue
    current_invested = sum((u * p for u, p in fifo_queue), Decimal(0))
    current_value = remaining_units * current_nav
    profit_booked = (Decimal(interest_in or 0) - Decimal(interest_out or 0))
    profit_loss = current_value - current_invested

    return {
        "t_buy": t_buy,
        "t_sell": t_sell,
        "profit_booked": profit_booked,
        "current_invested": round(current_invested, 2),
        "current_value": round(current_value, 2),
        "profit_loss": round(profit_loss, 2),
        "return_percentage": ((profit_loss / current_invested) * Decimal(100)) if current_invested != 0 else Decimal(0),
        "remaining_units": remaining_units
    }

from datetime import date

def calc_fd(name, txns, interest_in: Decimal, interest_out: Decimal):
    """
    Calculates FD/RD savings metrics.
    - For closed FDs: t_sell and profit_booked from transactions + interest table
    - For ongoing FDs: current_invested from principal, current_value = principal + accrued interest
    - No remaining_units because FDs don't have units
    """
    t_buy = Decimal(0)   # Total principal invested
    t_sell = Decimal(0)  # Total maturity amount withdrawn
    current_invested = Decimal(0)
    current_value = Decimal(0)

    # Identify closed vs ongoing
    on_going = True
    for txn in txns:
        cost = Decimal(str(txn.cost or 0))
        if txn.type_of_order.upper() == "BUY":
            t_buy += cost
        elif txn.type_of_order.upper() == "SELL":
            t_sell += cost
            on_going = False

    if on_going:
        parts = name.split("_")
        if len(parts) != 5:
            raise ValueError(f"Invalid FD name format: {name}")
        type_, principal_str, rate_str, start_str, maturity_str = parts
        principal = Decimal(principal_str)
        rate = Decimal(rate_str) / Decimal(100)  # % to decimal
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        days_elapsed = (today - start_date).days
        accrued_interest = (principal * rate * Decimal(days_elapsed) / Decimal(365)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        current_invested = t_buy
        current_value = current_invested + accrued_interest

    profit_booked = Decimal(interest_in or 0) - Decimal(interest_out or 0)
    profit_loss = current_value - current_invested

    return {
        "t_buy": round(t_buy, 2),
        "t_sell": round(t_sell, 2),
        "profit_booked": round(profit_booked, 2),
        "current_invested": round(current_invested, 2),
        "current_value": round(current_value, 2),
        "profit_loss": round(profit_loss, 2),
        "return_percentage": ((profit_loss / current_invested) * Decimal(100))
                             if current_invested != 0 else Decimal(0)
    }


def calc_pf(name, txns, interest_in: Decimal, interest_out: Decimal):
    """
    Calculates PF savings metrics.
    - t_buy = sum of contributions (BUY)
    - t_sell = sum of withdrawals (SELL)
    - profit_booked comes from Interest table (even if reinvested)
    - current_invested = t_buy - t_sell
    - current_value = current_invested + profit_booked
    """
    t_buy = Decimal(0)
    t_sell = Decimal(0)
    profit_booked = Decimal(0)
    current_invested = Decimal(0)
    
    for txn in txns:
        cost = Decimal(str(txn.cost or 0))
        if txn.type_of_order.upper() == "BUY":
            t_buy += cost
        elif txn.type_of_order.upper() == "SELL":
            t_sell += cost

    diff = t_buy - t_sell
    if diff >= 0:
        current_invested = diff
    else:
        profit_booked = abs(diff)
    current_value = current_invested + (Decimal(interest_in or 0) - Decimal(interest_out or 0))
 
    
    profit_loss = current_value - current_invested

    return {
        "t_buy": round(t_buy, 2),
        "t_sell": round(t_sell, 2),
        "profit_booked": round(profit_booked, 2),
        "current_invested": round(current_invested, 2),
        "current_value": round(current_value, 2),
        "profit_loss": round(profit_loss, 2),
        "return_percentage": round((profit_loss / current_invested) * Decimal(100), 2) if current_invested != 0 else Decimal(0)
    }

def calc_rd_lic(name, txns, interest_in: Decimal, interest_out: Decimal):
    """
    Calculates RD/LIC savings metrics where interest is credited to bank
    (not reinvested), principal returned at maturity or sell.

    - t_buy = total principal deposited
    - t_sell = total principal withdrawn/matured
    - profit_booked = net interest already credited (interest_in - interest_out)
    - current_invested = principal still invested (t_buy - t_sell)
    - current_value = current_invested (since interest not reinvested)
    """
    t_buy = Decimal(0)
    t_sell = Decimal(0)
    current_invested = Decimal(0)
    current_value = Decimal(0)
    profit_booked = Decimal(interest_in or 0) - Decimal(interest_out or 0)
    on_going = True

    for txn in txns:
        cost = Decimal(str(txn.cost or 0))
        if txn.type_of_order.upper() == "BUY":
            t_buy += cost
        elif txn.type_of_order.upper() == "SELL":
            t_sell += cost
            on_going = False

    if on_going:
        current_invested = t_buy
        profit_booked = Decimal(0)
        current_value = current_invested + Decimal(interest_in or 0) - Decimal(interest_out or 0)
        profit_loss = current_value - current_invested

    return {
        "t_buy": round(t_buy, 2),
        "t_sell": round(t_sell, 2),
        "profit_booked": round(profit_booked, 2),
        "current_invested": round(current_invested, 2),
        "current_value": round(current_value, 2),
        "profit_loss": round(profit_loss, 2),
        "return_percentage": Decimal(0) if current_invested == 0 else
            round((profit_booked / t_buy) * Decimal(100), 2)
    }

def calc_bonds(name, txns, interest_in: Decimal, interest_out: Decimal):
    """
    Calculates Bonds savings metrics where interest is credited to bank
    (not reinvested), principal returned at maturity or sell.

    - t_buy = total principal deposited
    - t_sell = total principal withdrawn/matured
    - profit_booked = net interest already credited (interest_in - interest_out)
    - current_invested = principal still invested (t_buy - t_sell)
    - current_value = current_invested (since interest not reinvested)
    """
    t_buy = Decimal(0)
    t_sell = Decimal(0)

    for txn in txns:
        cost = Decimal(str(txn.cost or 0))
        if txn.type_of_order.upper() == "BUY":
            t_buy += cost
        elif txn.type_of_order.upper() == "SELL":
            t_sell += cost

    current_invested = t_buy - t_sell
    profit_booked = Decimal(interest_in or 0) - Decimal(interest_out or 0)
    current_value = current_invested
    profit_loss = current_value - current_invested

    return {
        "t_buy": round(t_buy, 2),
        "t_sell": round(t_sell, 2),
        "profit_booked": round(profit_booked, 2),
        "current_invested": round(current_invested, 2),
        "current_value": round(current_value, 2),
        "profit_loss": round(profit_loss, 2),
        "return_percentage": Decimal(0) if current_invested == 0 else
            round((profit_booked / t_buy) * Decimal(100), 2)
    }

def calc_bank(name, bank_balance, interest_in: Decimal, interest_out: Decimal):
    t_buy = Decimal(0)
    t_sell = Decimal(0)
    current_invested = bank_balance
    profit_booked = Decimal(interest_in or 0) - Decimal(interest_out or 0)
    current_value = current_invested
    profit_loss = current_value - current_invested

    return {
        "t_buy": round(t_buy, 2),
        "t_sell": round(t_sell, 2),
        "profit_booked": round(profit_booked, 2),
        "current_invested": round(current_invested, 2),
        "current_value": round(current_value, 2),
        "profit_loss": round(profit_loss, 2)
    }

