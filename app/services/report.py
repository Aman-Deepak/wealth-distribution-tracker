from app.services.invest import fetch_invest_data
from app.services.expense import fetch_expense_data
from app.services.summary import fetch_savings_data, fetch_yearly_distribution_data
from app.services.income import fetch_income_data
from app.services.loan import fetch_loan_data
from app.services.insights import *
from app.services.charts import *
from app.services.tables import *
from app.services.config import *
from jinja2 import Environment, FileSystemLoader
import json

# ---------- Rendering ----------
def render_expense_report(context: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("expense_report.html")
    return template.render(**context)

def render_invest_report(context: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("invest_report.html")
    return template.render(**context)

def render_financial_report(context: dict) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("financial_report.html")
    return template.render(**context)


# ---------- Summary ----------------------------------
def expense_summary_card(summary_data: dict) -> list[dict]:
    return [
        {"label": "Total Expenses", "value": summary_data["TOTAL_EXPENSES"]},
        {"label": "Average Monthly Expense", "value": summary_data["AVG_MONTHLY_EXPENSE"]},
        {"label": "Highest Expense Month", "value": summary_data["HIGHEST_EXPENSE_MONTH"]},
        {"label": "Lowest Expense Month", "value": summary_data["LOWEST_EXPENSE_MONTH"]},
    ]

def investment_summary_card(summary_data: dict) -> list[dict]:
    return [
        {"label": "Total Investments", "value": summary_data["TOTAL_INVESTED"]},
        {"label": "Total Current Value", "value": summary_data["TOTAL_VALUE"]},
        {"label": "Total Profit/Loss", "value": summary_data["TOTAL_PNL"]},
        {"label": "Overall Return %", "value": summary_data["WEIGHTED_RETURN"]},
        {"label": "Profit Booked", "value": summary_data["PROFIT_BOOKED_SUM"]},
    ]

def financial_summary_card(summary_data: dict) -> list[dict]:
    return [
        {"label": "Total Wealth", "value": summary_data["TOTAL_WEALTH"]},
        {"label": "Total Liquid Wealth", "value": summary_data["LIQUID_WEALTH"]},
        {"label": "Total Loan", "value": summary_data["TOTAL_LOANS"]},
        {"label": "Current Bank Balance", "value": summary_data["BANK_BALANCE"]},
    ]


# ---------- Insight Sections ----------

def expense_insight_dict(insights: dict) -> dict:
    return {
        "HIGHEST_CATEGORY": insights.get("HIGHEST_CATEGORY", "N/A"),
        "HIGHEST_TYPE": insights.get("HIGHEST_TYPE", "N/A"),
        "AVG_MONTHLY_EXPENSE": insights.get("AVG_MONTHLY_EXPENSE", "N/A"),
        "YOY_EXPENSE": insights.get("YOY_EXPENSE", "N/A"),
    }

def investment_insight_dict(insights: dict) -> dict:
    return {
        "TOP_ASSET": insights.get("TOP_ASSET", "N/A"),
        "BOTTOM_ASSET": insights.get("BOTTOM_ASSET", "N/A"),
        "LARGEST_HOLDING": insights.get("LARGEST_HOLDING", "N/A"),
        "TOP_RETIREMENT_ASSET": insights.get("TOP_RETIREMENT_ASSET", "N/A"),
        "YOY_INVEST": insights.get("YOY_INVEST", "N/A"),
        "CONCENTRATION_RISK": insights.get("CONCENTRATION_RISK", "N/A"),
    }

def financial_insight_dict(insights: dict) -> dict:
    return {
        "PORTFOLIO_RETURN": insights.get("PORTFOLIO_RETURN", "N/A"),
        "RETIREMENT_RETURN": insights.get("RETIREMENT_RETURN", "N/A"),
        "AVG_MONTHLY_EXPENSE": insights.get("AVG_MONTHLY_EXPENSE", "N/A"),
        "YOY_EXPENSE": insights.get("YOY_EXPENSE", "N/A"),
        "YOY_INVEST": insights.get("YOY_INVEST", "N/A"),
        "CONCENTRATION_RISK": insights.get("CONCENTRATION_RISK", "N/A"),
        "TOP_ASSET": insights.get("TOP_ASSET", "N/A"),
        "LARGEST_HOLDING": insights.get("LARGEST_HOLDING", "N/A"),
    }



# ---------- report generator ----------
def generate_expense_report(user_id: int, db: Session) -> str:
    df = fetch_expense_data(user_id, db)
    summary_card_data = calculate_summary(exp_df=df)
    summary_cards = expense_summary_card(summary_card_data)
    insight_data = calculate_insights(exp_df=df)
    insights = expense_insight_dict(insight_data)
    pie_chart = prepare_expense_type_pie_chart(df)
    fiscal_chart = prepare_expense_fiscal_stacked_chart(df)
    monthly_trend = prepare_expense_monthly_trend(df)
    expense_table_html = generate_expense_table(df)

    context = {
        "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "summary": summary_cards,
        "insights": insights,
        "pie_chart_data": json.dumps(pie_chart, ensure_ascii=False),
        "fiscal_type_stacked_data": json.dumps(fiscal_chart, ensure_ascii=False),
        "monthly_trend_data": json.dumps(monthly_trend, ensure_ascii=False),
        "expense_table": expense_table_html,
    }

    html_content = render_expense_report(context)

    filename = f"expense_report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(GENERATED_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filename

def generate_invest_report(user_id: int, db: Session) -> str:
    inv_df = fetch_invest_data(user_id, db)
    s_df = fetch_savings_data(user_id, db)

    summary_card_data = calculate_summary(sav_df=s_df)
    summary_cards = investment_summary_card(summary_card_data)
    insight_data = calculate_insights(sav_df=s_df, inv_df=inv_df)
    insights = investment_insight_dict(insight_data)

    pie_invest, pie_portfolio, pie_retirement = prepare_saving_pie_charts(s_df)
    monthly_trend = prepare_invest_monthly_trend(inv_df)
    savings_table_html = generate_savings_table(s_df)

    context = {
        "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "summary_cards": summary_cards,
        "insights": insights,
        "pie_invest_data": json.dumps(pie_invest, ensure_ascii=False),
        "pie_portfolio_data": json.dumps(pie_portfolio, ensure_ascii=False),
        "pie_retirement_data": json.dumps(pie_retirement, ensure_ascii=False),
        "monthly_buysell_data": json.dumps(monthly_trend, ensure_ascii=False),
        "savings_table": savings_table_html,
    }

    html = render_invest_report(context)

    filename = f"invest_report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(GENERATED_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filename



def generate_financial_report(user_id: int, db: Session) -> str:
    # Fetch data
    exp_df = fetch_expense_data(user_id=user_id, db=db)
    income_df = fetch_income_data(user_id=user_id, db=db)
    sav_df = fetch_savings_data(user_id=user_id, db=db)
    inv_df = fetch_invest_data(user_id=user_id, db=db)
    yearly_df = fetch_yearly_distribution_data(user_id=user_id, db=db)
    loans_df = fetch_loan_data(user_id=user_id, db=db)
    bank_balance = get_yearly_closing_balance(user_id=user_id, db=db).closing_balance

    summary_card_data = calculate_summary(exp_df=exp_df, sav_df=sav_df, loans_df=loans_df, bank_balance=bank_balance)
    summary_cards = financial_summary_card(summary_card_data)
    insight_data = calculate_insights(exp_df=exp_df, sav_df=sav_df, inv_df=inv_df)
    insights = financial_insight_dict(insight_data)

    # Charts
    expense_pie_data = prepare_expense_type_pie_chart(exp_df)
    expense_fy_data = prepare_expense_fiscal_stacked_chart(exp_df)
    invest_pie_data, portfolio_pie_data, retirement_pie_data = prepare_saving_pie_charts(sav_df)

    # Monthly trends
    monthly_trend_data = monthly_trends(exp_df, inv_df, income_df, loans_df, bank_balance)

    # Tables
    expense_table_html = generate_expense_table(exp_df)
    savings_table_html = generate_savings_table(sav_df)
    yearly_table_html = generate_yearly_distribution_table(yearly_df)

    context = {
        "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "summary_cards": summary_cards,
        "insights": insights,
        "expense_pie_data": json.dumps(expense_pie_data, ensure_ascii=False),
        "expense_fy_data": json.dumps(expense_fy_data, ensure_ascii=False),
        "invest_pie_data": json.dumps(invest_pie_data, ensure_ascii=False),
        "portfolio_pie_data": json.dumps(portfolio_pie_data, ensure_ascii=False),
        "retirement_pie_data": json.dumps(retirement_pie_data, ensure_ascii=False),
        "monthly_trend_data": json.dumps(monthly_trend_data, ensure_ascii=False),
        "yearly_table": yearly_table_html,
        "expense_table": expense_table_html,
        "savings_table": savings_table_html,
    }

    html = render_financial_report(context)

    filename = f"financial_report_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(GENERATED_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filename
