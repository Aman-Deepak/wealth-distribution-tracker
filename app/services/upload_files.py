from sqlalchemy.orm import Session
from datetime import  datetime, date
from app.services.config import get_config_last_updated_date, update_config_date
from app.services.expense import process_expense_file
from app.services.income import process_financial_data_file
from app.services.invest import process_mutualfund_file
from app.services.summary import update_monthly_distributions, update_yearly_distributions, update_savings
from app.services.recon import reconcile_bank
from app.db.models import UploadHistory
import os
from typing import Optional
from fastapi import UploadFile, File, HTTPException
from app.services.config import *


def upload_file(db: Session, user_id: int, file: UploadFile = File(...)):
    try:
        filename = file.filename
        file_ext = filename.split(".")[-1].lower()
        if file_ext not in ["xlsx", "xls", "csv"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Save the file
        contents = file.file.read()
        save_path = save_file(contents, filename, UPLOAD_DIR)

        # Detect file type
        file_type = detect_file_type(filename)
        if not file_type:
            raise HTTPException(status_code=400, detail="Unrecognized file name or format")
        
        # Record upload in history
        upload_history(db, user_id, filename, file_ext)

        # Trigger processing and DB insert
        process_uploaded_file(save_path, file_type, user_id, db)

        return {"message": f"File '{filename}' uploaded and processed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def upload_history(db: Session, user_id: int, filename: str, file_type: str, ):
    db_upload = UploadHistory(
        user_id=user_id,
        filename=filename,
        file_type=file_type,
        upload_time=datetime.utcnow(),
    )
    db.add(db_upload)
    db.commit()

def save_file(file: bytes, filename: str, upload_dir: str) -> str:
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        f.write(file)
    return filepath

def detect_file_type(filename: str) -> Optional[str]:
    """
    Detects file type strictly by filename (case-insensitive).
    Returns one of: 'expenses', 'financial_data', 'mutualfund'
    """
    name = filename.strip().lower()

    for file_type, names in ALLOWED_FILENAMES.items():
        if name in names:
            return file_type

    return None

def process_uploaded_file(filepath: str, file_type: str, user_id: int, db: Session):
    print(f"🧙 Processing file {filepath} of type {file_type}")
    Config = get_config_last_updated_date(db, user_id)

    if file_type == "expenses":
        fy_list = process_expense_file(filepath, user_id, db, Config.expense_last_updated_date)
        update_config_date(db, user_id, field_name="expense_last_updated_date", value=date.today())
    elif file_type == "financial_data":
        fy_list = process_financial_data_file(filepath, user_id, db, Config.financial_last_updated_date)
        update_config_date(db, user_id, field_name="financial_last_updated_date", value=date.today())
    elif file_type == "mutualfund":
        fy_list = process_mutualfund_file(filepath, user_id, db, Config.invest_last_updated_date)
        update_config_date(db, user_id, field_name="invest_last_updated_date", value=date.today())

    else:
        raise Exception(f"Unknown file type: {file_type}")

    print("🔁 Updating summaries after data insert")
    for fy in fy_list:
        update_monthly_distributions(user_id, db, fy)
        if file_type == "expenses":
            reconcile_bank(user_id, db, fiscal_year=fy)
    for fy in fy_list:
        update_yearly_distributions(user_id, db, fy)

    update_savings(user_id, db)

