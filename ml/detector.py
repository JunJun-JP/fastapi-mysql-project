"""2モデルを統合して最終判定を行う。"""

from datetime import datetime

from ml.features import build_features
from ml.models import run_isolation_forest, run_autoencoder


# ── パターン分析 ──────────────────────────────────────────────────────────────

def _analyze_patterns(row: dict, ip_logs: list) -> list[dict]:
    """特徴量と実ログからIPの具体的な不審行動を分析する。"""
    patterns = []

    # ブルートフォース：401 エラーが多い
    if row["failed_count"] >= 5:
        patterns.append({
            "type": "brute_force",
            "severity": "high",
            "label": "ブルートフォース攻撃の疑い",
            "detail": f"認証失敗（401）を {int(row['failed_count'])} 回繰り返しています。"
                      f"パスワードの総当たり攻撃の可能性があります。",
        })
    elif row["failed_count"] >= 2:
        patterns.append({
            "type": "brute_force",
            "severity": "medium",
            "label": "認証失敗の繰り返し",
            "detail": f"認証失敗（401）が {int(row['failed_count'])} 回発生しています。",
        })

    # エンドポイントスキャン：多種類のパスにアクセス
    if row["unique_endpoint_count"] >= 8:
        # 実際にアクセスしたパスを列挙
        endpoints = list({l.endpoint for l in ip_logs if l.endpoint})
        suspicious = [e for e in endpoints if any(
            kw in e for kw in [".env", ".git", "wp-admin", "phpmyadmin", "admin", "config", "backup", "api/v1"]
        )]
        detail = f"{int(row['unique_endpoint_count'])} 種類のパスを探索しています。"
        if suspicious:
            detail += f" 特に {', '.join(suspicious[:4])} など機密パスへのアクセスを確認。"
        patterns.append({
            "type": "scanning",
            "severity": "high",
            "label": "エンドポイントスキャン疑い",
            "detail": detail,
        })
    elif row["unique_endpoint_count"] >= 5:
        patterns.append({
            "type": "scanning",
            "severity": "medium",
            "label": "複数エンドポイントへの探索",
            "detail": f"{int(row['unique_endpoint_count'])} 種類のパスにアクセスしています。",
        })

    # 存在しないパスの探索：404 エラー率が高い
    if row["error_404_rate"] >= 0.15:
        not_found = [l.endpoint for l in ip_logs if l.status_code == 404]
        detail = f"リクエストの {row['error_404_rate']*100:.0f}% が 404（存在しないパス）です。"
        if not_found:
            detail += f" 試されたパス: {', '.join(list(set(not_found))[:5])}"
        patterns.append({
            "type": "path_probing",
            "severity": "high" if row["error_404_rate"] >= 0.3 else "medium",
            "label": "存在しないパスの探索（スキャン疑い）",
            "detail": detail,
        })

    # 深夜アクセス
    if row["night_access_count"] >= 5:
        patterns.append({
            "type": "night_access",
            "severity": "high",
            "label": "深夜帯の大量アクセス",
            "detail": f"深夜0〜5時に {int(row['night_access_count'])} 回アクセスしています。"
                      f"業務時間外の不正操作の可能性があります。",
        })
    elif row["night_access_count"] >= 1:
        patterns.append({
            "type": "night_access",
            "severity": "medium",
            "label": "深夜帯アクセス",
            "detail": f"深夜0〜5時に {int(row['night_access_count'])} 回アクセスしています。",
        })

    # 高エラー率：サーバー攻撃やアプリ障害誘発の可能性
    if row["error_rate"] >= 0.5:
        patterns.append({
            "type": "high_errors",
            "severity": "high",
            "label": "異常なエラー率",
            "detail": f"リクエストの {row['error_rate']*100:.0f}% がエラーです。"
                      f"サーバー攻撃または障害誘発の可能性があります。",
        })

    # データ削除操作
    if row["admin_ratio"] >= 0.3:
        deletes = [l.endpoint for l in ip_logs if l.method == "DELETE"]
        patterns.append({
            "type": "data_destruction",
            "severity": "high",
            "label": "大量データ削除操作",
            "detail": f"DELETE リクエストが {row['admin_ratio']*100:.0f}%。"
                      f"削除されたパス: {', '.join(list(set(deletes))[:5])}",
        })
    elif row["admin_ratio"] >= 0.05:
        patterns.append({
            "type": "data_destruction",
            "severity": "medium",
            "label": "DELETE 操作を検出",
            "detail": f"DELETE リクエストが {row['admin_ratio']*100:.0f}% 含まれています。",
        })

    if not patterns:
        patterns.append({
            "type": "normal",
            "severity": "low",
            "label": "異常なし",
            "detail": "特定の不審なパターンは検出されませんでした。",
        })

    return patterns


