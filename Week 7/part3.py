import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

combined = pd.read_csv("Data/combined_cumulative_returns_2018_2021.csv", parse_dates=["Date"], index_col="Date", dayfirst=True)

#top 3 stocks with the highest cumulative return in 2021
final_day_returns = combined.iloc[-1]
top_three_series = final_day_returns.sort_values(ascending=False).head(3)
top_three_tickers = top_three_series.index.tolist()

for rank, (ticker, return_value) in enumerate(top_three_series.items(), 1):
    print(f"Rank {rank}: {ticker}: {return_value:.4f} of {return_value * 100:.2f}%")

#Question 2
top_three_df = combined[top_three_tickers]

plt.figure(figsize=(12, 6))
for ticker in top_three_tickers:
    plt.plot(top_three_df.index, top_three_df[ticker], label=ticker, linewidth=2)

plt.title("Daily Cumulative Returns of Top 3 Stocks (2018-2021)", fontsize=14, fontweight='bold')
plt.xlabel("Timeline (Daily)", fontsize=12)
plt.ylabel("Cumulative Return (Decimal Value)", fontsize=12)
plt.legend(title="Tickers")
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.show()

#Question 3
total_top_three_gain = top_three_series.sum()
contribution_percentages = (top_three_series / total_top_three_gain) * 100

plt.figure(figsize=(7, 7))
plt.pie(
    contribution_percentages, 
    labels=contribution_percentages.index, 
    autopct='%1.2f%%', 
    startangle=180, 
    colors=['#4CAF50', '#2196F3', '#9C27B0'],
    textprops={'fontsize': 12, 'weight': 'bold'}
)
plt.title("Percentage Contribution of Each Stock to Total Group Gain", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()

#Question 5
yearly_averages = top_three_df.groupby(top_three_df.index.year).mean()

# Plotting a Grouped Bar Chart
ax = yearly_averages.plot(kind="bar", figsize=(12, 6), width=0.8, edgecolor='black')
plt.title("Yearly Average Cumulative Returns of Top 3 Stocks", fontsize=14, fontweight='bold')
plt.xlabel("Year", fontsize=12)
plt.ylabel("Average Cumulative Return", fontsize=12)
plt.xticks(rotation=0)
plt.grid(axis="y", linestyle="--", alpha=0.6)
plt.legend(title="Tickers")
plt.tight_layout()
plt.show()

print("\n--- Part 3, Question 7: Generating Custom Exploratory Plots ---")

# Goal Plot 1: Box Plot to analyze Volatility Distribution of the top winners
plt.figure(figsize=(10, 6))
sns.boxplot(data=top_three_df, palette="Set2")
plt.title("Plot 1 (Boxplot): Volatility Spread & Distribution Analysis", fontsize=14, fontweight='bold')
plt.ylabel("Return Variations")
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

plt.figure(figsize=(10, 8))
sns.heatmap(combined.corr(), annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
plt.title("Plot 2 (Heatmap): Structural Correlation Across All 10 Tickers", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 6))
for ticker in top_three_tickers:
    sns.kdeplot(top_three_df[ticker], label=ticker, fill=True, alpha=0.15)
    
sns.kdeplot(combined.mean(axis=1), label="Portfolio Average (All 10 Stocks)", color="black", linestyle="--", linewidth=2.5)
plt.title("Plot 3 (KDE): Distribution Density of Top 3 vs Portfolio Average", fontsize=14, fontweight='bold')
plt.xlabel("Return Ranges")
plt.ylabel("Density")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()