# GRC Security Dashboard

社内APIの不正アクセスを自動検知するセキュリティ監査ツール。

FastAPI + MySQL + Railway でデプロイ済み。2つの機械学習モデル（Isolation Forest / AutoEncoder）でIPアドレスごとの異常行動を検出し、ダッシュボードに可視化する。

---

## 技術スタック

| カテゴリ | 技術 |
|---|---|
| バックエンド | FastAPI (Python) |
| データベース | MySQL（Railway）|
| デプロイ | Railway PaaS |
| 認証 | HMAC-SHA256 セッション認証（httponly Cookie）|
| ML | scikit-learn（Isolation Forest）+ PyTorch（AutoEncoder + Early Stopping）|
| 特徴量 | Polars |
| テンプレート | Jinja2 |

---

## ファイル構成

```
fastapi-mysql-project/
├── main.py                  # アプリエントリーポイント・ミドルウェア
├── config.py                # 環境変数管理
├── auth.py                  # HMAC-SHA256 認証・Depends
├── database.py              # SQLAlchemy セッション
├── models.py                # ORM モデル（4テーブル）
├── schemas.py               # Pydantic v2 スキーマ
├── seed.py                  # サンプルデータ投入スクリプト
├── routers/
│   ├── pages.py             # HTML ページルート（ログイン/ダッシュボード/docs）
│   ├── users.py             # /users
│   ├── audit.py             # /audit-logs, /run-audit, /audit-findings, /risk-scores
│   └── ai.py                # /ai-detect
├── ml/
│   ├── features.py          # Polars 特徴量エンジニアリング（8次元）
│   ├── models.py            # Isolation Forest + AutoEncoder（Early Stopping）
│   └── detector.py          # 2モデル統合・パターン分析
├── detectors/rules.py       # ルールベース検知
├── recommendations/engine.py# 推奨アクション生成
├── risk/scorer.py           # リスクスコアリング
└── templates/
    ├── login.html           # ログインページ
    ├── dashboard.html       # メインダッシュボード
    └── docs.html            # Swagger UI ラッパー
```

---

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example` を `.env` にコピーして各値を記入：

```bash
cp .env.example .env
```

```env
DATABASE_URL=mysql+pymysql://root:password@your-host.railway.app:3306/railway
ADMIN_USERNAME=admin
ADMIN_PASSWORD=yourpassword
SESSION_SECRET=your-random-secret
```

### 3. ローカル起動

```bash
uvicorn main:app --reload
```

### 4. サンプルデータ投入

```bash
python -X utf8 seed.py
```

4つのハッカーシナリオが投入されます：

| IP | シナリオ |
|---|---|
| 218.92.0.191 | 深夜偵察・エンドポイント総当たり（Night Crawler）|
| 91.108.56.247 | 認証ブルートフォース・大量401（Brute Forcer）|
| 185.220.101.55 | DELETE連発・データ破壊（Data Destroyer）|
| 45.155.205.233 | 高速スキャン・集中アクセス（Rapid Scanner）|

---

## APIエンドポイント

すべてのAPIエンドポイントはセッション認証が必要です。

| Method | Path | 説明 |
|---|---|---|
| GET | /dashboard | ダッシュボード（要ログイン）|
| POST | /ai-detect | AI 異常検知実行 |
| POST | /run-audit | ルールベース監査実行 |
| GET | /audit-logs | アクセスログ一覧 |
| GET | /audit-findings | 監査検出結果 |
| GET | /risk-scores | リスクスコア一覧 |
| GET | /users | ユーザー一覧 |
| POST | /users | ユーザー登録 |

---

## ML 検知ロジック

### 特徴量（8次元）

| 特徴量 | 説明 |
|---|---|
| failed_count | 401エラー数（ブルートフォース検知）|
| total_requests | 総リクエスト数 |
| night_access_count | 深夜0〜5時アクセス数 |
| admin_ratio | DELETEリクエスト率 |
| unique_status_count | ステータスコードの種類数 |
| error_rate | 4xx/5xx エラー率 |
| unique_endpoint_count | アクセスエンドポイント種類数（スキャン検知）|
| error_404_rate | 404エラー率（パス探索検知）|

### 判定ロジック

- **Isolation Forest**（contamination=0.15）: 外れ値検出
- **AutoEncoder**（Early Stopping, patience=15）: 再構成誤差で異常スコア算出
- どちらか一方が異常と判定 → `is_anomaly = True`

---

## デプロイ（Railway）

```bash
railway up
```

`Procfile` に起動コマンドが定義済みのため、そのままデプロイ可能。
