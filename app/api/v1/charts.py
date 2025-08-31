from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.v1.auth import get_current_user, get_db
from app.schemas.charts import ChartRequest
from app.services.charts import (
    prepare_expense_type_pie_chart,
    prepare_expense_fiscal_stacked_chart,
    prepare_expense_monthly_trend,
    prepare_invest_monthly_trend,
    prepare_saving_pie_charts,
    monthly_trends,
)
from app.services.expense import fetch_expense_data
from app.services.income import fetch_income_data
from app.services.loan import fetch_loan_data
from app.services.income import fetch_income_data
from app.services.config import get_yearly_closing_balance
from app.services.summary import fetch_savings_data
from app. services.invest import fetch_invest_data

router = APIRouter(prefix="/charts", tags=["Charts"])


@router.post("/data")
def get_chart_data(
    req: ChartRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user.id
    # Fetch dataframes
    exp_df = fetch_expense_data(user_id=user_id, db=db)
    sav_df = fetch_savings_data(user_id=user_id, db=db)
    loan_df = fetch_loan_data(user_id=user_id, db=db)
    invest_df = fetch_invest_data(user_id=user_id, db=db)
    inc_df = fetch_income_data(user_id=user_id, db=db)
    bank_balance = None
    try:
        bank_balance = get_yearly_closing_balance(user_id=user_id, db=db).closing_balance
    except:
        pass

    try:
        if req.chart_name == "expense_type_pie":
            return prepare_expense_type_pie_chart(exp_df)

        if req.chart_name == "expense_fiscal_stack":
            return prepare_expense_fiscal_stacked_chart(exp_df)

        if req.chart_name == "expense_monthly_trend":
            return prepare_expense_monthly_trend(exp_df)

        if req.chart_name == "invest_monthly_trend":
            return prepare_invest_monthly_trend(invest_df)

        if req.chart_name == "savings_pie":
            pie1, pie2, pie3 = prepare_saving_pie_charts(sav_df)
            return {"invest_breakdown": pie1, "portfolio_breakdown": pie2, "retirement_breakdown": pie3}

        if req.chart_name == "financial_monthly_trends":
            return monthly_trends(exp_df, invest_df, inc_df, loan_df, bank_balance)

        raise HTTPException(404, f"Unknown chart_name: {req.chart_name}")

    except Exception as e:
        raise HTTPException(500, str(e))
