import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import date

# Matplotlib日本語表示対応
plt.rcParams['font.family'] = 'Meiryo' # Windows環境で一般的な日本語フォント
plt.rcParams['axes.unicode_minus'] = False # マイナス記号の文字化け防止

# Ensure the generated_content directory exists
if not os.path.exists('generated_content'):
    os.makedirs('generated_content')

# Analysis function for Pareto (adapted from data_analyzer.py)
def analyze_and_display_pareto(df, sales_col, profit_col, category_col, filter_col=None, filter_values=None):
    if not sales_col or not category_col:
        st.error("パレート分析には「売上」と「カテゴリ」の列選択が必要です。利益列は任意です。")
        return

    # Apply filter if selected
    if filter_col and filter_col != "選択しない" and filter_values:
        df = df[df[filter_col].isin(filter_values)].copy() # Use .copy() to avoid SettingWithCopyWarning
        if df.empty:
            st.warning(f"選択されたフィルタ条件 ({filter_col}: {filter_values}) に合致するデータがありません。")
            return

    # Determine if profit analysis will be performed
    perform_profit_analysis = (profit_col != "選択しない" and profit_col is not None)

    # Ensure numeric types
    df[sales_col] = pd.to_numeric(df[sales_col], errors='coerce').fillna(0)
    if perform_profit_analysis:
        df[profit_col] = pd.to_numeric(df[profit_col], errors='coerce').fillna(0)

    # Calculate total sales and profit for each product group
    # Aggregate both sales and profit in one go if profit analysis is to be performed
    if perform_profit_analysis:
        group_summary = df.groupby(category_col).agg(
            TotalSales=(sales_col, 'sum'),
            TotalProfit=(profit_col, 'sum')
        ).reset_index()
        group_summary['ProfitMargin'] = (group_summary['TotalProfit'] / group_summary['TotalSales']).fillna(0)
    else:
        group_summary = df.groupby(category_col).agg(
            TotalSales=(sales_col, 'sum')
        ).reset_index()

    # Sort by TotalSales for Pareto analysis
    group_summary_sorted_sales = group_summary.sort_values(by='TotalSales', ascending=False).reset_index(drop=True)
    group_summary_sorted_sales['CumulativeSales'] = group_summary_sorted_sales['TotalSales'].cumsum()
    group_summary_sorted_sales['CumulativeSalesRatio'] = group_summary_sorted_sales['CumulativeSales'] / group_summary_sorted_sales['TotalSales'].sum()
    group_summary_sorted_sales['CumulativeProductGroupRatio'] = (group_summary_sorted_sales.index + 1) / len(group_summary_sorted_sales)

    if perform_profit_analysis:
        # Sort by TotalProfit for Pareto analysis
        group_summary_sorted_profit = group_summary.sort_values(by='TotalProfit', ascending=False).reset_index(drop=True)
        group_summary_sorted_profit['CumulativeProfit'] = group_summary_sorted_profit['TotalProfit'].cumsum()
        group_summary_sorted_profit['CumulativeProfitRatio'] = group_summary_sorted_profit['CumulativeProfit'] / group_summary_sorted_profit['TotalProfit'].sum()
        group_summary_sorted_profit['CumulativeProductGroupRatio'] = (group_summary_sorted_profit.index + 1) / len(group_summary_sorted_profit)

    # --- Visualization --- 
    st.write("### パレート分析結果")

    # Pareto Chart for Sales (Plotly)
    fig_sales = go.Figure()

    # Bar chart for Total Sales
    fig_sales.add_trace(go.Bar(
        x=group_summary_sorted_sales[category_col],
        y=group_summary_sorted_sales['TotalSales'],
        name='合計売上',
        marker_color='skyblue'
    ))

    # Line chart for Cumulative Sales Ratio (secondary y-axis)
    fig_sales.add_trace(go.Scatter(
        x=group_summary_sorted_sales[category_col],
        y=group_summary_sorted_sales['CumulativeSalesRatio'],
        mode='lines+markers',
        name='累積売上比率',
        yaxis='y2',
        marker_color='red'
    ))

    # 80% line
    fig_sales.add_hline(y=0.8, line_dash="dot", line_color="gray", annotation_text="80% Sales", annotation_position="top right", yref="y2")

    fig_sales.update_layout(
        title_text='売上パレート分析 (品群別)',
        xaxis_title=f'{category_col} (売上順)',
        yaxis_title='合計売上',
        yaxis2=dict(
            title='累積売上比率',
            overlaying='y',
            side='right',
            range=[0, 1.1]
        ),
        font=dict(family="Meiryo"), # 日本語フォント設定
        hovermode="x unified",
        height=600
    )
    
    # Display plot in Streamlit
    st.plotly_chart(fig_sales, use_container_width=True)

    # Save plot to generated_content folder as HTML
    plot_path_sales_html = os.path.join('generated_content', 'pareto_sales_analysis.html')
    fig_sales.write_html(plot_path_sales_html)

    # Pareto Chart for Profit (Conditional - Plotly)
    if perform_profit_analysis:
        fig_profit = go.Figure()

        # Bar chart for Total Profit
        fig_profit.add_trace(go.Bar(
            x=group_summary_sorted_profit[category_col],
            y=group_summary_sorted_profit['TotalProfit'],
            name='合計利益',
            marker_color='lightgreen'
        ))

        # Line chart for Cumulative Profit Ratio (secondary y-axis)
        fig_profit.add_trace(go.Scatter(
            x=group_summary_sorted_profit[category_col],
            y=group_summary_sorted_profit['CumulativeProfitRatio'],
            mode='lines+markers',
            name='累積利益比率',
            yaxis='y2',
            marker_color='darkred'
        ))

        # 80% line
        fig_profit.add_hline(y=0.8, line_dash="dot", line_color="gray", annotation_text="80% Profit", annotation_position="top right", yref="y2")

        fig_profit.update_layout(
            title_text='利益パレート分析 (品群別)',
            xaxis_title=f'{category_col} (利益順)',
            yaxis_title='合計利益',
            yaxis2=dict(
                title='累積利益比率',
                overlaying='y',
                side='right',
                range=[0, 1.1]
            ),
            font=dict(family="Meiryo"), # 日本語フォント設定
            hovermode="x unified",
            height=600
        )
        
        # Display plot in Streamlit
        st.plotly_chart(fig_profit, use_container_width=True)

        # Save plot to generated_content folder as HTML
        plot_path_profit_html = os.path.join('generated_content', 'pareto_profit_analysis.html')
        fig_profit.write_html(plot_path_profit_html)

    st.write("### 分析サマリー")
    # Use category_col instead of hardcoded 'ProductGroup'
    st.write("**売上パレート分析上位:**")
    st.dataframe(group_summary_sorted_sales[[category_col, 'TotalSales', 'CumulativeSalesRatio', 'CumulativeProductGroupRatio']].head())
    if perform_profit_analysis:
        st.write("**利益パレート分析上位:**")
        st.dataframe(group_summary_sorted_profit[[category_col, 'TotalProfit', 'CumulativeProfitRatio', 'CumulativeProductGroupRatio', 'ProfitMargin']].head())
        
        # Debugging output for cumulative profit ratio
        st.write("**DEBUG: 累積利益比率データ (上位5行)**")
        st.dataframe(group_summary_sorted_profit[[category_col, 'TotalProfit', 'CumulativeProfit', 'CumulativeProfitRatio']].head())

        # --- Strategic Focus Candidates Identification ---
        st.write("### 戦略的重点候補の提案")
        st.write("売上上位かつ利益率が低い品群を**戦略的重点候補**として提案します。これらの品群は、集客効果が高い可能性があり、今後の詳細な分析や戦略立案の対象となりえます。")

        # Define Strategic Focus Candidates: Top 30% by sales, and profit margin below overall average
        top_sales_threshold = 0.3 # Top 30% by sales
        overall_avg_profit_margin = group_summary['ProfitMargin'].mean()

        strategic_focus_candidates = group_summary_sorted_sales[
            (group_summary_sorted_sales['CumulativeProductGroupRatio'] <= top_sales_threshold) & 
            (group_summary_sorted_sales['ProfitMargin'] < overall_avg_profit_margin)
        ]

        if not strategic_focus_candidates.empty:
            st.dataframe(strategic_focus_candidates[[category_col, 'TotalSales', 'TotalProfit', 'ProfitMargin']].sort_values(by='ProfitMargin', ascending=True))
            st.info(f"全体平均利益率: {overall_avg_profit_margin:.2%}")
        else:
            st.write("戦略的重点候補は見つかりませんでした。")

