import os
import streamlit as st
import pandas as pd
from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config
import json
from typing import Dict, Any, List
from mcp_client import GenieMCPClient, GenieMCPResponseParser
from model_serving_utils import query_endpoint
import requests
# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available in Databricks Apps environment
    pass

st.set_page_config(
    page_title="Genie Advisor App",
    layout="wide"
)

# サイドバー設定
st.sidebar.title("🔧 設定")
default_genie_space_id = "01efbd0fe8711ecd80e48dcbc4042f28"
genie_space_id = st.sidebar.text_input(
    "Genie Space ID",
    value=default_genie_space_id,
    help="DatabricksのGenie Space IDを入力してください"
)

def get_workspace_info() -> tuple:
    """ワークスペース情報を取得"""
    try:
        workspace_client = WorkspaceClient()
        current_user = workspace_client.current_user.me()
        workspace_hostname = Config().host
        return workspace_hostname, current_user.user_name
    except Exception as e:
        st.error(f"ワークスペース情報の取得に失敗しました: {str(e)}")
        return None, None

def extract_dataframe_from_genie_response(result: Dict[str, Any]) -> pd.DataFrame:
    content = result.get("content")
    if isinstance(content, list) and content and "text" in content[0]:
        text = content[0]["text"]
        
        # デバッグ: レスポンスの内容を確認
        if not text or text.strip() == "":
            st.warning("Genieのレスポンスが空です")
            return pd.DataFrame()
            
        try:
            parsed = json.loads(text)
            sr = parsed.get("statement_response")
            if sr and "manifest" in sr and "result" in sr:
                columns = [col["name"] for col in sr["manifest"]["schema"]["columns"]]
                rows = []
                for row in sr["result"].get("data_array", []):
                    row_values = []
                    for v in row["values"]:
                        if "string_value" in v:
                            row_values.append(v["string_value"])
                        elif "long_value" in v:
                            row_values.append(v["long_value"])
                        elif "double_value" in v:
                            row_values.append(v["double_value"])
                        else:
                            row_values.append(None)
                    rows.append(row_values)
                df = pd.DataFrame(rows, columns=columns)
                # 数値変換
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                # 日付変換の改善
                for col in df.columns:
                    if any(x in col.lower() for x in ['date', 'month', 'time', 'day', 'year']):
                        try:
                            # まず文字列として扱い、複数の日付フォーマットを試行
                            df[col] = pd.to_datetime(df[col], errors='coerce', infer_datetime_format=True, utc=True)
                            # UTCからローカルタイムゾーンに変換してからnaiveに変換
                            if df[col].notna().any():
                                df[col] = df[col].dt.tz_convert(None)  # naiveなdatetimeに変換
                                continue
                            else:
                                # 全てNaTの場合は元に戻す
                                df[col] = pd.to_numeric(df[col], errors='ignore')
                        except Exception:
                            pass
                return df
            # fallback: 旧ロジック
            #st.write("DEBUG: parsed text json", parsed)
        except json.JSONDecodeError as e:
            # JSONパースエラーを静かに処理
            pass
        except Exception as e:
            st.warning(f"データ抽出エラー: {e}")
    return pd.DataFrame()

def extract_query_from_genie_response(result: Dict[str, Any]) -> str:
    """Genie MCPレスポンスから実行されたクエリーを抽出"""
    content = result.get("content")
    if isinstance(content, list) and content and "text" in content[0]:
        text = content[0]["text"]
        if not text or text.strip() == "":
            return ""
        try:
            parsed = json.loads(text)
            # まず "query" フィールドを確認
            if "query" in parsed:
                return parsed["query"]
            # フォールバック: statement_response内のstatement
            sr = parsed.get("statement_response")
            if sr and "statement" in sr:
                return sr["statement"]
        except json.JSONDecodeError:
            # JSONパースエラーの場合は静かに処理
            pass
        except Exception as e:
            st.warning(f"クエリー抽出エラー: {e}")
    return ""

