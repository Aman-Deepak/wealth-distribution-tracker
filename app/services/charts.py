import pandas as pd
from datetime import datetime
from app.services.config import *

def prepare_expense_type_pie_chart(exp_df: pd.DataFrame) -> dict:
    print("Preparing Expense Type PIE Chart")
    type_totals = exp_df.groupby("TYPE")["COST"].sum()
    return {
        "labels": type_totals.index.tolist(),
        "datasets": [{"data": type_totals.values.tolist()}]
    }


def prepare_expense_fiscal_stacked_chart(exp_df: pd.DataFrame) -> dict:
    print("Preparing Expense Fiscal Stack Chart")
    fiscal_group = exp_df.groupby(["FISCAL_YEAR", "TYPE"])["COST"].sum().reset_index()
    fiscal_years = sorted(fiscal_group["FISCAL_YEAR"].unique())
    types = sorted(fiscal_group["TYPE"].unique())

    datasets = []
    for t in types:
        datasets.append({
            "label": t,
            "data": [float(fiscal_group[(fiscal_group["FISCAL_YEAR"] == fy) & 
                                        (fiscal_group["TYPE"] == t)]["COST"].sum() or 0)
                     for fy in fiscal_years]
        })

    return {"labels": fiscal_years, "datasets": datasets}


def prepare_expense_monthly_trend(exp_df: pd.DataFrame) -> dict:
    print("Preparing Expense Monthly Trend Chart")
    monthly_group = exp_df.groupby(exp_df["DATE"].dt.strftime("%Y-%m"))["COST"].sum().reset_index()
    return {
        "labels": monthly_group["DATE"].tolist(),
        "datasets": [{"label": "Expense", "data": monthly_group["COST"].round(2).tolist()}]
    }

def prepare_invest_monthly_trend(inv_df: pd.DataFrame) -> dict:
    print("Preparing Invest Monthly Trend Chart")
    
    # Correct empty check
    if inv_df.empty:
        return {"labels": [], "datasets": []}

    inv_df["YEAR_MONTH"] = pd.to_datetime(inv_df["DATE"]).dt.to_period("M").astype(str)
    
    buys = inv_df[inv_df["TYPE_OF_ORDER"] == "BUY"].groupby("YEAR_MONTH")["COST"].sum()
    sells = inv_df[inv_df["TYPE_OF_ORDER"] == "SELL"].groupby("YEAR_MONTH")["COST"].sum()

    all_months = sorted(set(buys.index).union(set(sells.index)))
    buy_vals = [float(buys.get(m, 0.0)) for m in all_months]
    sell_vals = [float(sells.get(m, 0.0)) for m in all_months]

    return {
        "labels": all_months,
        "datasets": [
            {"label": "BUY", "data": buy_vals},
            {"label": "SELL", "data": sell_vals},
        ]
    }


def prepare_saving_pie_charts(s_df: pd.DataFrame) -> tuple[dict, dict, dict]:
    print("Preparing Saving PIE Chart")
    invest_breakdown = s_df.groupby(s_df["TYPE"].str.upper())["CURRENT_VALUE"].sum().sort_values(ascending=False)
    pie_invest_data = {
        "labels": invest_breakdown.index.tolist(),
        "datasets": [{"label": "value", "data": [float(x) for x in invest_breakdown.values]}]
    }

    port_df = s_df[s_df["TYPE"].str.upper().isin(PORTFOLIO_TYPES)]
    portfolio_breakdown = port_df.groupby(port_df["TYPE"].str.upper())["CURRENT_VALUE"].sum().sort_values(ascending=False)
    pie_portfolio_data = {
        "labels": portfolio_breakdown.index.tolist(),
        "datasets": [{"label": "Value", "data": [float(x) for x in portfolio_breakdown.values]}]
    }

    retire_df = s_df[s_df["TYPE"].str.upper().isin(RETIREMENT_SET)]
    retire_breakdown = retire_df.groupby(retire_df["TYPE"].str.upper())["CURRENT_VALUE"].sum().sort_values(ascending=False)
    pie_retirement_data = {
        "labels": retire_breakdown.index.tolist(),
        "datasets": [{"label": "Value", "data": [float(x) for x in retire_breakdown.values]}]
    }

    return pie_invest_data, pie_portfolio_data, pie_retirement_data


def monthly_trends(exp_df, inv_df, income_df, loans_df, bank_balance):
    print("Preparing Financial Monthly Trend Chart")
    series = {}
    if not exp_df.empty:
        ex = exp_df.groupby(exp_df["DATE"].dt.to_period("M"))["COST"].sum()
        series["Expense"] = ex
    if not inv_df.empty:
        inv_df["YM"] = inv_df["DATE"].dt.to_period("M")
        buy = inv_df[inv_df["TYPE_OF_ORDER"]=="BUY"].groupby("YM")["COST"].sum()
        sell = inv_df[inv_df["TYPE_OF_ORDER"]=="SELL"].groupby("YM")["COST"].sum()
        if not buy.empty: series["BUY"] = buy
        if not sell.empty: series["SELL"] = sell
    if not income_df.empty:
        inc = income_df.groupby(income_df["DATE"].dt.to_period("M"))["AMOUNT"].sum()
        if not inc.empty: series["Income"] = inc
    if not loans_df.empty and loans_df["DATE"].notna().any():
        ln = loans_df.dropna(subset=["DATE"]).groupby(loans_df["DATE"].dt.to_period("M"))["LOAN_AMOUNT"].sum()
        if not ln.empty: series["Loan"] = ln
    if bank_balance > 0:
        bank_series = pd.Series({pd.Period(datetime.now().strftime("%Y-%m")): bank_balance})
        series["Bank"] = bank_series

    all_months = sorted({str(idx) for s in series.values() for idx in s.index})
    def vals(s): return [float(s.get(pd.Period(m), 0.0)) for m in all_months]
    datasets = [{"label": name, "data": vals(s)} for name, s in series.items()]
    monthly_trend_data = {"labels": all_months, "datasets": datasets}
    return monthly_trend_data