# Analysis function for Time Series
def analyze_and_display_timeseries(df, date_col, value_col, aggregation_level, start_date=None, end_date=None):
    if not date_col or not value_col:
        st.error("時系列分析には「日付」と、可視化したい数値の列選択が必要です。")
        return

    # Ensure date column is datetime type
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df.dropna(subset=[date_col], inplace=True) # Drop rows where date conversion failed
    df = df.sort_values(by=date_col) # Sort by date

    # Apply date filter if selected
    if start_date and end_date:
        df = df[(df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))].copy()
        if df.empty:
            st.warning(f"選択された日付範囲 ({start_date} から {end_date}) に合致するデータがありません。")
            return

    # Ensure value column is numeric
    df[value_col] = pd.to_numeric(df[value_col], errors='coerce').fillna(0)

    # Aggregate data based on selected level
    if aggregation_level == "週次":
        df['Period'] = df[date_col].dt.to_period('W').dt.start_time
    elif aggregation_level == "月次":
        df['Period'] = df[date_col].dt.to_period('M').dt.start_time
    else: # 日次
        df['Period'] = df[date_col]
    
    # Group by the new Period column and sum the value_col
    aggregated_df = df.groupby('Period')[value_col].sum().reset_index()
    aggregated_df = aggregated_df.sort_values(by='Period')

    st.write("### 時系列分析結果")
    fig = px.line(aggregated_df, x='Period', y=value_col,
                  title=f'{value_col}の時系列推移 ({aggregation_level}集計)',
                  labels={'Period': '期間', value_col: value_col})
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)
    fig.update_layout(font=dict(family="Meiryo")) # 日本語フォント設定

    # Display plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # Then save plot to generated_content folder as HTML
    plot_path = os.path.join('generated_content', f'timeseries_{value_col}_{aggregation_level}.html')
    fig.write_html(plot_path)

    st.write("### 時系列データサマリー")
    st.dataframe(aggregated_df.describe())

