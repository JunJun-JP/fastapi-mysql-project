import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import models
from database import engine, get_db
from routers import pages, users, audit, ai

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))

_SKIP_AUDIT_PATHS = {
    "/dashboard", "/audit-logs", "/docs", "/docs/login", "/docs/logout",
    "/dashboard/login", "/openapi.json", "/", "/favicon.ico",
}

_DESCRIPTION = """
## 概要
APIアクセスを自動記録し、リスク検出・スコアリング・推奨アクション生成を行う **GRC監査システム** です。

---

## 🔐 認証
このドキュメントはログイン済みユーザーのみ閲覧可能です。セッションは **8時間** 有効です。
ログアウトは [`/docs/logout`](/docs/logout) から行えます。

---

## 📋 エンドポイント早見表

| メソッド | パス | 説明 |
|--------|------|------|
| `POST` | `/users` | ユーザー登録（name・email必須） |
| `GET` | `/users` | 登録ユーザー一覧 |
| `GET` | `/audit-logs` | 全アクセスログ（新しい順） |
| `POST` | `/run-audit` | 監査エンジン実行・結果をDB保存 |
| `GET` | `/audit-findings` | 最新監査の検出結果一覧 |
| `GET` | `/risk-scores` | 最新監査のリスクスコア一覧 |
| `POST` | `/ai-detect` | AI異常検知（Isolation Forest + AutoEncoder） |

---

## 🚨 リスク検出ルール

| ルールID | リスク | 条件 | スコア |
|---------|--------|------|--------|
| `LOGIN_001` | **High** | 深夜帯（00〜05時）アクセス | +2 |
| `LOGIN_002` | Medium | 夜間帯（22〜23時）アクセス | +1 |
| `ACTION_001` | **High** | DELETE リクエスト検出 | +3 |
| `ACTION_002` | **High** | 5xx サーバーエラー | +3 |
| `RATE_001` | **High** | 単一IPが全体の50%超 | +3 |
| `ADMIN_001` | Medium | 同一ユーザーが20件超 | +2 |

**スコア判定：** `≥6` → High　`≥3` → Medium　`それ以下` → Low

---

## 🔄 監査の実行手順

```
1. POST /run-audit を実行
2. GET /audit-findings で検出結果を確認
3. GET /risk-scores でリスクスコアを確認
```

または [ダッシュボード](/dashboard) の「監査実行」ボタンから操作できます。

---

## ⚙️ 自動ログ記録の仕組み

全リクエストはHTTPミドルウェアで自動キャプチャされます（`/docs` `/dashboard` 等の管理パスは除外）。

記録内容：`IP` / `method` / `endpoint` / `status_code` / `timestamp` / `user_id`
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database tables ready")
    except Exception as e:
        logger.warning("DB create_all failed: %s", e)
    yield


app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    title="社内管理システム",
    version="0.1.0",
    description=_DESCRIPTION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pages.router)
app.include_router(users.router)
app.include_router(audit.router)
app.include_router(ai.router)


@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    response = await call_next(request)
    if request.url.path in _SKIP_AUDIT_PATHS:
        return response
    try:
        forwarded = request.headers.get("x-forwarded-for")
        ip = (
            forwarded.split(",")[0].strip()
            if forwarded
            else (request.client.host if request.client else "unknown")
        )
        db = next(get_db())
        try:
            db.add(models.AuditLog(
                ip_address=ip,
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                timestamp=datetime.now(JST).replace(tzinfo=None),
            ))
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.debug("audit_log_middleware error: %s", e)
    return response
