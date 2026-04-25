import json
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
from auth import require_session
from database import get_db
from detectors.rules import run_all
from recommendations.engine import generate
from risk.scorer import compute
from schemas import AuditLogResponse, AuditFindingResponse, RiskScoreResponse

JST = timezone(timedelta(hours=9))

router = APIRouter(tags=["audit"], dependencies=[Depends(require_session)])


@router.get("/audit-logs", response_model=list[AuditLogResponse], summary="アクセスログ一覧")
def list_audit_logs(db: Session = Depends(get_db)):
    logs = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).all()
    return [
        AuditLogResponse(
            id=log.id,
            ip_address=log.ip_address,
            method=log.method,
            endpoint=log.endpoint,
            status_code=log.status_code,
            user_id=log.user_id,
            user_name=log.user.name if log.user else None,
            timestamp=log.timestamp.strftime("%Y-%m-%d %H:%M:%S JST") if log.timestamp else None,
        )
        for log in logs
    ]


@router.post("/run-audit", summary="監査エンジン実行")
def run_audit(db: Session = Depends(get_db)):
    """全ログを解析してリスク検出・スコアリング・推奨アクションを生成し DB に保存する。"""
    run_id = str(uuid.uuid4())
    now = datetime.now(JST).replace(tzinfo=None)

    logs = db.query(models.AuditLog).all()
    detections = run_all(logs)
    scores = compute(detections)
    recs = generate(detections)

    for d in detections:
        db.add(models.AuditFinding(
            run_id=run_id,
            rule_id=d.rule_id,
            risk_level=d.risk_level,
            user_id=d.user_id,
            ip_address=d.ip_address,
            description=d.description,
            recommendation=d.recommendation,
            urgency=d.urgency,
            score=d.score,
            evidence=json.dumps(d.evidence_log_ids),
            created_at=now,
        ))

    for s in scores:
        db.add(models.RiskScore(
            run_id=run_id,
            user_id=s.user_id,
            ip_address=s.ip_address,
            score=s.score,
            risk_level=s.risk_level,
            breakdown=json.dumps(s.breakdown),
            calculated_at=now,
        ))

    db.commit()

    return {
        "run_id": run_id,
        "findings": len(detections),
        "high": sum(1 for d in detections if d.risk_level == "high"),
        "medium": sum(1 for d in detections if d.risk_level == "medium"),
        "low": sum(1 for d in detections if d.risk_level == "low"),
        "recommendations": recs,
    }


@router.get("/audit-findings", response_model=list[AuditFindingResponse], summary="監査検出結果")
def list_audit_findings(db: Session = Depends(get_db)):
    """最新の監査実行で検出された全 Finding を返す。"""
    latest = db.query(models.AuditFinding).order_by(models.AuditFinding.created_at.desc()).first()
    if not latest:
        return []
    findings = db.query(models.AuditFinding).filter(
        models.AuditFinding.run_id == latest.run_id
    ).all()
    return [
        AuditFindingResponse(
            id=f.id,
            rule_id=f.rule_id,
            risk_level=f.risk_level,
            user_id=f.user_id,
            user_name=f.user.name if f.user else None,
            ip_address=f.ip_address,
            description=f.description,
            recommendation=f.recommendation,
            urgency=f.urgency,
            score=f.score,
            created_at=f.created_at.strftime("%Y-%m-%d %H:%M:%S") if f.created_at else None,
        )
        for f in findings
    ]


@router.get("/risk-scores", response_model=list[RiskScoreResponse], summary="リスクスコア一覧")
def list_risk_scores(db: Session = Depends(get_db)):
    """最新の監査実行のリスクスコアをスコア降順で返す。"""
    latest = db.query(models.RiskScore).order_by(models.RiskScore.calculated_at.desc()).first()
    if not latest:
        return []
    scores = db.query(models.RiskScore).filter(
        models.RiskScore.run_id == latest.run_id
    ).order_by(models.RiskScore.score.desc()).all()
    return [
        RiskScoreResponse(
            id=s.id,
            user_id=s.user_id,
            user_name=s.user.name if s.user else None,
            ip_address=s.ip_address,
            score=s.score,
            risk_level=s.risk_level,
            breakdown=json.loads(s.breakdown) if s.breakdown else {},
            calculated_at=s.calculated_at.strftime("%Y-%m-%d %H:%M:%S") if s.calculated_at else None,
        )
        for s in scores
    ]
