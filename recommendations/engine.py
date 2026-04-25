from __future__ import annotations
from typing import List

from detectors.rules import Detection

# ルールIDごとの推奨アクションカタログ
_CATALOG: dict[str, dict] = {
    "LOGIN_001": {
        "title": "深夜帯アクセスポリシーの強化",
        "action": "時間外アクセス制限ポリシーを策定し、VPN経由のみ許可する設定を検討してください",
    },
    "LOGIN_002": {
        "title": "夜間アクセスの監視強化",
        "action": "夜間帯アクセスにはMFA（多要素認証）を必須化することを検討してください",
    },
    "ACTION_001": {
        "title": "削除操作の承認フロー整備",
        "action": "DELETEオペレーションに上長承認フローを設け、ソフトデリートへの移行を検討してください",
    },
    "ACTION_002": {
        "title": "エラー監視アラートの設定",
        "action": "5xxエラー発生時の即時通知（Slack/メール）アラートを設定してください",
    },
    "RATE_001": {
        "title": "レートリミットの導入",
        "action": "IPベースのレートリミット（例: 60req/min）を実装し、WAFの導入を検討してください",
    },
    "ADMIN_001": {
        "title": "最小権限原則の適用",
        "action": "該当ユーザーの権限をレビューし、業務に必要な最小限のAPIアクセスのみ許可してください",
    },
}

_PRIORITY = {"immediate": 0, "high": 1, "medium": 2}


def generate(detections: List[Detection]) -> List[dict]:
    """検出結果からルール単位の推奨アクション一覧を生成する（重複排除・優先度順）。"""
    seen: set[str] = set()
    recs: List[dict] = []

    for d in sorted(detections, key=lambda x: _PRIORITY.get(x.urgency, 9)):
        if d.rule_id in seen:
            continue
        seen.add(d.rule_id)
        meta = _CATALOG.get(d.rule_id, {})
        recs.append({
            "rule_id": d.rule_id,
            "risk_level": d.risk_level,
            "title": meta.get("title", d.rule_id),
            "description": d.description,
            "action": meta.get("action", d.recommendation),
            "urgency": d.urgency,
        })

    return recs
