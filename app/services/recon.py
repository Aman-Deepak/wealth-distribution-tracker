from sqlalchemy.orm import Session
from app.db.models import (
    MonthlyDistribution, Expense
)
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from sqlalchemy import func, and_,  cast, Integer
from app.utils.helper_functions import compute_financial_year, get_current_financial_year, get_today_datetime
from app.services.config import get_yearly_closing_balance
from app.services.summary import update_monthly_distributions


def expense_adjustment_positive(db: Session, user_id: int, fiscal_year: str, amount: float, input_date: date = None):
    current_fy = get_current_financial_year()
    today = get_today_datetime

    if input_date:
        # only that month
        fy = fiscal_year
        year, month = str(input_date.year), f"{input_date.month:02d}"
        per_amount = amount
        upsert_expense(db, user_id, fy, year, month, per_amount)
    else:
        if fiscal_year != current_fy:
            print(f"fiscal_year != current_fy spread across 12 months")
            per_amount = amount / 12
            for m in range(1, 13):
                year = fiscal_year.split("-")[0] if m >= 4 else fiscal_year.split("-")[1]
                upsert_expense(db, user_id, fiscal_year, str(year), f"{m:02d}", per_amount)
        else:
            print(f"fiscal_year == current_fy spread till current month")
            months = today.month - 3 if today.month >= 4 else today.month + 9
            per_amount = amount / months
            for m in range(4, today.month + 1 if today.month >= 4 else today.month+13):
                year_start = today.year if today.month >= 4 else today.year - 1
                year_end = year_start + 1
                year = str(year_start if m <= 12 else year_end)
                month = f"{m:02d}" if m <= 12 else f"{m-12:02d}"
                upsert_expense(db, user_id, fiscal_year, year, month, per_amount)

    db.commit()



# helper: months of an FY in order (Apr..Mar) -> list[(year_str, month_str)]
def _fy_months(fiscal_year: str):
    y1, y2 = map(int, fiscal_year.split("-"))
    months = []
    for m in range(4, 13):  # Apr..Dec in y1
        months.append((str(y1), f"{m:02d}"))
    for m in range(1, 4):   # Jan..Mar in y2
        months.append((str(y2), f"{m:02d}"))
    return months

# helper: months up to today for current FY (Apr..today)
def _fy_months_upto_today(fiscal_year: str):
    months = _fy_months(fiscal_year)
    if fiscal_year != get_current_financial_year():
        return months
    t = date(2025, 4, 11)  #date.today()
    cutoff = (str(t.year), f"{t.month:02d}")
    out = []
    for y, m in months:
        out.append((y, m))
        if (y, m) == cutoff:
            break
    return out

def expense_adjustment_negative(
    db: Session,
    user_id: int,
    fiscal_year: str,
    amount: float,
    input_date: date = None
):
    q = Decimal("0.0001")
    amt = Decimal(str(amount)).copy_abs()

    # --- 1) Validate available total ---
    total_available = (
        db.query(func.coalesce(func.sum(Expense.cost), 0))
        .filter(
            Expense.user_id == user_id,
            Expense.financial_year == fiscal_year,
            Expense.type == "PERSONAL",
            Expense.category == "ADJUSTED",
        )
        .scalar()
    ) or Decimal("0")

    if amt > total_available:
        raise ValueError(
            f"Insufficient ADJUSTED in {fiscal_year}. "
            f"Available={total_available}, required={amt}"
        )

    # --- 2) Decide the month set & order ---
    if input_date:
        # ensure the date belongs to the same FY
        from_y = str(input_date.year)
        from_m = f"{input_date.month:02d}"

        # your helper uses strings; keep it consistent:
        fy_of_date = compute_financial_year(from_y, from_m)
        if fy_of_date != fiscal_year:
            raise ValueError("input_date does not belong to the provided fiscal_year")

        ordered = _fy_months(fiscal_year)
        start = (from_y, from_m)
        try:
            idx = ordered.index(start)
        except ValueError:
            # If there is no explicit ADJUSTED record yet for that month,
            # index() still works because we're indexing month coordinates, not rows.
            idx = next(i for i, (yy, mm) in enumerate(ordered) if yy == from_y and mm == from_m)
        # start from input month, go to end, then wrap to the beginning
        months_to_process = ordered[idx:] + ordered[:idx]
        greedy = True
    else:
        months_to_process = (
            _fy_months_upto_today(fiscal_year) if fiscal_year == _current_fy()
            else _fy_months(fiscal_year)
        )
        greedy = False

    # --- 3) Load existing ADJUSTED expenses for the FY into a map ---
    rows = (
        db.query(Expense)
        .filter(
            Expense.user_id == user_id,
            Expense.financial_year == fiscal_year,
            Expense.type == "PERSONAL",
            Expense.category == "ADJUSTED",
        )
        .all()
    )
    exp_map = {(e.year, e.month): e for e in rows}

    remaining = amt

    if greedy:
        # Case A: date passed -> carry forward greedily across FY (with wrap)
        for y, m in months_to_process:
            if remaining <= 0:
                break
            e = exp_map.get((y, m))
            if not e or e.cost is None:
                continue
            avail = Decimal(e.cost)
            take = min(avail, remaining)
            e.cost = (avail - take).quantize(q, rounding=ROUND_HALF_UP)
            remaining -= take

    else:
        # Case B: no date -> equalized deduction with carry-forward
        # Build pool of months that currently have > 0 to deduct from
        pool = []
        for y, m in months_to_process:
            e = exp_map.get((y, m))
            avail = Decimal(e.cost) if e and e.cost is not None else Decimal("0")
            if avail > 0:
                pool.append([y, m, e, avail])

        # Iteratively distribute equally; months that hit 0 drop out
        while remaining > 0 and pool:
            per = (remaining / Decimal(len(pool))).quantize(q, rounding=ROUND_HALF_UP)
            if per == 0:
                # avoid getting stuck on rounding
                per = remaining / Decimal(len(pool))

            new_pool = []
            for y, m, e, avail in pool:
                take = min(avail, per, remaining)
                e.cost = (Decimal(e.cost) - take).quantize(q, rounding=ROUND_HALF_UP)
                remaining -= take
                new_avail = avail - take
                if new_avail > 0:
                    new_pool.append([y, m, e, new_avail])
            pool = new_pool

        # tiny rounding dust fallback
        if remaining > 0 and pool:
            # subtract tiny remainder from the first month that can take it
            y, m, e, avail = pool[0]
            take = min(avail, remaining)
            e.cost = (Decimal(e.cost) - take).quantize(q, rounding=ROUND_HALF_UP)
            remaining -= take

    if remaining > 0:
        # Should not happen because of the up-front validation, unless race-condition updates
        raise RuntimeError(f"Failed to allocate full deduction. Remaining={remaining}")

    db.commit()



