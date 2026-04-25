from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from auth import require_session
from database import get_db
from schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_session)])


@router.post("", response_model=UserResponse, summary="ユーザー登録")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="このメールアドレスはすでに登録されています")
    db_user = models.User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    log = db.query(models.AuditLog).order_by(models.AuditLog.id.desc()).first()
    if log:
        log.user_id = db_user.id
        db.commit()
    return db_user


@router.get("", response_model=list[UserResponse], summary="ユーザー一覧")
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()
