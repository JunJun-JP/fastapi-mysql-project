from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Detection:
    rule_id: str
    risk_level: str          # "high" | "medium" | "low"
    user_id: Optional[int]
    ip_address: str
    description: str
    recommendation: str
    urgency: str             # "immediate" | "high" | "medium"
    score: int
    evidence_log_ids: List[int] = field(default_factory=list)


def run_all(logs) -> List[Detection]:
    results: List[Detection] = []
    results.extend(_abnormal_times(logs))
    results.extend(_suspicious_actions(logs))
    results.extend(_rate_abuse(logs))
    results.extend(_admin_excess(logs))
    return results


def _abnormal_times(logs) -> List[Detection]:
    out = []
    for log in logs:
        if not log.timestamp:
            continue
        h = log.timestamp.hour
        if 0 <= h <= 5:
            out.append(Detection(
                rule_id="LOGIN_001",
                risk_level="high",
                user_id=log.user_id,
                ip_address=log.ip_address,
                description=f"深夜帯アクセス ({h:02d}時台) — {log.method} {log.endpoint}",
                recommendation="IPを即時確認し、不審な場合はブロックしてください",
                urgency="immediate",
                score=2,
                evidence_log_ids=[log.id],
            ))
        elif 22 <= h <= 23:
            out.append(Detection(
                rule_id="LOGIN_002",
                risk_level="medium",
                user_id=log.user_id,
                ip_address=log.ip_address,
                description=f"夜間帯アクセス ({h:02d}時台) — {log.method} {log.endpoint}",
                recommendation="業務上の必要性を確認してください",
                urgency="medium",
                score=1,
                evidence_log_ids=[log.id],
            ))
    return out


def _suspicious_actions(logs) -> List[Detection]:
    out = []
    for log in logs:
        if log.method == "DELETE":
            out.append(Detection(
                rule_id="ACTION_001",
                risk_level="high",
                user_id=log.user_id,
                ip_address=log.ip_address,
                description=f"DELETE操作を検出 — {log.endpoint}",
                recommendation="削除操作の承認フローを確認し、不正削除がないか監査してください",
                urgency="immediate",
                score=3,
                evidence_log_ids=[log.id],
            ))
        if log.status_code and log.status_code >= 500:
            out.append(Detection(
                rule_id="ACTION_002",
                risk_level="high",
                user_id=log.user_id,
                ip_address=log.ip_address,
                description=f"サーバーエラー {log.status_code} — {log.method} {log.endpoint}",
                recommendation="サーバーログを確認し、攻撃の可能性を調査してください",
                urgency="high",
                score=3,
                evidence_log_ids=[log.id],
            ))
    return out


def _rate_abuse(logs) -> List[Detection]:
    if len(logs) < 5:
        return []
    ip_map: dict[str, list] = defaultdict(list)
    for log in logs:
        ip_map[log.ip_address].append(log.id)
    total = len(logs)
    out = []
    for ip, ids in ip_map.items():
        if len(ids) / total > 0.5:
            out.append(Detection(
                rule_id="RATE_001",
                risk_level="high",
                user_id=None,
                ip_address=ip,
                description=f"単一IPからの集中アクセス — {ip} ({len(ids)}/{total}件, {len(ids)/total*100:.0f}%)",
                recommendation="レートリミットを導入し、該当IPのブロックを検討してください",
                urgency="immediate",
                score=3,
                evidence_log_ids=ids[:10],
            ))
    return out


def _admin_excess(logs) -> List[Detection]:
    user_map: dict[int, list] = defaultdict(list)
    for log in logs:
        if log.user_id:
            user_map[log.user_id].append(log.id)
    out = []
    for uid, ids in user_map.items():
        if len(ids) > 20:
            out.append(Detection(
                rule_id="ADMIN_001",
                risk_level="medium",
                user_id=uid,
                ip_address="",
                description=f"ユーザーID {uid} の過剰API操作 ({len(ids)}件)",
                recommendation="該当ユーザーの権限レビューを実施してください",
                urgency="medium",
                score=2,
                evidence_log_ids=ids[:10],
            ))
    return out