def upsert_expense(db: Session, user_id: int, fiscal_year: str, year: str, month: str, amount: float):
    """Insert or update Expense row for PERSONAL/ADJUSTED."""
    from app.db.models import Expense

    expense = db.query(Expense).filter(
        and_(
            Expense.user_id == user_id,
            Expense.financial_year == fiscal_year,
            Expense.year == year,
            Expense.month == month,
            Expense.type == "PERSONAL",
            Expense.category == "ADJUSTED",
        )
    ).first()

    if expense:
         expense.cost = expense.cost + amount
    else:
        new_expense = Expense(
            user_id=user_id,
            financial_year=fiscal_year,
            year=year,
            month=month,
            day="01",  # default day
            type="PERSONAL",
            category="ADJUSTED",
            cost=amount,
        )
        db.add(new_expense)


def reconcile_bank(user_id: int, db: Session, input_date: date = None, fiscal_year: str = None):
    """
    Reconcile bank balance:
    1. Compare configs.bank_balance with calculated monthly_distribution bank sum
    2. Insert/update ADJUSTED expenses accordingly
    """
    # ---- Step 1: Fetch current bank balance ----
    if input_date:
        fiscal_year = compute_financial_year(input_date.year, input_date.month) 
    current_bank_balance = get_yearly_closing_balance(user_id, db, fiscal_year).closing_balance
    print(f"{fiscal_year} closing bank balance: {current_bank_balance}")

    # ---- Step 2: Get calculated bank balance from MonthlyDistribution ----
    query = db.query(func.coalesce(func.sum(MonthlyDistribution.bank), 0))\
            .filter(MonthlyDistribution.user_id == user_id)
    target_start_year = int(fiscal_year.split("-")[0])
    fy_start_expr = cast(func.substr(MonthlyDistribution.financial_year, 1, 4), Integer)
    query = query.filter(fy_start_expr <= target_start_year)
    calculated_bank_balance = query.scalar() or Decimal("0.0")
    print(f"{fiscal_year} calculated closing bank balance: {calculated_bank_balance}")


    # ---- Step 3: Compare ----
    diff = calculated_bank_balance - current_bank_balance

    if diff == 0:
        print("✅ Reconciliation passed. No adjustment needed.")
        return "Reconciliation passed"
    # Case A: current < calculated → Need to add expense(s)
    elif diff > 0:
        print(f"current < calculated → Need to add expense(s) {diff}")
        expense_adjustment_positive(db, user_id, fiscal_year, diff, input_date)
        update_monthly_distributions(user_id, db, fiscal_year)
    # Case B: current > calculated → Need to reduce/adjust expense
    else:
        print(f"current > calculated → Need to reduce/adjust expense {diff}")
        expense_adjustment_negative(db, user_id, fiscal_year, abs(diff), input_date)
        update_monthly_distributions(user_id, db, fiscal_year)
    print("♻️ Bank reconciliation completed.")
    return "Reconciliation completed"

