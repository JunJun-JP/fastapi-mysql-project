# FastAPI + MySQL (Railway) Project

## セットアップ

```bash
pip install -r requirements.txt
```

## 環境変数

`.env.example` を `.env` にコピーして接続情報を記入：

```bash
cp .env.example .env
```

```env
DATABASE_URL=mysql+pymysql://root:password@your-host.railway.app:3306/railway
```

## 起動

```bash
uvicorn main:app --reload
```

## APIエンドポイント

| Method | Path     | 説明             |
|--------|----------|------------------|
| POST   | /users   | ユーザーを作成   |
| GET    | /users   | ユーザー一覧取得 |

## Swagger UI

http://localhost:8000/docs

## Railwayへのデプロイ

Procfileがあるのでそのままデプロイ可能。
