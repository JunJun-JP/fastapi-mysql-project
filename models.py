from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45))
    method = Column(String(10))
    endpoint = Column(String(255))
    status_code = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, nullable=True)

    user = relationship("User", backref="audit_logs")


class AuditFinding(Base):
    """run-audit で検出された個別の問題を永続化するテーブル。"""
    __tablename__ = "audit_findings"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(36), index=True)   # 同一実行をグループ化する UUID
    rule_id = Column(String(50))
    risk_level = Column(String(10))           # high | medium | low
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45))
    description = Column(String(500))
    recommendation = Column(String(500))
    urgency = Column(String(20))
    score = Column(Integer)
    evidence = Column(Text)                   # JSON: 関連ログIDのリスト
    created_at = Column(DateTime)

    user = relationship("User", backref="findings")


class RiskScore(Base):
    """run-audit で計算されたユーザー/IP ごとのリスクスコア。"""
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(36), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45))
    score = Column(Integer)
    risk_level = Column(String(10))           # high | medium | low
    breakdown = Column(Text)                  # JSON: {rule_id: score}
    calculated_at = Column(DateTime)

    user = relationship("User", backref="risk_scores")