# Analysis function for Composition Analysis
def analyze_and_display_composition(df, category_col, value_col):
    if not category_col or not value_col:
        st.error("構成比分析には「カテゴリ」と「値」の列選択が必要です。")
        return

    # Ensure value column is numeric
    df[value_col] = pd.to_numeric(df[value_col], errors='coerce').fillna(0)

    # Aggregate data by category
    category_summary = df.groupby(category_col)[value_col].sum().reset_index()
    category_summary = category_summary.sort_values(by=value_col, ascending=False)

    st.write("### 構成比分析結果")
    fig = px.pie(category_summary, values=value_col, names=category_col,
                 title=f'{value_col}の構成比 ({category_col}別)')
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(font=dict(family="Meiryo")) # 日本語フォント設定

    # Display plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # Then save plot to generated_content folder as HTML
    plot_path = os.path.join('generated_content', f'composition_{value_col}_{category_col}.html')
    fig.write_html(plot_path)

    st.write("### 構成比データサマリー")
    st.dataframe(category_summary)

def main():
    st.set_page_config(layout="wide")
    st.title("データ分析ツール：ファイルアップロードと列マッピング")

    uploaded_file = st.file_uploader("CSVまたはExcelファイルをアップロードしてください", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.write("### アップロードされたデータのプレビュー")
            st.dataframe(df.head())

            st.write("### 分析タイプを選択してください")
            analysis_type = st.radio(
                "どの分析を実行しますか？",
                ("パレート分析", "時系列分析", "構成比分析"), 
                key="analysis_type_selection"
            )

            st.write("### 分析に必要な列を選択してください")
            
            all_columns = ["選択しない"] + df.columns.tolist()

            if analysis_type == "パレート分析":
                st.write("#### パレート分析に必要な列")
                category_col = st.selectbox("カテゴリ列 (品群など)", all_columns, key="pareto_category_col")
                sales_col = st.selectbox("売上列", all_columns, key="pareto_sales_col")
                profit_col = st.selectbox("利益列 (任意)", all_columns, key="pareto_profit_col") 

                # Hint button for Pareto Analysis
                with st.expander("パレート分析のヒント"): 
                    st.write("**カテゴリ列の推奨:**")
                    st.write("ユニークな値が多く、品群や商品名など、データを分類するのに適した列を選びましょう。例: `ProductGroup`, `カテゴリ`, `商品名`")
                    st.write("**売上列の推奨:**")
                    st.write("数値データで、売上高を示す列を選びましょう。例: `Sales`, `売上`, `金額`")
                    st.write("**利益列の推奨:**")
                    st.write("数値データで、利益額を示す列を選びましょう。任意ですが、選択するとより詳細な分析が可能です。例: `Profit`, `利益`, `粗利`")

                st.write("#### フィルタリング (任意)")
                filter_col = st.selectbox("フィルタリングする列", all_columns, key="pareto_filter_col")
                filter_values = []
                if filter_col != "選択しない":
                    unique_values = df[filter_col].unique().tolist()
                    filter_values = st.multiselect(f"{filter_col} でフィルタリングする値", unique_values, key="pareto_filter_values")

                if st.button("分析を開始"): 
                    st.info("分析を実行中です。しばらくお待ちください...")
                    analyze_and_display_pareto(df, sales_col, profit_col, category_col, filter_col, filter_values)
                    st.success("分析が完了しました！")

            elif analysis_type == "時系列分析":
                st.write("#### 時系列分析に必要な列")
                date_col = st.selectbox("日付列", all_columns, key="timeseries_date_col")
                value_col = st.selectbox("値列 (売上、利益、数量など)", all_columns, key="timeseries_value_col")

                # Hint button for Time Series Analysis
                with st.expander("時系列分析のヒント"): 
                    st.write("**日付列の推奨:**")
                    st.write("日付や時刻の情報が含まれる列を選びましょう。例: `Date`, `日付`, `年月日`")
                    st.write("**値列の推奨:**")
                    st.write("数値データで、時系列で推移を見たい列を選びましょう。例: `Sales`, `売上`, `Profit`, `利益`, `Quantity`, `数量`")

                st.write("#### 集計粒度")
                aggregation_level = st.radio(
                    "データをどの粒度で集計しますか？",
                    ("日次", "週次", "月次"),
                    key="aggregation_level_selection"
                )

                st.write("#### 日付フィルタリング (任意)")
                if date_col != "選択しない":
                    try:
                        min_date = pd.to_datetime(df[date_col]).min().date()
                        max_date = pd.to_datetime(df[date_col]).max().date()
                    except:
                        min_date = date(2000, 1, 1) 
                        max_date = date(2030, 12, 31)

                    start_date = st.date_input("開始日", min_date, min_value=min_date, max_value=max_date, key="timeseries_start_date")
                    end_date = st.date_input("終了日", max_date, min_value=min_date, max_value=max_date, key="timeseries_end_date")
                else:
                    start_date = None
                    end_date = None

                if st.button("分析を開始"): 
                    st.info("分析を実行中です。しばらくお待ちください...")
                    analyze_and_display_timeseries(df, date_col, value_col, aggregation_level, start_date, end_date)
                    st.success("分析が完了しました！")
            
            elif analysis_type == "構成比分析": 
                st.write("#### 構成比分析に必要な列")
                category_col_comp = st.selectbox("カテゴリ列 (品群、商品名、メーカーなど)", all_columns, key="comp_category_col")
                value_col_comp = st.selectbox("値列 (売上、利益、数量など)", all_columns, key="comp_value_col")

                # Hint button for Composition Analysis
                with st.expander("構成比分析のヒント"): 
                    st.write("**カテゴリ列の推奨:**")
                    st.write("構成比を見たい分類の列を選びましょう。ユニークな値が多すぎるとグラフが見づらくなることがあります。例: `ProductGroup`, `カテゴリ`, `メーカー`")
                    st.write("**値列の推奨:**")
                    st.write("数値データで、構成比を計算したい列を選びましょう。例: `Sales`, `売上`, `Profit`, `利益`, `Quantity`, `数量`")

                if st.button("分析を開始"): 
                    st.info("分析を実行中です。しばらくお待ちください...")
                    analyze_and_display_composition(df, category_col_comp, value_col_comp)
                    st.success("分析が完了しました！")

        except Exception as e:
            st.error(f"ファイルの読み込みまたは分析中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()