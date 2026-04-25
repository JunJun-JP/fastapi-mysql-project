const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageNumber, Header, Footer, TableOfContents,
  PageBreak
} = require("docx");
const fs = require("fs");

// ── helpers ──────────────────────────────────────────────────────────────────

const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const NO_BORDER = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const NO_BORDERS = { top: NO_BORDER, bottom: NO_BORDER, left: NO_BORDER, right: NO_BORDER };
const CONTENT_W = 9026; // A4 1-inch margins

function h(text, level, opts = {}) {
  return new Paragraph({
    heading: level,
    children: [new TextRun({ text, font: "Arial" })],
    spacing: { before: 240, after: 120 },
    ...opts,
  });
}

function p(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 22 })],
    spacing: { before: 60, after: 60 },
    ...opts,
  });
}

function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    children: [new TextRun({ text, font: "Arial", size: 22 })],
    spacing: { before: 40, after: 40 },
  });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function sectionTitle(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, font: "Arial", bold: true })],
    spacing: { before: 360, after: 180 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2563EB", space: 6 } },
  });
}

function subTitle(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, font: "Arial", bold: true })],
    spacing: { before: 240, after: 120 },
  });
}

// ── table helpers ─────────────────────────────────────────────────────────────

function headerCell(text, w) {
  return new TableCell({
    borders: BORDERS,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: "2563EB", type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      children: [new TextRun({ text, font: "Arial", size: 20, bold: true, color: "FFFFFF" })],
    })],
  });
}

function dataCell(text, w, shade = false) {
  return new TableCell({
    borders: BORDERS,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: shade ? "F0F4FF" : "FFFFFF", type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      children: [new TextRun({ text, font: "Arial", size: 20 })],
    })],
  });
}

function monoCell(text, w, shade = false) {
  return new TableCell({
    borders: BORDERS,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: shade ? "F0F4FF" : "FFFFFF", type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      children: [new TextRun({ text, font: "Courier New", size: 18 })],
    })],
  });
}

function makeTable(headers, rows, colWidths) {
  const totalW = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) => headerCell(h, colWidths[i])),
      }),
      ...rows.map((row, ri) =>
        new TableRow({
          children: row.map((cell, ci) => {
            const isMono = typeof cell === "object" && cell.mono;
            const text = typeof cell === "object" ? cell.text : cell;
            return isMono
              ? monoCell(text, colWidths[ci], ri % 2 === 0)
              : dataCell(text, colWidths[ci], ri % 2 === 0);
          }),
        })
      ),
    ],
  });
}

