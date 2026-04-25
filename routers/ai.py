from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
from auth import require_session
from database import get_db
from ml.detector import ai_detect

router = APIRouter(tags=["ai"], dependencies=[Depends(require_session)])


@router.post("/ai-detect", summary="AI 異常検知（Isolation Forest + AutoEncoder）")
def ai_detect_endpoint(max_epochs: int = 300, db: Session = Depends(get_db)):
    """audit_logs を機械学習モデルで解析し、異常な IP アドレスを検出する。"""
    logs = db.query(models.AuditLog).all()
    if not logs:
        return {"total_ips": 0, "anomaly_count": 0, "anomalies": [], "results": []}
    return ai_detect(logs, max_epochs=max_epochs)
