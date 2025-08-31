from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.v1.auth import get_current_user, get_db
from app.schemas.tables import TableRequest
from app.services.tables import (
    generate_expense_table,
    generate_savings_table,
    generate_yearly_distribution_table,
)
from app.services.expense import fetch_expense_data
from app.services.summary import fetch_savings_data, fetch_yearly_distribution_data

router = APIRouter(prefix="/tables", tags=["Tables"])


@router.post("/data")
def get_table_data(
    req: TableRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user.id
    # Fetch dataframes
    exp_df = fetch_expense_data(user_id=user_id, db=db)
    sav_df = fetch_savings_data(user_id=user_id, db=db)
    yearly_df = fetch_yearly_distribution_data(user_id=user_id, db=db)

    try:
        if req.table_name == "expense_summary":
            html = generate_expense_table(exp_df)
            return {"html": html}

        if req.table_name == "savings_summary":
            html = generate_savings_table(sav_df)
            return {"html": html}

        if req.table_name == "yearly_distribution":
            html = generate_yearly_distribution_table(yearly_df)
            return {"html": html}

        raise HTTPException(404, f"Unknown table_name: {req.table_name}")

    except Exception as e:
        raise HTTPException(500, str(e))