# ── メイン検知関数 ────────────────────────────────────────────────────────────

def ai_detect(logs: list, max_epochs: int = 300) -> dict:
    """
    audit_logs の ORM リストを受け取り、IP ごとの異常判定を返す。
    IsolationForest OR AutoEncoder のどちらかが異常 → is_anomaly=True
    """
    if not logs:
        return {"total_ips": 0, "anomaly_count": 0, "results": []}

    feature_df, X = build_features(logs)

    if_labels = run_isolation_forest(X)
    ae_anomaly, ae_errors, ae_threshold, ae_best_epoch = run_autoencoder(X, max_epochs=max_epochs)

    # IP → ユーザー名 / ログ一覧 のマッピング
    ip_to_user: dict[str, str | None] = {}
    ip_to_logs: dict[str, list] = {}
    for log in logs:
        ip = log.ip_address
        if ip not in ip_to_user:
            ip_to_user[ip] = log.user.name if log.user else None
        ip_to_logs.setdefault(ip, []).append(log)

    ips = feature_df["ip"].to_list()
    results = []
    for i, ip in enumerate(ips):
        if_flag  = bool(if_labels[i] == -1)
        ae_flag  = bool(ae_anomaly[i])
        row      = feature_df.row(i, named=True)
        ip_logs  = ip_to_logs.get(ip, [])
        patterns = _analyze_patterns(row, ip_logs)

        # 直近ログ（最大10件、時系列順）
        sorted_logs = sorted(
            ip_logs,
            key=lambda l: l.timestamp or datetime.min
        )
        recent_logs = [
            {
                "method":   l.method or "—",
                "endpoint": l.endpoint or "—",
                "status":   l.status_code,
                "time":     l.timestamp.strftime("%m/%d %H:%M") if l.timestamp else "—",
            }
            for l in sorted_logs[-10:]
        ]

        results.append({
            "ip":        ip,
            "user_name": ip_to_user.get(ip),
            "features": {
                "failed_count":          int(row["failed_count"]),
                "total_requests":        int(row["total_requests"]),
                "night_access_count":    int(row["night_access_count"]),
                "error_rate":            round(float(row["error_rate"]), 3),
                "unique_status_count":   int(row["unique_status_count"]),
                "unique_endpoint_count": int(row["unique_endpoint_count"]),
                "error_404_rate":        round(float(row["error_404_rate"]), 3),
            },
            "patterns":              patterns,
            "recent_logs":           recent_logs,
            "isolation_forest":      if_flag,
            "autoencoder_score":     round(float(ae_errors[i]), 6),
            "autoencoder_threshold": round(ae_threshold, 6),
            "is_anomaly":            if_flag or ae_flag,
        })

    results.sort(key=lambda r: r["autoencoder_score"], reverse=True)
    anomalies = [r for r in results if r["is_anomaly"]]

    return {
        "total_ips":         len(ips),
        "anomaly_count":     len(anomalies),
        "ae_optimal_epochs": ae_best_epoch,
        "anomalies":         anomalies,
        "results":           results,
    }
