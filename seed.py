"""
サンプルデータ投入スクリプト。
実行: python -X utf8 seed.py
"""

import json
import uuid
from datetime import datetime, timedelta, timezone

from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)

JST = timezone(timedelta(hours=9))


def jst(year, month, day, hour, minute=0, second=0):
    return datetime(year, month, day, hour, minute, second, tzinfo=JST).replace(tzinfo=None)


def now_jst():
    return datetime.now(JST).replace(tzinfo=None)


# ── ユーザー定義 ──────────────────────────────────────────────────────────────

USERS = [
    {"name": "田中 太郎",   "email": "tanaka@example.com"},
    {"name": "佐藤 花子",   "email": "sato@example.com"},
    {"name": "鈴木 一郎",   "email": "suzuki@example.com"},
    {"name": "山田 美咲",   "email": "yamada@example.com"},
    {"name": "伊藤 健太",   "email": "ito@example.com"},
]

# ── ログシナリオ定義 ──────────────────────────────────────────────────────────
# (ip, method, endpoint, status_code, timestamp, user_index or None)

LOGS = [

    # ════════════════════════════════════════════════════════
    #  正常系アクセス（社内ユーザー）
    # ════════════════════════════════════════════════════════
    ("192.168.1.10", "GET",  "/users",         200, jst(2025,4,20,10, 5),  0),
    ("192.168.1.10", "POST", "/users",         201, jst(2025,4,20,10, 7),  0),
    ("192.168.1.10", "GET",  "/audit-logs",    200, jst(2025,4,20,10,15),  0),
    ("192.168.1.10", "GET",  "/audit-logs",    200, jst(2025,4,20,22,10),  0),  # 夜間
    ("192.168.1.11", "GET",  "/users",         200, jst(2025,4,20,11, 0),  1),
    ("192.168.1.11", "GET",  "/audit-logs",    200, jst(2025,4,20,11,30),  1),
    ("192.168.1.11", "GET",  "/users",         200, jst(2025,4,20,22,45),  1),  # 夜間
    ("192.168.1.12", "GET",  "/users",         200, jst(2025,4,20,13, 0),  2),
    ("192.168.1.12", "POST", "/users",         201, jst(2025,4,20,13, 5),  2),
    ("192.168.1.13", "GET",  "/audit-logs",    200, jst(2025,4,20,14, 0),  3),
    ("192.168.1.13", "GET",  "/risk-scores",   200, jst(2025,4,20,23, 5),  3),  # 夜間
    ("192.168.1.14", "GET",  "/users",         200, jst(2025,4,20,15, 0),  4),

    # 田中さんが業務で大量アクセス → ADMIN_001 発動
    *[
        ("192.168.1.10", "GET", "/audit-logs", 200, jst(2025,4,23,10, i), 0)
        for i in range(25)
    ],

    # ════════════════════════════════════════════════════════
    #  [HACKER-1]  "Night Crawler"  218.92.0.191
    #  中国系 IP。深夜に静かに偵察し、エンドポイントを総当たり。
    #  → LOGIN_001 (深夜) + RATE_001 (集中アクセス)
    # ════════════════════════════════════════════════════════
    ("218.92.0.191", "GET",  "/users",          200, jst(2025,4,24, 2, 0),  None),
    ("218.92.0.191", "GET",  "/audit-logs",     200, jst(2025,4,24, 2, 1),  None),
    ("218.92.0.191", "GET",  "/audit-findings", 200, jst(2025,4,24, 2, 2),  None),
    ("218.92.0.191", "GET",  "/risk-scores",    200, jst(2025,4,24, 2, 3),  None),
    ("218.92.0.191", "GET",  "/ai-detect",      405, jst(2025,4,24, 2, 4),  None),
    ("218.92.0.191", "POST", "/ai-detect",      200, jst(2025,4,24, 2, 5),  None),
    ("218.92.0.191", "GET",  "/users/1",        404, jst(2025,4,24, 2, 6),  None),
    ("218.92.0.191", "GET",  "/users/2",        404, jst(2025,4,24, 2, 7),  None),
    ("218.92.0.191", "GET",  "/users/3",        404, jst(2025,4,24, 2, 8),  None),
    ("218.92.0.191", "GET",  "/admin",          404, jst(2025,4,24, 2, 9),  None),
    ("218.92.0.191", "GET",  "/config",         404, jst(2025,4,24, 2,10),  None),
    ("218.92.0.191", "GET",  "/.env",           404, jst(2025,4,24, 2,11),  None),
    ("218.92.0.191", "GET",  "/backup",         404, jst(2025,4,24, 2,12),  None),
    ("218.92.0.191", "POST", "/run-audit",      200, jst(2025,4,24, 3, 0),  None),
    ("218.92.0.191", "GET",  "/audit-findings", 200, jst(2025,4,24, 3, 1),  None),
    ("218.92.0.191", "GET",  "/users",          200, jst(2025,4,24, 3, 5),  None),
    ("218.92.0.191", "GET",  "/users",          200, jst(2025,4,24, 3,10),  None),
    ("218.92.0.191", "GET",  "/users",          200, jst(2025,4,24, 4, 0),  None),
    ("218.92.0.191", "GET",  "/audit-logs",     200, jst(2025,4,24, 4,30),  None),

    # ════════════════════════════════════════════════════════
    #  [HACKER-2]  "Brute Forcer"  91.108.56.247
    #  ロシア系 IP。401 を大量に出しながら認証突破を試みる。
    #  → LOGIN_001 (深夜) + ACTION_002 (大量エラー)
    # ════════════════════════════════════════════════════════
    ("91.108.56.247", "POST", "/users",   401, jst(2025,4,24, 1, 0,  0), None),
    ("91.108.56.247", "POST", "/users",   401, jst(2025,4,24, 1, 0, 10), None),
    ("91.108.56.247", "POST", "/users",   401, jst(2025,4,24, 1, 0, 20), None),
    ("91.108.56.247", "POST", "/users",   401, jst(2025,4,24, 1, 0, 30), None),
    ("91.108.56.247", "POST", "/users",   401, jst(2025,4,24, 1, 0, 40), None),
    ("91.108.56.247", "POST", "/users",   401, jst(2025,4,24, 1, 0, 50), None),
    ("91.108.56.247", "POST", "/users",   401, jst(2025,4,24, 1, 1,  0), None),
    ("91.108.56.247", "POST", "/users",   401, jst(2025,4,24, 1, 1, 10), None),
    ("91.108.56.247", "POST", "/users",   401, jst(2025,4,24, 1, 1, 20), None),
    ("91.108.56.247", "POST", "/users",   401, jst(2025,4,24, 1, 1, 30), None),
    ("91.108.56.247", "POST", "/users",   401, jst(2025,4,24, 1, 1, 40), None),
    ("91.108.56.247", "POST", "/users",   401, jst(2025,4,24, 1, 1, 50), None),
    ("91.108.56.247", "POST", "/users",   500, jst(2025,4,24, 1, 2,  0), None),  # サーバー過負荷
    ("91.108.56.247", "POST", "/users",   500, jst(2025,4,24, 1, 2, 10), None),
    ("91.108.56.247", "GET",  "/users",   200, jst(2025,4,24, 1, 5,  0), None),  # 突破成功

    # ════════════════════════════════════════════════════════
    #  [HACKER-3]  "Data Destroyer"  185.220.101.55
    #  Tor 出口ノード。DELETE を連発してデータ破壊を試みる。
    #  → ACTION_001 (DELETE連発) + LOGIN_001 (深夜)
    # ════════════════════════════════════════════════════════
    ("185.220.101.55", "GET",    "/users",     200, jst(2025,4,25, 3, 0), None),
    ("185.220.101.55", "DELETE", "/users/1",   200, jst(2025,4,25, 3, 1), None),
    ("185.220.101.55", "DELETE", "/users/2",   200, jst(2025,4,25, 3, 2), None),
    ("185.220.101.55", "DELETE", "/users/3",   200, jst(2025,4,25, 3, 3), None),
    ("185.220.101.55", "DELETE", "/users/4",   404, jst(2025,4,25, 3, 4), None),
    ("185.220.101.55", "DELETE", "/users/5",   404, jst(2025,4,25, 3, 5), None),
    ("185.220.101.55", "DELETE", "/audit-logs",403, jst(2025,4,25, 3, 6), None),
    ("185.220.101.55", "POST",   "/run-audit", 500, jst(2025,4,25, 3, 7), None),
    ("185.220.101.55", "DELETE", "/users/6",   500, jst(2025,4,25, 3, 8), None),

    # ════════════════════════════════════════════════════════
    #  [HACKER-4]  "Rapid Scanner"  45.155.205.233
    #  欧州 VPS。高速でエンドポイントをスキャン。
    #  → RATE_001 (全体の50%超を占める集中アクセス)
    # ════════════════════════════════════════════════════════
    *[
        ("45.155.205.233", "GET", ep, code, jst(2025,4,25, 9, i // 2, (i % 2) * 30), None)
        for i, (ep, code) in enumerate([
            ("/users",          200), ("/audit-logs",    200),
            ("/audit-findings", 200), ("/risk-scores",   200),
            ("/ai-detect",      405), ("/run-audit",     405),
            ("/users",          200), ("/users",         200),
            ("/audit-logs",     200), ("/audit-findings",200),
            ("/risk-scores",    200), ("/users",         200),
            ("/audit-logs",     200), ("/users",         200),
            ("/audit-findings", 200), ("/risk-scores",   200),
            ("/.git/config",    404), ("/wp-admin",      404),
            ("/phpmyadmin",     404), ("/api/v1/users",  404),
        ])
    ],
    # スキャナーを「集中」に見せるため他 IP は少数
    ("192.168.2.1", "GET", "/users",      200, jst(2025,4,25, 9,15), None),
    ("192.168.2.2", "GET", "/audit-logs", 200, jst(2025,4,25, 9,16), None),
    ("192.168.2.3", "GET", "/users",      200, jst(2025,4,25, 9,17), None),
]


def seed():
    db = SessionLocal()
    try:
        # ── 既存データ削除 ────────────────────────────────────
        db.query(models.RiskScore).delete()
        db.query(models.AuditFinding).delete()
        db.query(models.AuditLog).delete()
        db.query(models.User).delete()
        db.commit()
        print("OK  既存データをクリア")

        # ── ユーザー登録 ──────────────────────────────────────
        user_objs = []
        for u in USERS:
            obj = models.User(name=u["name"], email=u["email"])
            db.add(obj)
            user_objs.append(obj)
        db.commit()
        for obj in user_objs:
            db.refresh(obj)
        print(f"OK  ユーザー {len(user_objs)} 件を登録")

        # ── 監査ログ投入 ──────────────────────────────────────
        log_objs = []
        for ip, method, endpoint, status, ts, user_idx in LOGS:
            uid = user_objs[user_idx].id if user_idx is not None else None
            obj = models.AuditLog(
                ip_address=ip, method=method, endpoint=endpoint,
                status_code=status, timestamp=ts, user_id=uid,
            )
            db.add(obj)
            log_objs.append(obj)
        db.commit()
        print(f"OK  監査ログ {len(log_objs)} 件を投入")

        # ── 監査エンジン実行 ──────────────────────────────────
        from detectors.rules import run_all
        from risk.scorer import compute
        from recommendations.engine import generate

        all_logs  = db.query(models.AuditLog).all()
        detections = run_all(all_logs)
        scores     = compute(detections)
        recs       = generate(detections)
        run_id     = str(uuid.uuid4())
        run_at     = now_jst()

        for d in detections:
            db.add(models.AuditFinding(
                run_id=run_id, rule_id=d.rule_id, risk_level=d.risk_level,
                user_id=d.user_id, ip_address=d.ip_address,
                description=d.description, recommendation=d.recommendation,
                urgency=d.urgency, score=d.score,
                evidence=json.dumps(d.evidence_log_ids), created_at=run_at,
            ))
        for s in scores:
            db.add(models.RiskScore(
                run_id=run_id, user_id=s.user_id, ip_address=s.ip_address,
                score=s.score, risk_level=s.risk_level,
                breakdown=json.dumps(s.breakdown), calculated_at=run_at,
            ))
        db.commit()
        print(f"OK  監査エンジン完了 — findings: {len(detections)}, scores: {len(scores)}")

        # ── サマリー ──────────────────────────────────────────
        high   = sum(1 for d in detections if d.risk_level == "high")
        medium = sum(1 for d in detections if d.risk_level == "medium")
        print()
        print("=" * 44)
        print("  シードデータ投入完了")
        print("=" * 44)
        print(f"  ユーザー          : {len(user_objs)} 件")
        print(f"  監査ログ          : {len(log_objs)} 件")
        print(f"  High findings     : {high} 件")
        print(f"  Medium findings   : {medium} 件")
        print(f"  推奨アクション    : {len(recs)} 件")
        print()
        print("  [ハッカーシナリオ]")
        print("  218.92.0.191   Night Crawler  (深夜偵察・エンドポイント総当たり)")
        print("  91.108.56.247  Brute Forcer   (認証ブルートフォース・大量401)")
        print("  185.220.101.55 Data Destroyer (DELETE連発・データ破壊)")
        print("  45.155.205.233 Rapid Scanner  (高速スキャン・集中アクセス)")
        print("=" * 44)

    finally:
        db.close()


if __name__ == "__main__":
    seed()
