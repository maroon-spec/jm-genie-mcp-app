# Genie MCP 問い合わせアプリ

Databricks Genie MCPサーバーを使用して、データに対して自然言語で質問を行い、結果を表示するStreamlitアプリケーションです。

## 概要

このアプリケーションは、[Databricks Genie MCPサーバー](https://docs.databricks.com/gcp/ja/generative-ai/agent-framework/mcp)を使用して、Unity Catalog内のテーブルに対して自然言語で質問を行い、構造化データから知見を得ることができます。

## 機能

- 🔍 **Genie MCPサーバーとの通信**: DatabricksのマネージドMCPサーバーを使用
- 💬 **自然言語質問**: データに対して自然言語で質問
- 📊 **結果表示**: テキスト回答とデータフレームの表示
- 📈 **データ可視化**: 結果データの自動可視化（ラインチャート、バーチャート、散布図、ヒストグラム）
- ⚙️ **設定可能**: Genie Space IDの設定
- 📝 **サンプル質問**: よく使用される質問のテンプレート
- 🔐 **複数認証方法**: ヘッダートークン、環境変数、手動入力に対応
- 🐛 **デバッグ機能**: 問題の診断に役立つ詳細情報

## 前提条件

1. **Databricksワークスペース**: アクセス可能なDatabricksワークスペース
2. **Genieスペース**: 問い合わせを行いたいGenieスペースが設定済み
3. **権限**: Genieスペースへのアクセス権限
4. **Databricks CLI**: 認証設定済み

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

### 2. Databricks CLIの設定

```bash
databricks configure
```

### 3. アクセストークンの生成

1. Databricksワークスペースにログイン
2. 右上のユーザーアイコン → ユーザー設定
3. アクセストークン → 新しいトークンを生成
4. トークンを安全な場所に保存

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
databricks apps create genie-mcp-query-app
```

2. シークレットの設定:
```bash
databricks secrets create-scope genie-mcp-app
databricks secrets put-secret genie-mcp-app databricks-token --string-value "your-access-token"
```

3. ソースコードをアップロード:
```bash
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
databricks sync . "/Users/$DATABRICKS_USERNAME/genie-mcp-query-app"
databricks apps deploy genie-mcp-query-app --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/genie-mcp-query-app"
```

## アプリケーションの使用手順

1. **Genie Space IDの設定**
   - サイドバーでGenie Space IDを入力

2. **認証方法の選択**
   - 自動検出、ヘッダートークン、環境変数、手動入力から選択

3. **接続テスト**
   - 「接続テスト」ボタンでMCPサーバーとの接続を確認

4. **質問の入力**
   - カスタム質問を入力するか、サンプル質問を選択

5. **質問の送信**
   - 「質問を送信」ボタンをクリック

6. **結果の確認**
   - テキスト回答の確認
   - データフレームの表示
   - データの可視化

## サンプル質問

- "このデータセットの概要を教えてください"
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

### アーキテクチャ

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │  Genie MCP       │    │  Unity Catalog  │
│   App           │───▶│  Server          │───▶│  Tables         │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
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

## 認証方法

### 1. 自動検出（推奨）
- ヘッダートークン、環境変数、SDK設定を自動的に検出

### 2. ヘッダートークン
- Databricks Apps環境での自動認証

### 3. 環境変数
- `DATABRICKS_TOKEN` 環境変数を使用

### 4. 手動入力
- ユーザーが直接トークンを入力

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