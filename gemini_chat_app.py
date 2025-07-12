import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pandas as pd
import io
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# --- matplotlibの日本語設定 --- 
plt.rcParams['font.family'] = 'Yu Gothic' # Windowsの場合
# もしYu Gothicがなければ、Meiryoなど別のフォントを試す
# plt.rcParams['font.family'] = 'Meiryo' 
plt.rcParams['axes.unicode_minus'] = False # マイナス記号を正しく表示
# --- 日本語設定ここまで --- 

# .envファイルから環境変数を読み込む
load_dotenv()

# Gemini APIキーを設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEYが設定されていません。.envファイルを確認してください。")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# Geminiモデルの初期化
model = genai.GenerativeModel('models/gemini-2.5-flash')

st.title("Gemini データ分析アシスタント")

# --- ここからトップ画面のデータ推奨ヒントを追加 --- 
with st.expander("データアップロードの推奨形式を見る"): 
    st.markdown("### データアップロードの推奨形式")
    st.info("""より正確な分析を行うために、以下の形式でのデータアップロードを推奨します。

- **ヘッダー（列名）は1行目**に含めてください。
- データは**縦持ち（ロングフォーマット）**で、各行が1つの観測値（例: 1つの取引、1つのイベント）を表すようにしてください。
- **カラム名**は、内容が分かりやすいように具体的に命名してください（例: `売上`, `顧客ID`, `日付`, `商品カテゴリ`）。
- **日付/時刻データ**は、`YYYY-MM-DD` や `YYYY/MM/DD HH:MM:SS` などの標準的な形式で統一してください。
- **数値データ**は、数値として認識できる形式で入力してください（通貨記号やカンマは含めない）。

**推奨データ例:**
```csv
日付,商品名,売上,数量,顧客ID
2023-01-01,りんご,150,2,C001
2023-01-01,みかん,100,3,C002
2023-01-02,りんご,300,4,C001
2023-01-02,バナナ,200,1,C003
```""")
# --- ヒント機能ここまで --- 

# タブの作成
chat_tab, settings_tab = st.tabs(["チャット", "設定"])

with settings_tab:
    st.header("設定")
    st.markdown("### 回答の対象ユーザーを選択してください")
    target_audience_options = [
        "一般ビジネスマン向け",
        "高校生向け",
        "データ分析初心者向け",
        "プロフェッショナル向け"
    ]
    selected_audience = st.radio(
        "",
        target_audience_options,
        index=target_audience_options.index(st.session_state.get("target_audience", "データ分析初心者向け")) if "target_audience" in st.session_state else 2
    )
    st.session_state.target_audience = selected_audience
    st.info(f"現在の設定: {st.session_state.target_audience}に合わせた回答をします。")

# Pythonコード実行関数
def execute_python_code(code, df):
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    plots = []
    plotly_figures = []
    
    try:
        local_vars = {'df': df, 'pd': pd, 'plt': plt, 'sns': sns, 'px': px, 'go': go}
        exec(code, globals(), local_vars)
        
        if plt.get_fignums():
            for fig_num in plt.get_fignums():
                fig = plt.figure(fig_num)
                plots.append(fig)
                plt.close(fig) 
        
        for var_name, var_value in local_vars.items():
            if isinstance(var_value, (go.Figure, go.FigureWidget)):
                plotly_figures.append(var_value)

        output = redirected_output.getvalue()
        return output, plots, plotly_figures, None
    except Exception as e:
        output = redirected_output.getvalue()
        return output, [], [], str(e)
    finally:
        sys.stdout = old_stdout
        plt.close('all')

