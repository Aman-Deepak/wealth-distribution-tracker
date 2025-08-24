import pandas as pd
from datetime import timedelta
from app.utils.helper_functions import fmt_inr, get_today_datetime, safe_sum, weighted_invest_return_pct, weighted_return_pct
from app.services.config import *

# ---------- Summary & Insights ----------
def calculate_summary(exp_df: pd.DataFrame = None, sav_df: pd.DataFrame = None, loans_df: pd.DataFrame = None, bank_balance: str = None):
    print("Generate summary cards data.")

    # Default values
    summary = {
        "TOTAL_EXPENSES": "N/A",
        "AVG_MONTHLY_EXPENSE": "N/A",
        "HIGHEST_EXPENSE_MONTH": "N/A",
        "LOWEST_EXPENSE_MONTH": "N/A",
        "TOTAL_INVESTED": "N/A",
        "TOTAL_VALUE": "N/A",
        "TOTAL_PNL": "N/A",
        "WEIGHTED_RETURN": "N/A",
        "PROFIT_BOOKED_SUM": "N/A",
        "TOTAL_WEALTH": "N/A",
        "LIQUID_WEALTH": "N/A",
        "TOTAL_LOANS": "N/A",
        "BANK_BALANCE": "N/A",
    }

    if exp_df is not None and not exp_df.empty:
        summary["TOTAL_EXPENSES"] = fmt_inr(safe_sum(exp_df.get("COST")))
        summary["AVG_MONTHLY_EXPENSE"] = fmt_inr(round(exp_df.groupby(exp_df["DATE"].dt.to_period("M"))["COST"].sum().mean(), 2))
        summary["HIGHEST_EXPENSE_MONTH"] = exp_df.groupby(exp_df["DATE"].dt.strftime("%B %Y"))["COST"].sum().idxmax()
        summary["LOWEST_EXPENSE_MONTH"] = exp_df.groupby(exp_df["DATE"].dt.strftime("%B %Y"))["COST"].sum().idxmin()

    if sav_df is not None and not sav_df.empty:
        summary["TOTAL_INVESTED"] = fmt_inr(safe_sum(sav_df.get("CURRENT_INVESTED")))
        summary["TOTAL_VALUE"] = fmt_inr(safe_sum(sav_df.get("CURRENT_VALUE")))
        summary["TOTAL_PNL"] = fmt_inr(safe_sum(sav_df.get("PROFIT_LOSS")))
        summary["WEIGHTED_RETURN"] = f"{fmt_inr(weighted_invest_return_pct(sav_df))}%"
        summary["PROFIT_BOOKED_SUM"] = fmt_inr(safe_sum(sav_df.get("PROFIT_BOOKED")))
        summary["TOTAL_WEALTH"] = fmt_inr(safe_sum(sav_df.get("CURRENT_VALUE")))
        summary["LIQUID_WEALTH"] = fmt_inr(safe_sum(sav_df[sav_df["TYPE"].isin({"BANK","MUTUALFUND","RD"})]["CURRENT_VALUE"]))

    if loans_df is not None and not loans_df.empty:
        summary["TOTAL_LOANS"] = fmt_inr(safe_sum(loans_df.get("LOAN_AMOUNT")) - safe_sum(loans_df.get("LOAN_REPAYMENT")))

    if bank_balance:
        summary["BANK_BALANCE"] = fmt_inr(bank_balance)

    return summary



def calculate_invest_yoy_growth(inv_df) -> str:
    if not inv_df:
        return "N/A"

    today = get_today_datetime()
    end_curr = today
    start_curr = today - timedelta(days=365)
    end_prev = start_curr
    start_prev = start_curr - timedelta(days=365)

    curr_mask = (inv_df["DATE"] > start_curr) & (inv_df["DATE"] <= end_curr)
    prev_mask = (inv_df["DATE"] > start_prev) & (inv_df["DATE"] <= end_prev)

    curr_buys = float(inv_df[curr_mask & (inv_df["TYPE_OF_ORDER"] == "BUY")]["COST"].sum())
    prev_buys = float(inv_df[prev_mask & (inv_df["TYPE_OF_ORDER"] == "BUY")]["COST"].sum())

    if prev_buys > 0:
        return f"{((curr_buys - prev_buys) / prev_buys) * 100:.2f}%"
    return "N/A"


