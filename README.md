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

### 2. 環境変数の設定

#### Databricks Appsの場合
`app.yaml`で環境変数を設定します：


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