def extract_comment_from_genie_response(result: Dict[str, Any]) -> str:
    """Genie MCPレスポンスからコメントを抽出"""
    content = result.get("content")
    if isinstance(content, list) and content and "text" in content[0]:
        text = content[0]["text"]
        if not text or text.strip() == "":
            return ""
        try:
            parsed = json.loads(text)
            # コメントまたは説明文を探す
            if "comment" in parsed:
                return parsed["comment"]
            elif "description" in parsed:
                return parsed["description"]
            elif "explanation" in parsed:
                return parsed["explanation"]
            # statement_responseの中にコメントがある場合
            sr = parsed.get("statement_response")
            if sr:
                if "comment" in sr:
                    return sr["comment"]
                elif "description" in sr:
                    return sr["description"]
        except json.JSONDecodeError:
            # JSONパースエラーの場合は静かに処理
            pass
        except Exception as e:
            st.warning(f"コメント抽出エラー: {e}")
    
    # JSONとして解析できない場合は、プレーンテキストとして扱う
    if isinstance(content, list) and content and "text" in content[0]:
        text = content[0]["text"]
        # JSONデータの場合は、コメントとして返さない
        if text and text.strip() != "" and not text.strip().startswith('{"'):
            return text
    
    return ""


def format_sql_query(query: str) -> str:
    """SQLクエリを見やすく改行して整形"""
    if not query:
        return ""
    
    # SQLキーワードで改行を追加
    keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN']
    
    formatted_query = query
    for keyword in keywords:
        # キーワードの前に改行を追加
        formatted_query = formatted_query.replace(f' {keyword}', f'\n{keyword}')
        formatted_query = formatted_query.replace(f' {keyword.lower()}', f'\n{keyword}')
    
    # 最初の改行を削除
    formatted_query = formatted_query.lstrip('\n')
    
    return formatted_query

def analyze_dataframe_with_llm(df: pd.DataFrame, question: str) -> tuple[str, list[str]]:
    """DataFrameをLLMで分析してコメントと次の質問候補を生成"""
    try:
        # DataFrameを文字列形式に変換
        df_summary = f"""
データ概要:
- 行数: {len(df)}
- 列数: {len(df.columns)}
- 列名: {', '.join(df.columns.tolist())}

データサンプル (最初の5行):
{df.head().to_string()}

基本統計:
{df.describe().to_string()}
"""
        
        # 分析プロンプトを作成
        analysis_prompt = f"""
あなたはデータアナリストです。以下のデータについて分析し、必ずJSON形式で回答してください。

元の質問: {question}

{df_summary}

回答は必ず以下のJSON形式にしてください（他の文章は一切含めないでください）：

{{
  "analysis": "データの分析結果を200文字以内で日本語で記述",
  "follow_up_questions": [
    "このデータを見た人が次に聞きたくなる具体的な質問1",
    "このデータを見た人が次に聞きたくなる具体的な質問2",
    "このデータを見た人が次に聞きたくなる具体的な質問3"
  ]
}}

分析では以下を含めてください:
- データの主要な傾向や特徴
- 注目すべき数値やパターン
- ビジネス上の洞察

follow_up_questionsは、実際にこのデータを見た人が詳しく知りたくなる実用的な質問にしてください。
"""
        
        # LLMに送信するメッセージ形式
        messages = [{"role": "user", "content": analysis_prompt}]
        
        # SERVING_ENDPOINTに問い合わせ
        response = query_endpoint(
            endpoint_name=os.getenv("SERVING_ENDPOINT"),
            messages=messages,
            max_tokens=500,
        )
        
        # JSONレスポンスをパース
        try:
            import json
            result = json.loads(response["content"])
            analysis = result.get("analysis", "分析結果を取得できませんでした")
            follow_up_questions = result.get("follow_up_questions", [])
            return analysis, follow_up_questions
        except json.JSONDecodeError:
            # JSONパースに失敗した場合は、レスポンス全体を分析結果として返す
            return response["content"], []
            
    except Exception as e:
        return f"分析中にエラーが発生しました: {str(e)}", []


def analyze_dataframe_with_followup(df: pd.DataFrame, original_question: str, followup_question: str) -> str:
    """DataFrameに対する追加質問に回答"""
    try:
        # DataFrameを文字列形式に変換
        df_summary = f"""
データ概要:
- 行数: {len(df)}
- 列数: {len(df.columns)}
- 列名: {', '.join(df.columns.tolist())}

データサンプル (最初の5行):
{df.head().to_string()}

基本統計:
{df.describe().to_string()}
"""
        
        # 追加質問プロンプトを作成
        followup_prompt = f"""
以下のデータについて追加の質問に答えてください。

元の質問: {original_question}
追加の質問: {followup_question}

{df_summary}

追加質問に対して、データに基づいた具体的で有用な回答を日本語で提供してください。
可能であれば具体的な数値やパターンを含めてください。
300文字以内で回答してください。
"""
        
        # LLMに送信するメッセージ形式
        messages = [{"role": "user", "content": followup_prompt}]
        
        # SERVING_ENDPOINTに問い合わせ
        response = query_endpoint(
            endpoint_name=os.getenv("SERVING_ENDPOINT"),
            messages=messages,
            max_tokens=400,
        )
        
        return response["content"]
    except Exception as e:
        return f"追加質問の回答中にエラーが発生しました: {str(e)}"