def calculate_insights(exp_df: pd.DataFrame = None, sav_df: pd.DataFrame = None, inv_df=None) -> dict:
    print("Generate consolidated insights (expense + investment + financial).")

    insights = {
        # Expense
        "HIGHEST_CATEGORY": "N/A",
        "HIGHEST_TYPE": "N/A",
        "AVG_MONTHLY_EXPENSE": "N/A",
        "YOY_EXPENSE": "N/A",

        # Investment
        "TOP_ASSET": "N/A",
        "BOTTOM_ASSET": "N/A",
        "LARGEST_HOLDING": "N/A",
        "TOP_RETIREMENT_ASSET": "N/A",
        "YOY_INVEST": "N/A",
        "CONCENTRATION_RISK": "N/A",

        # Financial
        "PORTFOLIO_RETURN": "N/A",
        "RETIREMENT_RETURN": "N/A",
    }

    # ---------- Expense Insights ----------
    if exp_df is not None and not exp_df.empty:
        try:
            insights["HIGHEST_CATEGORY"] = exp_df.groupby("CATEGORY")["COST"].sum().idxmax()
            insights["HIGHEST_TYPE"] = exp_df.groupby("TYPE")["COST"].sum().idxmax()

            m = exp_df.groupby(exp_df["DATE"].dt.to_period("M"))["COST"].sum()
            if not m.empty:
                insights["AVG_MONTHLY_EXPENSE"] = fmt_inr(float(m.mean()))

            fy_totals = exp_df.groupby("FISCAL_YEAR")["COST"].sum().sort_index()
            if len(fy_totals) >= 2:
                latest, prev = fy_totals.iloc[-1], fy_totals.iloc[-2]
                if prev:
                    insights["YOY_EXPENSE"] = f"{((latest - prev) / prev) * 100:.2f}%"
        except Exception:
            pass

    # ---------- Investment Insights ----------
    if sav_df is not None and not sav_df.empty:
        try:
            if "RETURN_PERCENTAGE" in sav_df.columns:
                s_nonnull = sav_df[sav_df["RETURN_PERCENTAGE"].notna()]
                if not s_nonnull.empty:
                    top_row = s_nonnull.sort_values("RETURN_PERCENTAGE", ascending=False).iloc[0]
                    bottom_row = s_nonnull.sort_values("RETURN_PERCENTAGE", ascending=True).iloc[0]
                    insights["TOP_ASSET"] = f"{top_row['NAME']} ({top_row['RETURN_PERCENTAGE']:.2f}%)"
                    insights["BOTTOM_ASSET"] = f"{bottom_row['NAME']} ({bottom_row['RETURN_PERCENTAGE']:.2f}%)"

            lr = sav_df.sort_values("CURRENT_VALUE", ascending=False).iloc[0]
            insights["LARGEST_HOLDING"] = f"{lr['NAME']} ({fmt_inr(lr['CURRENT_VALUE'])})"

            retire_df = sav_df[sav_df["TYPE"].str.upper().isin(RETIREMENT_SET)]
            if not retire_df.empty:
                rr = retire_df.sort_values("CURRENT_VALUE", ascending=False).iloc[0]
                insights["TOP_RETIREMENT_ASSET"] = f"{rr['NAME']} ({fmt_inr(rr['CURRENT_VALUE'])})"

            total_value = float(sav_df["CURRENT_VALUE"].sum())
            if total_value > 0:
                max_val = float(sav_df["CURRENT_VALUE"].max())
                insights["CONCENTRATION_RISK"] = f"{(max_val / total_value) * 100:.2f}%"

            insights["YOY_INVEST"] = calculate_invest_yoy_growth(inv_df)

            portfolio_return = weighted_return_pct(sav_df, "CURRENT_INVESTED", "RETURN_PERCENTAGE")
            insights["PORTFOLIO_RETURN"] = f"{portfolio_return:.2f}%"

            ret_df = sav_df[sav_df["TYPE"].isin(RETIREMENT_SET)]
            if not ret_df.empty:
                retirement_return = weighted_return_pct(ret_df, "CURRENT_INVESTED", "RETURN_PERCENTAGE")
                insights["RETIREMENT_RETURN"] = f"{retirement_return:.2f}%"
        except Exception:
            pass

    return insights
