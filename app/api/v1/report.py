import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.v1.auth import get_current_user, get_db
from app.services.report import generate_expense_report, generate_financial_report, generate_invest_report

GENERATED_DIR = "generated_reports"
os.makedirs(GENERATED_DIR, exist_ok=True)

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/generate/")
def generate_report(
    report_type: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a report (expense, invest, financial) for the current user.
    """
    report_type = report_type.lower()
    print(f"🧙 Processing generate report {report_type} of user {current_user.id}")
    if report_type not in ["expense", "invest", "financial"]:
        raise HTTPException(status_code=400, detail="Invalid report type")

    if report_type == "expense":
        filename = generate_expense_report(current_user.id, db)
    elif report_type == "invest":
        filename = generate_invest_report(current_user.id, db)
    else:
        filename = generate_financial_report(current_user.id, db)

    return {"message": f"{report_type.capitalize()} report generated", "filename": filename}

@router.get("/list/")
def list_reports():
    """
    List all generated reports.
    """
    reports = []
    for file in os.listdir(GENERATED_DIR):
        if file.endswith(".html"):
            reports.append({"filename": file, "path": os.path.join(GENERATED_DIR, file)})
    return reports

@router.get("/download/{filename}")
def download_report(filename: str):
    """
    Download a specific generated report.
    """
    file_path = os.path.join(GENERATED_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(file_path, media_type="text/html", filename=filename)