def display_query_result():
    df = st.session_state.get("genie_df")
    question = st.session_state.get("genie_question", "")
    executed_query = st.session_state.get("genie_executed_query", "")
    genie_comment = st.session_state.get("genie_comment", "")
    
    # Genieのコメントを表示（コメントがある場合のみ）
    if genie_comment and genie_comment.strip():
        st.subheader("💬 Genieからの回答")
        st.info(genie_comment)
    
    if df is not None and not df.empty:
        # データ型を事前に取得（両方のカラムで使用するため）
        numeric_columns = df.select_dtypes(include=['number']).columns
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns
        datetime_columns = df.select_dtypes(include=['datetime64[ns]', 'datetime']).columns
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("📊 データ")
            st.dataframe(df, use_container_width=True)
            
            # 実行されたクエリーを表示（データの下に表示）
            if executed_query:
                with st.expander("🔍 実行されたクエリー", expanded=False):
                    formatted_query = format_sql_query(executed_query)
                    st.code(formatted_query, language="sql")
            
            # 統計情報を表示（クエリーの下に表示）
            with st.expander("📋 統計情報"):
                st.write("**基本統計:**")
                st.write(df.describe())
                st.write("**データ型:**")
                st.write(df.dtypes)
                st.write("**欠損値:**")
                st.write(df.isnull().sum())
                if len(datetime_columns) > 0:
                    st.write("**日付列の情報:**")
                    for col in datetime_columns:
                        st.write(f"- {col}: {df[col].min()} ～ {df[col].max()}")
        
        with col2:
            st.subheader("📈 可視化")
            chart_type = st.selectbox(
                "チャートタイプ",
                ["line", "bar", "scatter", "histogram", "pie"],
                key="chart_type"
            )
            
            # Group By機能の追加
            group_by_options = ["なし"] + list(categorical_columns) + list(datetime_columns)
            group_by_col = st.selectbox("Group By（グループ化）", group_by_options, key="group_by_col")
            if chart_type == "line" and len(numeric_columns) > 0:
                # 日付列がある場合はX軸として使用可能
                if len(datetime_columns) > 0:
                    x_axis_col = st.selectbox("X軸（時間軸）", datetime_columns)
                    y_axis_cols = st.multiselect(
                        "Y軸（数値）を選択",
                        numeric_columns,
                        default=list(numeric_columns[:3])
                    )
                    if x_axis_col and y_axis_cols:
                        if group_by_col != "なし":
                            # Group Byありの場合
                            chart_data = df.groupby([x_axis_col, group_by_col])[y_axis_cols].sum().reset_index()
                            chart_data = chart_data.pivot(index=x_axis_col, columns=group_by_col, values=y_axis_cols[0])
                            st.line_chart(chart_data)
                        else:
                            # Group Byなしの場合
                            chart_data = df.set_index(x_axis_col)[y_axis_cols]
                            st.line_chart(chart_data)
                else:
                    selected_columns = st.multiselect(
                        "表示する列を選択",
                        numeric_columns,
                        default=list(numeric_columns[:3])
                    )
                    if selected_columns:
                        if group_by_col != "なし":
                            # Group Byありの場合
                            chart_data = df.groupby(group_by_col)[selected_columns].sum()
                            st.line_chart(chart_data)
                        else:
                            # Group Byなしの場合
                            st.line_chart(df[selected_columns])
            elif chart_type == "bar" and len(numeric_columns) > 0:
                # X軸の選択肢を準備（カテゴリ列と日付列）
                x_axis_options = list(categorical_columns) + list(datetime_columns)
                if len(x_axis_options) == 0:
                    x_axis_options = df.columns.tolist()
                x_col = st.selectbox("X軸（カテゴリ・日付）", x_axis_options)
                y_col = st.selectbox("Y軸（数値）", numeric_columns)
                if x_col and y_col:
                    if group_by_col != "なし" and group_by_col != x_col:
                        # Group Byありの場合
                        chart_data = df.groupby([x_col, group_by_col])[y_col].sum().reset_index()
                        chart_data = chart_data.pivot(index=x_col, columns=group_by_col, values=y_col)
                        st.bar_chart(chart_data)
                    else:
                        # Group Byなしの場合
                        chart_data = df.groupby(x_col)[y_col].sum().reset_index()
                        st.bar_chart(chart_data.set_index(x_col))
            elif chart_type == "scatter" and len(numeric_columns) >= 2:
                x_col = st.selectbox("X軸", numeric_columns, key="scatter_x")
                y_col = st.selectbox("Y軸", [col for col in numeric_columns if col != x_col], key="scatter_y")
                if x_col and y_col:
                    if group_by_col != "なし":
                        # Group Byありの場合は、色分けで表示
                        st.write("散布図では、Group Byによる色分けは現在サポートされていません")
                        st.scatter_chart(df, x=x_col, y=y_col)
                    else:
                        # Group Byなしの場合
                        st.scatter_chart(df, x=x_col, y=y_col)
            elif chart_type == "histogram" and len(numeric_columns) > 0:
                col = st.selectbox("列を選択", numeric_columns, key="histogram_col")
                if col:
                    if group_by_col != "なし":
                        # Group Byありの場合は、グループ別にヒストグラムを表示
                        st.write("ヒストグラムでは、Group Byによる分割表示は現在サポートされていません")
                        st.histogram_chart(df[col])
                    else:
                        # Group Byなしの場合
                        st.histogram_chart(df[col])
            elif chart_type == "pie" and len(categorical_columns) > 0:
                category_col = st.selectbox("カテゴリ列", categorical_columns, key="pie_category")
                if len(numeric_columns) > 0:
                    value_col = st.selectbox("値列", numeric_columns, key="pie_value")
                    if category_col and value_col:
                        if group_by_col != "なし" and group_by_col != category_col:
                            # Group Byありの場合は、複数の円グラフを表示
                            st.write("円グラフでは、Group Byによる分割表示は現在サポートされていません")
                            pie_data = df.groupby(category_col)[value_col].sum()
                            st.write("円グラフデータ:")
                            st.write(pie_data)
                            st.bar_chart(pie_data)
                        else:
                            # Group Byなしの場合
                            pie_data = df.groupby(category_col)[value_col].sum()
                            st.write("円グラフデータ:")
                            st.write(pie_data)
                            st.bar_chart(pie_data)
        
        
        # AI分析コメントを表示
        st.subheader("🤖 AI分析コメント")
        if st.button("分析を実行", key="analyze_button"):
            with st.spinner("データを分析中..."):
                analysis_comment, follow_up_questions = analyze_dataframe_with_llm(df, question)
                st.session_state["analysis_comment"] = analysis_comment
                st.session_state["follow_up_questions"] = follow_up_questions
                # 分析チャット履歴を初期化
                if "analysis_messages" not in st.session_state:
                    st.session_state["analysis_messages"] = []
                # 最初の分析結果をチャット履歴に追加
                st.session_state["analysis_messages"].append({"role": "assistant", "content": analysis_comment})
        
        # 保存された分析コメントがあれば表示
        if "analysis_comment" in st.session_state:
            st.info(st.session_state["analysis_comment"])
            
            # 分析結果に対する追加質問機能
            st.subheader("💭 AIに追加で質問")
            
            # AIが生成したサンプル質問の表示
            if "follow_up_questions" in st.session_state and st.session_state["follow_up_questions"]:
                st.markdown("**次におすすめの質問：**")
                sample_questions = st.session_state["follow_up_questions"]
            else:
                st.markdown("**よく使われる質問例：**")
                sample_questions = [
                    "このデータの主要な課題は何ですか？",
                    "改善すべき点を具体的に教えてください",
                    "注目すべき特徴やパターンはありますか？"
                ]
            
            cols = st.columns(len(sample_questions))
            for i, sample_q in enumerate(sample_questions):
                with cols[i]:
                    if st.button(f"📝 {sample_q}", key=f"sample_q_{i}"):
                        # サンプル質問をチャット履歴に追加
                        if "analysis_messages" not in st.session_state:
                            st.session_state["analysis_messages"] = []
                        st.session_state["analysis_messages"].append({"role": "user", "content": sample_q})
                        
                        # AIの応答を生成
                        with st.spinner("回答を生成中..."):
                            follow_up_response = analyze_dataframe_with_followup(df, question, sample_q)
                            st.session_state["analysis_messages"].append({"role": "assistant", "content": follow_up_response})
                        st.rerun()
            
            # 分析チャット履歴の初期化
            if "analysis_messages" not in st.session_state:
                st.session_state["analysis_messages"] = []
            
            # 分析チャット履歴の表示（最初のAI分析コメントは除外）
            for i, msg in enumerate(st.session_state["analysis_messages"]):
                # 最初のassistantメッセージ（AI分析コメント）はスキップ
                if i == 0 and msg["role"] == "assistant":
                    continue
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            # 追加質問の入力
            if analysis_prompt := st.chat_input("このデータについて追加で質問してください...", key="analysis_chat"):
                # ユーザーの質問を履歴に追加
                st.session_state["analysis_messages"].append({"role": "user", "content": analysis_prompt})
                with st.chat_message("user"):
                    st.markdown(analysis_prompt)
                
                # AIの応答を生成
                with st.chat_message("assistant"):
                    with st.spinner("回答を生成中..."):
                        follow_up_response = analyze_dataframe_with_followup(df, question, analysis_prompt)
                        st.markdown(follow_up_response)
                        st.session_state["analysis_messages"].append({"role": "assistant", "content": follow_up_response})
            
            # 分析チャット履歴をクリア
            if st.button("🗑️ 分析チャットをクリア", key="clear_analysis_chat"):
                st.session_state["analysis_messages"] = []
                st.rerun()
        
    #else:
    #    st.info("表形式で表示できるデータがありません")

