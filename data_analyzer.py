import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_sales_data(file_path):
    df = pd.read_csv(file_path)

    # Calculate total sales and profit for each product group
    group_summary = df.groupby('ProductGroup').agg(TotalSales=('Sales', 'sum'), TotalProfit=('Profit', 'sum')).reset_index()

    # Sort by TotalSales for Pareto analysis
    group_summary_sorted_sales = group_summary.sort_values(by='TotalSales', ascending=False).reset_index(drop=True)
    group_summary_sorted_sales['CumulativeSales'] = group_summary_sorted_sales['TotalSales'].cumsum()
    group_summary_sorted_sales['CumulativeSalesRatio'] = group_summary_sorted_sales['CumulativeSales'] / group_summary_sorted_sales['TotalSales'].sum()
    group_summary_sorted_sales['CumulativeProductGroupRatio'] = (group_summary_sorted_sales.index + 1) / len(group_summary_sorted_sales)

    # Sort by TotalProfit for Pareto analysis
    group_summary_sorted_profit = group_summary.sort_values(by='TotalProfit', ascending=False).reset_index(drop=True)
    group_summary_sorted_profit['CumulativeProfit'] = group_summary_sorted_profit['TotalProfit'].cumsum()
    group_summary_sorted_profit['CumulativeProfitRatio'] = group_summary_sorted_profit['TotalProfit'] / group_summary_sorted_profit['TotalProfit'].sum()
    group_summary_sorted_profit['CumulativeProductGroupRatio'] = (group_summary_sorted_profit.index + 1) / len(group_summary_sorted_profit)

    # --- Visualization --- 
    plt.figure(figsize=(14, 6))

    # Pareto Chart for Sales
    plt.subplot(1, 2, 1)
    sns.barplot(x='ProductGroup', y='TotalSales', data=group_summary_sorted_sales)
    plt.plot(group_summary_sorted_sales['CumulativeSalesRatio'], color='red', marker='o', linestyle='--')
    plt.axhline(0.8, color='gray', linestyle=':', label='80% Sales')
    plt.ylim(0, 1.1) # Adjust Y-axis limit for ratio
    plt.title('Sales Pareto Analysis by Product Group')
    plt.xlabel('Product Group (Sorted by Sales)')
    plt.ylabel('Total Sales')
    plt.tick_params(axis='x', rotation=45)
    plt.grid(axis='y', linestyle='--')
    plt.legend()

    # Pareto Chart for Profit
    plt.subplot(1, 2, 2)
    sns.barplot(x='ProductGroup', y='TotalProfit', data=group_summary_sorted_profit)
    plt.plot(group_summary_sorted_profit['CumulativeProfitRatio'], color='red', marker='o', linestyle='--')
    plt.axhline(0.8, color='gray', linestyle=':', label='80% Profit')
    plt.ylim(0, 1.1) # Adjust Y-axis limit for ratio
    plt.title('Profit Pareto Analysis by Product Group')
    plt.xlabel('Product Group (Sorted by Profit)')
    plt.ylabel('Total Profit')
    plt.tick_params(axis='x', rotation=45)
    plt.grid(axis='y', linestyle='--')
    plt.legend()

    plt.tight_layout()
    plt.savefig('pareto_analysis_results.png')
    print("Pareto analysis complete. Results saved to pareto_analysis_results.png")
    
    print("\n--- Sales Pareto Analysis ---")
    print(group_summary_sorted_sales[['ProductGroup', 'TotalSales', 'CumulativeSalesRatio', 'CumulativeProductGroupRatio']].head())
    print("\n--- Profit Pareto Analysis ---")
    print(group_summary_sorted_profit[['ProductGroup', 'TotalProfit', 'CumulativeProfitRatio', 'CumulativeProductGroupRatio']].head())

if __name__ == "__main__":
    analyze_sales_data('sample_sales_data.csv')
