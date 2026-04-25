from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional

from detectors.rules import Detection


@dataclass
class UserRiskScore:
    user_id: Optional[int]
    ip_address: str
    score: int
    risk_level: str          # "high" | "medium" | "low"
    breakdown: dict[str, int]


def compute(detections: List[Detection]) -> List[UserRiskScore]:
    """Detection リストからユーザー/IP ごとのリスクスコアを集計する。"""
    # key: user_id (int) or ip string when no user
    buckets: dict = defaultdict(lambda: {"score": 0, "breakdown": defaultdict(int), "ip": ""})

    for d in detections:
        key = d.user_id if d.user_id is not None else f"ip:{d.ip_address}"
        buckets[key]["score"] += d.score
        buckets[key]["breakdown"][d.rule_id] += d.score
        if d.ip_address:
            buckets[key]["ip"] = d.ip_address

    results: List[UserRiskScore] = []
    for key, data in buckets.items():
        s = data["score"]
        level = "high" if s >= 6 else ("medium" if s >= 3 else "low")
        user_id = key if isinstance(key, int) else None
        ip = data["ip"]
        results.append(UserRiskScore(
            user_id=user_id,
            ip_address=ip,
            score=s,
            risk_level=level,
            breakdown=dict(data["breakdown"]),
        ))

    return sorted(results, key=lambda x: x.score, reverse=True)
