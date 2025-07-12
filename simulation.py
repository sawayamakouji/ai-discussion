import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import random

def generate_pareto_sales_potential(num_items, total_potential_sales, pareto_alpha=1.16):
    """
    Generates sales potential for each item following a Pareto distribution.
    pareto_alpha: Shape parameter. Lower alpha means more skewed distribution (e.g., 80/20 rule).
    """
    # Generate random numbers from a uniform distribution and transform them
    # to approximate Pareto ranks. Then scale.
    
    # Generate random values and sort them in descending order
    raw_values = np.random.rand(num_items)
    sorted_values = np.sort(raw_values)[::-1] # Descending order
    
    # Apply a power law to create the Pareto effect
    # This is a heuristic, not a strict Pareto distribution generation
    # The idea is that higher ranked items get disproportionately more
    scaled_values = sorted_values**pareto_alpha
    
    # Normalize to sum to total_potential_sales
    item_potentials = scaled_values / np.sum(scaled_values) * total_potential_sales
    
    return item_potentials

def run_supermarket_simulation_pareto_analysis(
    max_items_to_consider=200, # Max items we can potentially stock
    total_market_potential_sales=1000, # Total sales if all items were perfectly stocked
    pareto_alpha=1.16, # For sales distribution (lower = more skewed)
    
    # Cost parameters
    fixed_cost=50, # Example fixed cost for store operation
    variable_cost_per_item_unit=0.5, # Cost per unit of sales (e.g., COGS)
    item_holding_cost_per_item=1, # Cost to hold/manage one item (per month)
    
    # Overchoice and Competitor (simplified integration for now)
    overchoice_sensitivity=0.005, # Sensitivity to overchoice (higher = more loss)
    competitor_optimal_items=90, # Competitor's optimal item count
    competitor_influence_factor=0.001 # How much competitor affects sales based on item count difference
):
    results_df = pd.DataFrame(columns=["NumberOfItems", "TotalSales", "TotalProfit", "CumulativeSalesRatio", "CumulativeItemRatio"])
    
    # Generate potential sales for a large pool of items following Pareto
    # We assume we are adding items from this pool, starting with the highest potential
    all_item_potentials = generate_pareto_sales_potential(max_items_to_consider, total_market_potential_sales, pareto_alpha)
    
    # Sort items by their potential sales in descending order
    sorted_item_potentials = np.sort(all_item_potentials)[::-1]

    for num_items_stocked in range(1, max_items_to_consider + 1):
        # Select items to stock (highest potential first)
        current_stocked_items_potential = sorted_item_potentials[:num_items_stocked]
        
        # Calculate base sales from stocked items
        base_sales = np.sum(current_stocked_items_potential)
        
        # Apply overchoice effect
        # This effect should reduce sales based on how far we are from an "ideal" number of items
        # Let's assume an ideal number of items for customer experience (e.g., 100)
        ideal_customer_items = 100
        overchoice_penalty = overchoice_sensitivity * abs(num_items_stocked - ideal_customer_items)
        sales_after_overchoice = base_sales * (1 - overchoice_penalty)
        sales_after_overchoice = max(0, sales_after_overchoice) # Ensure non-negative
        
        # Apply competitor influence
        competitor_penalty = competitor_influence_factor * abs(num_items_stocked - competitor_optimal_items)
        actual_sales = sales_after_overchoice * (1 - competitor_penalty)
        actual_sales = max(0, actual_sales) # Ensure non-negative

        # Calculate costs
        total_variable_cost = actual_sales * variable_cost_per_item_unit
        total_item_holding_cost = num_items_stocked * item_holding_cost_per_item
        total_costs = fixed_cost + total_variable_cost + total_item_holding_cost
        
        # Calculate profit
        profit = actual_sales - total_costs
        
        # Store results
        results_df.loc[num_items_stocked] = [num_items_stocked, actual_sales, profit, 0, 0] # Cumulative ratios will be calculated later

    # Calculate cumulative sales and item ratios for Pareto curve
    results_df["CumulativeSales"] = results_df["TotalSales"].cumsum()
    results_df["CumulativeSalesRatio"] = results_df["TotalSales"].cumsum() / results_df["TotalSales"].sum()
    results_df["CumulativeItemRatio"] = results_df["NumberOfItems"] / max_items_to_consider
    
    return results_df

if __name__ == "__main__":
    simulation_results = run_supermarket_simulation_pareto_analysis()
    
    # Plot Total Sales and Profit
    plt.figure(figsize=(14, 7))
    sns.lineplot(x="NumberOfItems", y="TotalSales", data=simulation_results, label="Total Sales")
    sns.lineplot(x="NumberOfItems", y="TotalProfit", data=simulation_results, label="Total Profit")
    plt.title("Supermarket Item Count vs. Sales & Profit (Pareto & Costs)")
    plt.xlabel("Number of Items Stocked")
    plt.ylabel("Value (Arbitrary Units)")
    plt.grid(True)
    plt.legend()
    plt.savefig("supermarket_pareto_sales_profit.png")
    
    # Plot Pareto Curve
    plt.figure(figsize=(10, 6))
    sns.lineplot(x="CumulativeItemRatio", y="CumulativeSalesRatio", data=simulation_results)
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Ideal (1:1)') # Ideal 1:1 line
    plt.title("Pareto Curve: Cumulative Sales vs. Cumulative Items")
    plt.xlabel("Cumulative Proportion of Items (Sorted by Sales)")
    plt.ylabel("Cumulative Proportion of Sales")
    plt.grid(True)
    plt.legend()
    plt.savefig("supermarket_pareto_curve.png")
    
    print("Simulation complete. Results saved to supermarket_pareto_sales_profit.png and supermarket_pareto_curve.png")
    print(simulation_results.tail())