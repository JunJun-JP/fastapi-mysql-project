"""audit_logs レコードから IP ごとの特徴量を生成する。"""

import numpy as np
import polars as pl

FEATURE_COLS = [
    "failed_count",           # 401 エラー数（ブルートフォース検知）
    "total_requests",         # 総リクエスト数
    "night_access_count",     # 深夜（00〜05時）アクセス数
    "admin_ratio",            # DELETE リクエスト率
    "unique_status_count",    # ステータスコードの種類数
    "error_rate",             # 4xx/5xx エラー率
    "unique_endpoint_count",  # アクセスしたエンドポイントの種類数（スキャン検知）
    "error_404_rate",         # 404 エラー率（存在しないパスを探る行為）
]


def build_features(logs: list) -> tuple[pl.DataFrame, np.ndarray]:
    """
    AuditLog ORM オブジェクトのリストから特徴量を生成する。

    Returns
    -------
    feature_df : IP + 特徴量の DataFrame
    X          : shape (n_ips, 8) の float32 配列
    """
    rows = [
        {
            "ip":       log.ip_address,
            "status":   log.status_code or 200,
            "hour":     log.timestamp.hour if log.timestamp else 12,
            "method":   log.method or "GET",
            "endpoint": log.endpoint or "/",
        }
        for log in logs
    ]

    df = pl.DataFrame(rows)

    feature_df = (
        df.group_by("ip")
        .agg(
            (pl.col("status") == 401).sum().alias("failed_count"),
            pl.len().alias("total_requests"),
            (pl.col("hour") <= 5).sum().alias("night_access_count"),
            (pl.col("method") == "DELETE").mean().alias("admin_ratio"),
            pl.col("status").n_unique().alias("unique_status_count"),
            (pl.col("status") >= 400).mean().alias("error_rate"),
            # ── 新特徴量 ──────────────────────────────────────────────
            pl.col("endpoint").n_unique().alias("unique_endpoint_count"),
            (pl.col("status") == 404).mean().alias("error_404_rate"),
        )
        .sort("ip")
    )

    X = feature_df.select(FEATURE_COLS).to_numpy().astype(np.float32)
    return feature_df, X
