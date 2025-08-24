from decimal import Decimal
from datetime import datetime, date
import pandas as pd

def compute_financial_year(year: str, month: str) -> str:
    """
    Computes the financial year for a given calendar year and month.
    Returns in 'YYYY-YYYY' format.
    Assumes Indian financial year (April to March).
    """
    y, m = int(year), int(month)
    if m >= 4:
        return f"{y}-{y+1}"
    else:
        return f"{y-1}-{y}"

def get_current_financial_year(today: date = None) -> str:
    today = today or date.today()
    y, m = today.year, today.month
    if m >= 4:
        return f"{y}-{y+1}"
    else:
        return f"{y-1}-{y}"
    
def to_decimal(v) -> Decimal:
    if v is None:
        return Decimal("0")
    if isinstance(v, Decimal):
        return v
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")

def fmt_inr(n: float) -> str:
    return f"₹{n:,.2f}"

def get_today_datetime():
    return datetime.now()

def safe_sum(series) -> float:
    if series is None or len(series) == 0:
        return 0.0
    try:
        return float(pd.to_numeric(series, errors="coerce").fillna(0).sum())
    except Exception:
        return 0.0

def weighted_return_pct(df: pd.DataFrame, value_col="current_invested", ret_col="return_percentage") -> float:
    if df is None or df.empty or value_col not in df or ret_col not in df:
        return 0.0
    v = pd.to_numeric(df[value_col], errors="coerce").fillna(0.0)
    r = pd.to_numeric(df[ret_col], errors="coerce").fillna(0.0)
    if v.sum() == 0:
        return 0.0
    weights = v / v.sum()
    return float((weights * r).sum())


def weighted_invest_return_pct(df: pd.DataFrame) -> float:
    invested = float(df["CURRENT_INVESTED"].sum()) if "CURRENT_INVESTED" in df else 0.0
    profit_loss = float(df["PROFIT_LOSS"].sum()) if "PROFIT_LOSS" in df else 0.0
    if invested == 0:
        return 0.0
    return (profit_loss / invested) * 100.0

# -- Table helpers -----------------------------------------------------------
def df_to_html_table(df: pd.DataFrame, title: str = "", index: bool = False) -> str:
    if df is None or df.empty:
        return f"<h3>{title}</h3><p>No {title} data</p>"

    html_table = df.copy()
    for col in html_table.select_dtypes(include=["float", "int"]).columns:
        html_table[col] = html_table[col].map(lambda v: f"{v:,.2f}" if pd.notna(v) else "")

    table_html = html_table.to_html(
        index=index,
        classes="table table-sm table-bordered",
        border=0,
        justify="left",
        escape=False  # ✅ Render HTML badges
    )
    return f"<h3>{title}</h3>\n{table_html}"