// ── document ─────────────────────────────────────────────────────────────────

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u2022",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }, {
          level: 1, format: LevelFormat.BULLET, text: "\u25E6",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1080, hanging: 360 } } },
        }],
      },
    ],
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "1E3A5F" },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2563EB" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "374151" },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 },
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [
            new TextRun({ text: "GRC セキュリティ監査システム  |  システム仕様書", font: "Arial", size: 18, color: "6B7280" }),
          ],
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "E5E7EB", space: 4 } },
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [
            new TextRun({ text: "- ", font: "Arial", size: 18, color: "9CA3AF" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: "9CA3AF" }),
            new TextRun({ text: " -", font: "Arial", size: 18, color: "9CA3AF" }),
          ],
        })],
      }),
    },
    children: [

      // ═════════════════════════════════════════
      // 表紙
      // ═════════════════════════════════════════
      new Paragraph({ children: [new TextRun("")], spacing: { before: 1440 } }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "GRC セキュリティ監査システム", font: "Arial", size: 52, bold: true, color: "1E3A5F" })],
        spacing: { before: 1440, after: 240 },
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "システム仕様書", font: "Arial", size: 36, color: "2563EB" })],
        spacing: { before: 0, after: 600 },
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: "E5E7EB", space: 1 } },
        children: [new TextRun("")],
        spacing: { before: 0, after: 240 },
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "バージョン: v1.0", font: "Arial", size: 22, color: "6B7280" })],
        spacing: { before: 0, after: 120 },
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "作成日: 2026年4月25日", font: "Arial", size: 22, color: "6B7280" })],
        spacing: { before: 0, after: 120 },
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "対象環境: Railway PaaS（本番）", font: "Arial", size: 22, color: "6B7280" })],
        spacing: { before: 0, after: 1440 },
      }),

      pageBreak(),

      // ═════════════════════════════════════════
      // 目次
      // ═════════════════════════════════════════
      new TableOfContents("目次", {
        hyperlink: true,
        headingStyleRange: "1-3",
      }),

      pageBreak(),

      // ═════════════════════════════════════════
      // 1. システム概要
      // ═════════════════════════════════════════
      sectionTitle("1. システム概要"),
      p("本システムは、社内 API への全アクセスをリアルタイムで自動記録し、ルールベースおよび機械学習（AI）の 2 段階で不審なアクセスを検知・スコアリングするセキュリティ監査プラットフォームです。"),
      p(""),
      makeTable(
        ["項目", "内容"],
        [
          ["システム名", "GRC セキュリティ監査システム"],
          ["一言説明", "社内 API の不正アクセスを自動検知するセキュリティ監査ツール"],
          ["バージョン", "v1.0"],
          ["デプロイ先", "Railway PaaS（本番環境）"],
          ["アクセス URL", "https://fastapi-mysql-project-production.up.railway.app"],
        ],
        [3000, 6026]
      ),
      p(""),

      subTitle("主な機能"),
      bullet("全 API アクセスの自動ログ記録（HTTPミドルウェア）"),
      bullet("ルールベース検知：6 つのルールで即時リスク判定"),
      bullet("AI 異常検知：Isolation Forest + AutoEncoder の 2 モデルによる統合判定"),
      bullet("リスクスコアリングと推奨アクション生成"),
      bullet("GRC ダッシュボード：詳細モーダル・社内/外部バッジ・30 秒自動更新"),
      bullet("認証付き Swagger UI（管理者のみ閲覧可能）"),

      p(""),

      // ═════════════════════════════════════════
      // 2. 技術スタック
      // ═════════════════════════════════════════
      sectionTitle("2. 技術スタック"),
      makeTable(
        ["カテゴリ", "技術", "バージョン・備考"],
        [
          ["バックエンド", "FastAPI (Python)", "lifespan, APIRouter 使用"],
          ["データベース", "MySQL", "Railway マネージドDB"],
          ["ORM", "SQLAlchemy", "pymysql ドライバー"],
          ["デプロイ", "Railway PaaS", "Procfile: uvicorn main:app"],
          ["認証", "HMAC-SHA256", "httponly Cookie / 有効期限 8 時間"],
          ["ML モデル①", "Isolation Forest", "scikit-learn / contamination=0.15"],
          ["ML モデル②", "AutoEncoder", "PyTorch / Early Stopping"],
          ["特徴量処理", "Polars", "高速 DataFrame"],
          ["テンプレート", "Jinja2", "login / docs / dashboard"],
          ["スキーマ検証", "Pydantic v2", "response_model 付き"],
        ],
        [2200, 2800, 4026]
      ),
      p(""),

      // ═════════════════════════════════════════
      // 3. ファイル構成
      // ═════════════════════════════════════════
      sectionTitle("3. ファイル構成"),
      makeTable(
        ["ファイル / ディレクトリ", "役割"],
        [
          [{ text: "main.py", mono: true }, "アプリエントリーポイント・ミドルウェア・ルーター登録"],
          [{ text: "config.py", mono: true }, "環境変数の一元管理"],
          [{ text: "auth.py", mono: true }, "HMAC 認証ヘルパー（make_token / verify_session）"],
          [{ text: "database.py", mono: true }, "SQLAlchemy エンジン・セッション・URL 正規化"],
          [{ text: "models.py", mono: true }, "ORM モデル定義（4 テーブル）"],
          [{ text: "schemas.py", mono: true }, "Pydantic スキーマ（リクエスト / レスポンス）"],
          [{ text: "routers/pages.py", mono: true }, "HTML ページルーター（/docs, /dashboard, login/logout）"],
          [{ text: "routers/users.py", mono: true }, "ユーザー API（POST /users, GET /users）"],
          [{ text: "routers/audit.py", mono: true }, "監査 API（/audit-logs, /run-audit, /findings, /scores）"],
          [{ text: "routers/ai.py", mono: true }, "AI 検知 API（POST /ai-detect）"],
          [{ text: "templates/login.html", mono: true }, "ログイン画面（Jinja2）"],
          [{ text: "templates/docs.html", mono: true }, "カスタム Swagger UI（ダーク・サイドバー付き）"],
          [{ text: "templates/dashboard.html", mono: true }, "GRC ダッシュボード（モーダル・Chart.js）"],
          [{ text: "detectors/rules.py", mono: true }, "ルールベース検知エンジン（6 ルール）"],
          [{ text: "risk/scorer.py", mono: true }, "リスクスコアリング（IP/ユーザー別集計）"],
          [{ text: "recommendations/engine.py", mono: true }, "推奨アクション生成（urgency 順ソート）"],
          [{ text: "ml/features.py", mono: true }, "特徴量エンジニアリング（Polars group_by, 8 次元）"],
          [{ text: "ml/models.py", mono: true }, "ML モデル実装（Isolation Forest + AutoEncoder）"],
          [{ text: "ml/detector.py", mono: true }, "AI 検知オーケストレーション・パターン分析"],
          [{ text: "seed.py", mono: true }, "サンプルデータ投入スクリプト（ハッカー 4 シナリオ含む）"],
        ],
        [3200, 5826]
      ),
      p(""),

      pageBreak(),

      // ═════════════════════════════════════════
      // 4. データベース設計
      // ═════════════════════════════════════════
      sectionTitle("4. データベース設計"),
      p("4 つのテーブルで構成されます。audit_findings と risk_scores は run_id（UUID）で監査実行単位にグループ化されます。"),
      p(""),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "4.1  users", font: "Courier New", size: 26, bold: true, color: "2563EB" })],
        spacing: { before: 240, after: 120 },
      }),
      makeTable(
        ["カラム", "型", "制約", "説明"],
        [
          ["id", "INT", "PK / AUTO_INCREMENT", "ユーザーID"],
          ["name", "VARCHAR(100)", "NOT NULL", "氏名"],
          ["email", "VARCHAR(100)", "UNIQUE", "メールアドレス"],
        ],
        [2000, 2200, 2400, 2426]
      ),
      p(""),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "4.2  audit_logs", font: "Courier New", size: 26, bold: true, color: "2563EB" })],
        spacing: { before: 240, after: 120 },
      }),
      p("全 API リクエストをミドルウェアで自動記録するテーブル。"),
      makeTable(
        ["カラム", "型", "制約", "説明"],
        [
          ["id", "INT", "PK", "ログID"],
          ["ip_address", "VARCHAR(45)", "", "アクセス元 IP（IPv6 対応）"],
          ["method", "VARCHAR(10)", "", "HTTP メソッド（GET/POST/DELETE 等）"],
          ["endpoint", "VARCHAR(255)", "", "リクエストパス"],
          ["status_code", "INT", "", "HTTP レスポンスコード"],
          ["user_id", "INT", "FK → users / NULL可", "登録済みユーザーと紐づけ"],
          ["timestamp", "DATETIME", "", "アクセス日時（JST）"],
        ],
        [2000, 2200, 2400, 2426]
      ),
      p(""),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "4.3  audit_findings", font: "Courier New", size: 26, bold: true, color: "2563EB" })],
        spacing: { before: 240, after: 120 },
      }),
      p("POST /run-audit 実行時に生成される検知結果。run_id でまとめて取得可能。"),
      makeTable(
        ["カラム", "型", "制約", "説明"],
        [
          ["id", "INT", "PK", ""],
          ["run_id", "VARCHAR(36)", "INDEX", "監査実行 UUID"],
          ["rule_id", "VARCHAR(50)", "", "検知ルール（LOGIN_001 等）"],
          ["risk_level", "VARCHAR(10)", "", "high / medium / low"],
          ["user_id", "INT", "FK / NULL可", ""],
          ["ip_address", "VARCHAR(45)", "", ""],
          ["description", "VARCHAR(500)", "", "検知内容の説明文"],
          ["recommendation", "VARCHAR(500)", "", "推奨対応アクション"],
          ["urgency", "VARCHAR(20)", "", "immediate / high / medium"],
          ["score", "INT", "", "このルールのスコア加算値"],
          ["evidence", "TEXT", "", "関連ログ ID リスト（JSON）"],
          ["created_at", "DATETIME", "", "監査実行日時"],
        ],
        [2000, 2200, 1600, 3226]
      ),
      p(""),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "4.4  risk_scores", font: "Courier New", size: 26, bold: true, color: "2563EB" })],
        spacing: { before: 240, after: 120 },
      }),
      p("ユーザーまたは IP ごとのリスクスコア集計結果。"),
      makeTable(
        ["カラム", "型", "制約", "説明"],
        [
          ["id", "INT", "PK", ""],
          ["run_id", "VARCHAR(36)", "INDEX", "監査実行 UUID"],
          ["user_id", "INT", "FK / NULL可", ""],
          ["ip_address", "VARCHAR(45)", "", ""],
          ["score", "INT", "", "累積リスクスコア"],
          ["risk_level", "VARCHAR(10)", "", "high / medium / low"],
          ["breakdown", "TEXT", "", "ルール別スコア内訳（JSON）"],
          ["calculated_at", "DATETIME", "", "スコア計算日時"],
        ],
        [2000, 2200, 1600, 3226]
      ),
      p(""),

      pageBreak(),

      // ═════════════════════════════════════════
      // 5. API エンドポイント一覧
      // ═════════════════════════════════════════
      sectionTitle("5. API エンドポイント一覧"),
      makeTable(
        ["メソッド", "パス", "説明", "認証"],
        [
          ["GET", "/docs", "カスタム Swagger UI", "Cookie 必須"],
          ["POST", "/docs/login", "ドキュメントへのログイン", "なし"],
          ["GET", "/docs/logout", "ログアウト・Cookie 削除", "なし"],
          ["GET", "/openapi.json", "OpenAPI スキーマ取得", "Cookie 必須"],
          ["GET", "/dashboard", "GRC ダッシュボード画面", "Cookie 必須"],
          ["GET", "/dashboard/login", "ダッシュボードログイン画面", "なし"],
          ["POST", "/dashboard/login", "ダッシュボードへのログイン", "なし"],
          ["POST", "/users", "ユーザー登録（name・email 必須）", "なし"],
          ["GET", "/users", "登録ユーザー一覧", "なし"],
          ["GET", "/audit-logs", "アクセスログ一覧（新しい順）", "なし"],
          ["POST", "/run-audit", "監査エンジン実行・DB 保存", "なし"],
          ["GET", "/audit-findings", "最新監査の検出結果一覧", "なし"],
          ["GET", "/risk-scores", "最新監査のリスクスコア降順", "なし"],
          ["POST", "/ai-detect", "AI 異常検知実行", "なし"],
        ],
        [1400, 2800, 3200, 1626]
      ),
      p(""),

      // ═════════════════════════════════════════
      // 6. 機能仕様
      // ═════════════════════════════════════════
      sectionTitle("6. 機能仕様"),

      subTitle("6.1 認証機能"),
      bullet("管理者用 ID/パスワードは環境変数で管理（ADMIN_USERNAME / ADMIN_PASSWORD）"),
      bullet("ログイン成功時：HMAC-SHA256 でセッショントークンを生成し httponly Cookie に保存"),
      bullet("セッション有効期限：8 時間"),
      bullet("未ログイン状態で /docs または /dashboard にアクセス → ログイン画面を表示"),
      bullet("XSS 対策：Cookie に httponly / SameSite=Lax を設定"),
      bullet("CSRF 対策：SameSite 属性により外部サイトからの Cookie 送信を制限"),
      p(""),

      subTitle("6.2 自動ログ記録（HTTPミドルウェア）"),
      bullet("全リクエストをミドルウェアで自動キャプチャし audit_logs テーブルへ記録"),
      bullet("記録項目：IP アドレス / HTTP メソッド / エンドポイント / ステータスコード / タイムスタンプ（JST）/ ユーザーID"),
      bullet("除外パス：/dashboard, /docs, /docs/login, /docs/logout, /dashboard/login, /openapi.json, /favicon.ico"),
      bullet("X-Forwarded-For ヘッダーを優先してリアル IP を取得（リバースプロキシ対応）"),
      p(""),

      subTitle("6.3 ルールベース検知"),
      p("POST /run-audit 実行時に全ログをスキャンし、以下のルールで Detection を生成します。"),
      p(""),
      makeTable(
        ["ルールID", "リスク", "検知条件", "スコア"],
        [
          ["LOGIN_001", "High", "深夜 0〜5 時のアクセス", "+2"],
          ["LOGIN_002", "Medium", "夜間 22〜23 時のアクセス", "+1"],
          ["ACTION_001", "High", "DELETE リクエストを検出", "+3"],
          ["ACTION_002", "High", "5xx サーバーエラーを検出", "+3"],
          ["RATE_001", "High", "単一 IP が全リクエストの 50% 超", "+3"],
          ["ADMIN_001", "Medium", "同一ユーザーが 20 件超のアクセス", "+2"],
        ],
        [1800, 1400, 3800, 2026]
      ),
      p(""),
      p("スコア判定基準：累積スコア ≥ 6 → High　/ ≥ 3 → Medium　/ それ以下 → Low"),
      p(""),

      subTitle("6.4 AI 異常検知"),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun({ text: "特徴量エンジニアリング（8 次元）", font: "Arial" })],
        spacing: { before: 180, after: 80 },
      }),
      p("audit_logs を IP ごとに Polars で集計し、8 次元の特徴量ベクトルを生成します。"),
      p(""),
      makeTable(
        ["特徴量", "説明", "検知対象"],
        [
          ["failed_count", "401 エラー数", "ブルートフォース"],
          ["total_requests", "総リクエスト数", "集中アクセス"],
          ["night_access_count", "深夜帯（0〜5 時）アクセス数", "深夜侵入"],
          ["admin_ratio", "DELETE リクエスト率", "データ破壊"],
          ["unique_status_count", "ステータスコードの種類数", "異常挙動"],
          ["error_rate", "4xx / 5xx エラー率", "攻撃試行"],
          ["unique_endpoint_count", "アクセスエンドポイント種類数", "エンドポイントスキャン"],
          ["error_404_rate", "404 エラー率", "パス探索（スキャン）"],
        ],
        [2600, 3200, 3226]
      ),
      p(""),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun({ text: "モデル①：Isolation Forest", font: "Arial" })],
        spacing: { before: 180, after: 80 },
      }),
      bullet("ライブラリ：scikit-learn"),
      bullet("前処理：StandardScaler で正規化"),
      bullet("パラメータ：contamination=0.15、n_estimators=100、random_state=42"),
      bullet("出力：-1（異常）/ 1（正常）"),
      p(""),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun({ text: "モデル②：AutoEncoder（Early Stopping）", font: "Arial" })],
        spacing: { before: 180, after: 80 },
      }),
      bullet("ライブラリ：PyTorch"),
      bullet("アーキテクチャ：Input → Hidden(dim×2) → Bottleneck(dim//2) → Hidden → Output"),
      bullet("活性化関数：ReLU"),
      bullet("最適化：Adam（lr=0.001）"),
      bullet("学習方式：train 80% / test 20% に分割し Early Stopping を適用"),
      bullet("Early Stopping：max_epochs=300、patience=15（検証損失が 15 エポック改善なし → 終了）"),
      bullet("異常判定閾値：全データの再構成誤差の 平均 + 2σ"),
      bullet("最適エポック数をレスポンスに含めて返却"),
      p(""),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun({ text: "統合判定ロジック", font: "Arial" })],
        spacing: { before: 180, after: 80 },
      }),
      p("Isolation Forest または AutoEncoder のいずれかが異常を検知した場合、is_anomaly = True と判定します（OR 条件）。"),
      p(""),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun({ text: "パターン分析", font: "Arial" })],
        spacing: { before: 180, after: 80 },
      }),
      p("各 IP の特徴量と実ログを解析し、以下の不審パターンを自動分類してレスポンスに含めます。"),
      makeTable(
        ["パターンタイプ", "判定条件", "重要度"],
        [
          ["ブルートフォース攻撃", "failed_count ≥ 5", "High"],
          ["認証失敗の繰り返し", "failed_count ≥ 2", "Medium"],
          ["エンドポイントスキャン", "unique_endpoint_count ≥ 8", "High"],
          ["複数エンドポイント探索", "unique_endpoint_count ≥ 5", "Medium"],
          ["存在しないパスの探索", "error_404_rate ≥ 15%", "Medium〜High"],
          ["深夜帯の大量アクセス", "night_access_count ≥ 5", "High"],
          ["深夜帯アクセス", "night_access_count ≥ 1", "Medium"],
          ["異常なエラー率", "error_rate ≥ 50%", "High"],
          ["大量データ削除操作", "admin_ratio ≥ 30%", "High"],
        ],
        [2800, 3000, 3226]
      ),
      p(""),

      subTitle("6.5 ダッシュボード"),
      bullet("URL：/dashboard（Cookie 認証必須）"),
      bullet("メトリクスカード：総リクエスト数 / High findings 数 / 異常 IP 数 / 最適エポック数"),
      bullet("AI 異常検知テーブル：全 IP の特徴量・判定結果を一覧表示"),
      bullet("  行クリック → 詳細モーダル表示（検知パターン + 直近ログ 10 件）", 1),
      bullet("  社内ユーザー：[社内] バッジ（青）/ 未登録 IP：[外部] バッジ（黄）", 1),
      bullet("リスクスコアランキング：累積スコア降順で上位 8 件を表示"),
      bullet("推奨アクション：urgency 順（immediate → high → medium）でリスト表示"),
      bullet("ステータスコード分布：Chart.js によるドーナツグラフ（2xx / 3xx / 4xx-5xx）"),
      bullet("自動更新：30 秒ごとに /audit-logs を再取得"),
      p(""),

      pageBreak(),

      // ═════════════════════════════════════════
      // 7. 環境変数・設定
      // ═════════════════════════════════════════
      sectionTitle("7. 環境変数・設定"),
      makeTable(
        ["変数名", "説明", "デフォルト"],
        [
          ["DATABASE_URL", "MySQL 接続 URL（mysql+pymysql://...）", "なし（必須）"],
          ["MYSQL_PUBLIC_URL", "Railway 外部アクセス用 URL（内部 URL のフォールバック）", "なし"],
          ["ADMIN_USERNAME", "管理者ログイン ID", "admin"],
          ["ADMIN_PASSWORD", "管理者パスワード", "changeme"],
          ["SESSION_SECRET", "HMAC 署名キー（本番では必ず変更）", "起動時ランダム生成"],
        ],
        [2800, 4000, 2226]
      ),
      p(""),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "7.1 MySQL URL 正規化ロジック", font: "Arial", bold: true, color: "2563EB" })],
        spacing: { before: 240, after: 120 },
      }),
      bullet("DATABASE_URL が未設定の場合、MYSQL_PUBLIC_URL を使用"),
      bullet("内部ホスト（.railway.internal）を含む場合、MYSQL_PUBLIC_URL にフォールバック"),
      bullet("mysql:// または mysql+mysqldb:// プレフィックスは mysql+pymysql:// に自動変換"),
      p(""),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "7.2 起動フロー", font: "Arial", bold: true, color: "2563EB" })],
        spacing: { before: 240, after: 120 },
      }),
      bullet("Procfile：uvicorn main:app --host 0.0.0.0 --port $PORT"),
      bullet("lifespan イベントで Base.metadata.create_all() を実行（テーブル自動作成）"),
      bullet("失敗時は WARNING ログを出力して起動を継続"),
      p(""),
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  const outPath = "C:\\Users\\t-kum\\OneDrive - Sophia Univ. Students\\デスクトップ\\fastapi-mysql-project\\仕様書.docx";
  fs.writeFileSync(outPath, buffer);
  console.log("OK: " + outPath);
}).catch(e => {
  console.error("ERROR:", e.message);
});