def genie_mcp_page(genie_space_id: str):
    """Genie MCP問い合わせページ"""
    st.title("🔍 Genie アドバイザー")
    st.markdown("Databricks Genie を使用してデータを取得し、AIとチャットで分析します")
    workspace_hostname, username = get_workspace_info()
    if not workspace_hostname:
        return

    # 1. 環境変数
    access_token = os.getenv("DATABRICKS_ACCESS_TOKEN")
    
    # Base64デコードが必要な場合
    if access_token:
        try:
            import base64
            decoded_token = base64.b64decode(access_token).decode('utf-8')
            if decoded_token.startswith('dapi'):
                access_token = decoded_token
        except:
            pass  # デコードに失敗した場合は元の値を使用
    
    if not access_token:
        st.error("DATABRICKS_ACCESS_TOKEN が設定されていません。app.yaml の secret 設定を確認してください。")
        st.write("デバッグ情報:")
        st.write("- DATABRICKS_HOST:", os.getenv("DATABRICKS_HOST"))
        st.write("- SERVING_ENDPOINT:", os.getenv("SERVING_ENDPOINT"))
        st.write("- その他の環境変数:", [k for k in os.environ.keys() if k.startswith('DATABRICKS')])
        return
    #st.write("Genie用アクセストークン:", access_token)

    # 質問入力
    st.subheader("💬 データを取得：Genie に質問してデータを取得してください")
    question = st.text_area(
        "Genieへの質問",
        value="月別の支払い額の合計とステータスを教えて",
        height=100,
        placeholder="Genieスペースに対して質問を入力してください..."
    )

    # 質問送信ボタン
    if st.button("🚀 質問を送信", type="primary"):
        if question.strip():
            try:
                # 新しい質問を送信する際に分析結果とチャット履歴をリセット
                if "analysis_comment" in st.session_state:
                    del st.session_state["analysis_comment"]
                if "analysis_messages" in st.session_state:
                    del st.session_state["analysis_messages"]
                
                with GenieMCPClient(workspace_hostname, genie_space_id, access_token) as genie_client:
                    with st.spinner("Genieに質問中..."):
                        response = genie_client.query_genie(question)
                        #st.write("DEBUG: Genie response:", response)
                        result = GenieMCPResponseParser.parse_response(response)
                        #st.write("DEBUG: Parsed result:", result)
                        df = extract_dataframe_from_genie_response(result)
                        executed_query = extract_query_from_genie_response(result)
                        genie_comment = extract_comment_from_genie_response(result)
                        st.session_state["genie_df"] = df
                        st.session_state["genie_question"] = question
                        st.session_state["genie_executed_query"] = executed_query
                        st.session_state["genie_comment"] = genie_comment
            except Exception as e:
                st.error(f"Genieへの問い合わせでエラー: {e}")
        else:
            st.warning("⚠️ 質問を入力してください")

    # データと可視化のみ表示
    #st.subheader("📊 回答データと可視化")
    display_query_result()


def main():
    genie_mcp_page(genie_space_id)

if __name__ == "__main__":
    main()
