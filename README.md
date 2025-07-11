# Genie アドバイザーアプリ

Databricks Genie MCPサーバーを使用して、データに対して自然言語で質問を行い、結果を表示・分析するStreamlitアプリケーションです。

## 概要

このアプリケーションは、[Databricks Genie MCPサーバー](https://docs.databricks.com/gcp/ja/generative-ai/agent-framework/mcp)を使用して、Unity Catalog内のテーブルに対して自然言語で質問を行い、構造化データから知見を得ることができます。さらに、取得したデータをAIが分析し、ビジネス上の洞察を提供します。

## 機能

- 🔍 **Genie MCPサーバーとの通信**: DatabricksのマネージドMCPサーバーを使用
- 💬 **自然言語質問**: データに対して自然言語で質問
- 📊 **結果表示**: テキスト回答とデータフレームの表示
- 📈 **データ可視化**: 結果データの自動可視化（ラインチャート、バーチャート、散布図、ヒストグラム、円グラフ）
- 🤖 **AI分析**: LLMによるデータ分析とビジネス洞察の提供
- 💭 **追加質問**: 分析結果に対するフォローアップ質問機能
- 🔍 **実行クエリ表示**: Genieが実行したSQLクエリの確認機能
- 📋 **統計情報**: データの基本統計、データ型、欠損値の情報表示
- ⚙️ **設定可能**: Genie Space IDの設定

## 前提条件

1. **Databricksワークスペース**: アクセス可能なDatabricksワークスペース
2. **Genieスペース**: 問い合わせを行いたいGenieスペースが設定済み
3. **権限**: Genieスペースへのアクセス権限
4. **Model Serving Endpoint**: AI分析用のLLMエンドポイント（例：`databricks-claude-sonnet-4`）
5. **Databricks CLI**: 認証設定済み

## 必要な権限

Genie MCPサーバーにアクセスするには、以下の権限が必要です：

- `genie:read` - Genieスペースの読み取り権限
- `mcp:access` - MCPサーバーへのアクセス権限

### 権限の確認方法

1. **Databricksワークスペースにログイン**
2. **Genieページにアクセス**: `https://<workspace>/genie`
3. **Genieスペースにアクセスできるか確認**
4. **管理者に権限の付与を依頼**

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

必要なパッケージ：
- `streamlit`
- `pandas`
- `databricks-sdk`
- `requests`
- `python-dotenv`
- `mlflow`

### 2. 環境変数の設定

#### ローカル開発の場合
`.env`ファイルを作成してください：

```env
DATABRICKS_HOST=https://your-workspace.azuredatabricks.net
DATABRICKS_ACCESS_TOKEN=your-access-token
SERVING_ENDPOINT=your-llm-endpoint-name
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

#### Databricks Appsの場合
`app.yaml`で環境変数を設定します：

```yaml
env:
  - name: "DATABRICKS_HOST"
    value: "https://your-workspace.azuredatabricks.net"
  - name: "DATABRICKS_ACCESS_TOKEN"
    valueFrom: "secret/databricks/access-token"
  - name: "SERVING_ENDPOINT"
    value: "your-llm-endpoint-name"
```

### 3. Databricks Secretsの設定

```bash
# シークレットスコープの作成
databricks secrets create-scope --scope databricks

# アクセストークンの設定
databricks secrets put --scope databricks --key access-token
```

### 4. Genie Space IDの取得

1. Databricksワークスペースにログイン
2. Genieページに移動: `https://<workspace>/genie`
3. 使用したいGenieスペースを選択
4. URLからSpace IDを取得: `https://<workspace>/genie/<space-id>`

## 使用方法

### ローカル実行

```bash
streamlit run app.py
```

### Databricks Appsとしてデプロイ

1. アプリケーションを作成:
```bash
databricks apps create genie-advisor-app
```

2. シークレットの設定:
```bash
databricks secrets create-scope --scope databricks
databricks secrets put --scope databricks --key access-token
```

3. ソースコードをアップロード:
```bash
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
databricks sync . "/Users/$DATABRICKS_USERNAME/genie-advisor-app"
databricks apps deploy genie-advisor-app --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/genie-advisor-app"
```

## アプリケーションの使用手順

1. **Genie Space IDの設定**
   - サイドバーでGenie Space IDを入力（デフォルト：`01efbd0fe8711ecd80e48dcbc4042f28`）

2. **質問の入力**
   - テキストエリアに自然言語で質問を入力
   - 例：「月別の問い合わせ数」

3. **質問の送信**
   - 「🚀 質問を送信」ボタンをクリック

4. **結果の確認**
   - **データ表示**: 取得したデータのテーブル表示
   - **可視化**: 各種チャート（ライン、バー、散布図、ヒストグラム、円グラフ）
   - **実行クエリ**: Genieが実行したSQLクエリの確認
   - **統計情報**: データの基本統計、データ型、欠損値情報

5. **AI分析の実行**
   - 「分析を実行」ボタンをクリック
   - AIがデータを分析してビジネス洞察を提供

6. **追加質問**
   - 分析結果に対してフォローアップ質問が可能
   - チャット形式で対話的に分析を深掘り

## サンプル質問

- "月別の問い合わせ数"
- "売上データの傾向を分析してください"
- "最も売上が高い商品は何ですか？"
- "月別の売上推移を教えてください"
- "顧客の購買パターンを分析してください"
- "データの統計情報を教えてください"
- "異常値や外れ値はありますか？"
- "相関関係の強い列はありますか？"

## 技術仕様

### 使用技術

- **Streamlit**: Webアプリケーションフレームワーク
- **Databricks SDK**: Databricksワークスペースとの連携
- **MCP (Model Context Protocol)**: 標準化されたツールアクセスプロトコル
- **Pandas**: データ処理と可視化
- **MLflow**: Model Serving Endpointとの通信
- **python-dotenv**: 環境変数管理

### アーキテクチャ

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │  Genie MCP       │    │  Unity Catalog  │
│   App           │───▶│  Server          │───▶│  Tables         │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │
         │
         ▼
┌─────────────────┐
│  Model Serving  │
│  Endpoint       │
│  (LLM)          │
└─────────────────┘
```

### API エンドポイント

Genie MCPサーバーのエンドポイント:
```
https://<workspace-hostname>/api/2.0/mcp/genie/{genie_space_id}
```

## トラブルシューティング

### よくある問題

#### 1. 認証エラー (HTTP 403)

**エラーメッセージ**: `"Provided OAuth token does not have required scopes"`

**解決方法**:
1. **Databricks管理者に連絡**して以下の権限の付与を依頼:
   - `genie:read` - Genieスペースの読み取り権限
   - `mcp:access` - MCPサーバーへのアクセス権限

2. **新しいアクセストークンを生成**:
   - Databricksワークスペースの設定 → ユーザー設定 → アクセストークン

3. **Genieスペースへのアクセス権限を確認**:
   - Genieページでスペースにアクセスできるか確認

#### 2. Genie Space IDエラー

**解決方法**:
- Space IDの正確性を確認
- アクセス権限を確認
- Genieページでスペースが表示されるか確認

#### 3. ネットワークエラー

**解決方法**:
- ワークスペースの接続性を確認
- ファイアウォール設定を確認
- VPN接続が必要な場合は確認

#### 4. トークン取得エラー

**解決方法**:
- 認証方法を変更（自動検出 → 手動入力）
- 環境変数 `DATABRICKS_TOKEN` を設定
- Databricks CLIの設定を確認

### デバッグ機能の使用

1. **デバッグモードを有効化**: サイドバーの「デバッグモード」をチェック
2. **接続テストを実行**: 「🔗 接続テスト」ボタンをクリック
3. **エラー詳細を確認**: デバッグ情報で詳細なエラー内容を確認

### ログの確認

```bash
# アプリケーションログの確認
databricks apps logs genie-mcp-query-app

# Databricks CLIログの確認
databricks workspace list --debug
```

## 環境変数一覧

| 環境変数 | 説明 | 設定例 |
|----------|------|---------|
| `DATABRICKS_HOST` | Databricksワークスペースのホスト名 | `https://adb-984752964297111.11.azuredatabricks.net` |
| `DATABRICKS_ACCESS_TOKEN` | Databricksアクセストークン | `dapi7d670d3ea0c261e2...` |
| `SERVING_ENDPOINT` | Model Serving Endpointの名前 | `databricks-claude-sonnet-4` |
| `STREAMLIT_BROWSER_GATHER_USAGE_STATS` | Streamlit使用統計の収集を無効化 | `false` |

## 参考資料

- [Databricks MCP ドキュメント](https://docs.databricks.com/gcp/ja/generative-ai/agent-framework/mcp)
- [Genie ドキュメント](https://docs.databricks.com/gcp/ja/genie/)
- [Streamlit ドキュメント](https://docs.streamlit.io/)
- [Databricks SDK ドキュメント](https://docs.databricks.com/dev-tools/sdk-python.html)
- [Databricks アクセストークン管理](https://docs.databricks.com/dev-tools/auth.html#access-tokens)

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

プルリクエストやイシューの報告を歓迎します。 