with chat_tab:
    # ファイルアップロード機能
    uploaded_file = st.file_uploader("CSVまたはExcelファイルをアップロードしてください", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            st.success("ファイルの読み込みに成功しました！")
            st.write("読み込んだデータの最初の5行:")
            st.dataframe(df.head())
            
            # データフレームのメタ情報を取得
            buffer = io.StringIO()
            df.info(buf=buffer)
            df_info = buffer.getvalue()
            df_describe = df.describe(include='all').to_markdown()
            df_columns = df.columns.tolist()

            # メタ情報をセッションステートに保存
            st.session_state.df_info = df_info
            st.session_state.df_describe = df_describe
            st.session_state.df_columns = df_columns

            # --- ここから分析ヒントと目的の質問を追加 --- 
            st.markdown("### こんな分析ができますよ！")
            st.info("""- **データの全体像を把握する:** 各カラムの平均、最大値、最小値、欠損値などを確認できます。
- **データの分布を見る:** 特定のカラム（例: 売上、年齢）がどのような値の範囲に、どれくらいの頻度で存在するかをグラフで可視化できます。
- **関係性を探る:** 2つのカラム（例: 広告費と売上）の間にどのような関係があるか、散布図などで確認できます。
- **時系列トレンドを追う:** 日付データがあれば、時間の経過とともにデータがどのように変化しているかを見ることができます。
- **カテゴリごとの比較:** 商品カテゴリ別や地域別など、カテゴリごとの合計値や平均値を比較できます。

このデータを使って、どのような目的を達成したいですか？例えば、『売上を伸ばすための要因を見つけたい』『顧客の行動パターンを理解したい』など、具体的な目標を教えてください。""")
            # --- 分析ヒントと目的の質問ここまで --- 

            # Geminiにデータフレームの情報を渡す
            initial_prompt = f"""
あなたは{st.session_state.target_audience}です。その視点に立って、以下のデータファイルについて分析や可視化の提案をしてください。
特に、以下の点に注目して具体的な提案をお願いします。
- カラム名とデータ型から推測できる分析（例: 日付カラムがあれば時系列分析、数値カラムがあれば分布分析など）
- 複数のカラムを組み合わせた分析（例: カテゴリと数値の集計、2つの数値カラムの相関など）

分析や可視化のコードを生成する際は、必ずPythonコードブロック（```python ... ```）で囲んでください。
データフレームは`df`という変数に格納されています。
以下のライブラリは既にインポートされていますので、コード内で直接使用できます:
- `pandas` (as `pd`)
- `matplotlib.pyplot` (as `plt`)
- `seaborn` (as `sns`)
- `plotly.express` (as `px`) (インタラクティブなグラフを作成できます)
- `plotly.graph_objects` (as `go`) (インタラクティブなグラフを作成できます)

グラフを生成する場合は、`plt.show()`や`fig.show()`は使用せず、コードの最後に`plt.figure()`で作成したMatplotlibの図、または`px.`や`go.`で作成したPlotlyの図オブジェクトをそのまま残してください。Streamlitが自動的に表示します。
テキスト出力は`print()`を使用してください。

--- データ概要 ---
カラム名とデータ型:
{df_info}

統計情報:
{df_describe}

カラム一覧: {', '.join(df_columns)}

--- 質問 ---
このデータを使って、どのような目的を達成したいですか？例えば、『売上を伸ばすための要因を見つけたい』『顧客の行動パターンを理解したい』など、具体的な目標を教えてください。
"""
            st.session_state.messages.append({"role": "assistant", "content": initial_prompt})
            st.session_state.df = df # データフレームをセッションステートに保存

        except Exception as e:
            st.error(f"ファイルの読み込み中にエラーが発生しました: {e}")

    # チャット履歴の初期化
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 過去のメッセージを表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ユーザーからの入力 (これをタブの外に移動し、常に最下部に表示)
# Streamlitのチャット入力欄は、コードの最後に配置することで自動的に最下部に固定されます。
if prompt := st.chat_input("何でも聞いてください..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            # データフレームのメタ情報をセッションステートから取得
            df_info = st.session_state.get("df_info", "データがアップロードされていません。")
            df_describe = st.session_state.get("df_describe", "データがアップロードされていません。")
            df_columns = st.session_state.get("df_columns", [])

            # アップロードされたデータフレームがある場合、プロンプトに含める
            if "df" in st.session_state and st.session_state.df is not None:
                # データフレームのメタ情報をプロンプトに含める
                data_context = f"""
あなたは{st.session_state.target_audience}です。その視点に立って、ユーザーは以下のデータについて質問しています。
このデータを使って、どのような分析や可視化が可能か、具体的なカラム名を挙げて提案してください。
特に、日付カラムがあれば時系列分析の可能性、数値カラムとカテゴリカルカラムがあれば集計や比較分析の可能性について言及してください。

分析や可視化のコードを生成する際は、必ずPythonコードブロック（```python ... ```）で囲んでください。
データフレームは`df`という変数に格納されています。
以下のライブラリは既にインポートされていますので、コード内で直接使用できます:
- `pandas` (as `pd`)
- `matplotlib.pyplot` (as `plt`)
- `seaborn` (as `sns`)
- `plotly.express` (as `px`) (インタラクティブなグラフを作成できます)
- `plotly.graph_objects` (as `go`) (インタラクティブなグラフを作成できます)

グラフを生成する場合は、`plt.show()`や`fig.show()`は使用せず、コードの最後に`plt.figure()`で作成したMatplotlibの図、または`px.`や`go.`で作成したPlotlyの図オブジェクトをそのまま残してください。Streamlitが自動的に表示します。
テキスト出力は`print()`を使用してください。

--- データ概要 ---
カラム名とデータ型:
{df_info}

統計情報:
{df_describe}

カラム一覧: {', '.join(df_columns)}

--- ユーザーの質問 ---
{prompt}
"""
                response = model.generate_content(data_context, stream=True)
            else:
                response = model.generate_content(prompt, stream=True)

            for chunk in response:
                full_response += chunk.text
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

            # Pythonコードブロックを抽出して実行
            python_code_blocks = []
            current_code_block = []
            in_code_block = False

            for line in full_response.split('\n'):
                if line.strip() == '```python':
                    in_code_block = True
                    current_code_block = []
                    continue
                elif line.strip() == '```' and in_code_block:
                    in_code_block = False
                    python_code_blocks.append('\n'.join(current_code_block))
                    continue
                
                if in_code_block:
                    current_code_block.append(line)
            
            if python_code_blocks and "df" in st.session_state and st.session_state.df is not None: # dfが存在する場合のみ実行
                st.markdown("--- ")
                st.markdown("### 実行結果")
                for i, code_block in enumerate(python_code_blocks):
                    st.markdown(f"#### コードブロック {i+1}")
                    st.code(code_block, language='python')
                    
                    output, plots, plotly_figures, error = execute_python_code(code_block, st.session_state.df)
                    
                    if error:
                        st.error(f"コード実行中にエラーが発生しました: {error}")
                        if output:
                            st.code(output, language='text')
                    else:
                        if output:
                            st.code(output, language='text')
                        for plot in plots:
                            st.pyplot(plot)
                        for fig in plotly_figures: # Plotlyの図を表示
                            st.plotly_chart(fig)
                        if not output and not plots and not plotly_figures:
                            st.info("コードは正常に実行されましたが、出力やグラフはありませんでした。")
            elif python_code_blocks:
                st.warning("データがアップロードされていないため、コードは実行されませんでした。")

        except Exception as e:
            full_response = f"エラーが発生しました: {e}"
            message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})