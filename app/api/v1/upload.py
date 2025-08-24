from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.api.v1.auth import get_current_user, get_db
from app.db.models import UploadHistory
from app.services.upload_files import upload_file

router = APIRouter(prefix="/upload", tags=["Upload"])
@router.post("/")
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return upload_file(db, current_user.id, file)


@router.get("/history/")
def get_upload_history(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    history = db.query(UploadHistory).filter_by(user_id=current_user.id).order_by(UploadHistory.upload_time.desc()).all()
    return history