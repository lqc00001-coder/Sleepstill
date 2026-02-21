# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 22:54:31 2025

@author: Li Qiang
"""

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
import pandas as pd

# Load the uploaded Excel file
file_path = r'E:\BaiduSyncdisk\墨尔本博后\老挝项目\Manuscript\图3-模拟产量精度分析\WS-0513.xlsx'
excel_data = pd.ExcelFile(file_path)

# Check the sheet names to confirm the structure
excel_data.sheet_names
# Load the 'Wet season' sheet
wet_season_data = excel_data.parse('Sheet1')

# Display the first few rows to check the structure and confirm column names
wet_season_data.head()

# Extract X and Y data from the columns
x = wet_season_data['statistical_yield(kg/ha)'].values
y = wet_season_data['modelling yield kg/ha'].values

# Linear regression model
model = LinearRegression()
model.fit(x.reshape(-1, 1), y)
y_pred = model.predict(x.reshape(-1, 1))

# Plot
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 14

sns.set(style="whitegrid")
fig = plt.figure(figsize=(8, 8))
gs = fig.add_gridspec(4, 4)
ax_main = fig.add_subplot(gs[1:4, 0:3])
ax_xhist = fig.add_subplot(gs[0, 0:3], sharex=ax_main)
ax_yhist = fig.add_subplot(gs[1:4, 3], sharey=ax_main)

# Scatter plot and fit line
# =============================================================================
# ax_main.scatter(x, y, c='green', label=f"$R^2$={model.score(x.reshape(-1, 1), y):.3f}\n$y={model.coef_[0]:.3f}x+{model.intercept_:.3f}$")
# ax_main.plot(x, y_pred, color='black', label="Fit line")
# ax_main.plot([min(x), max(x)], [min(x), max(x)], color='red', linestyle='--', label="1:1 line")
# ax_main.legend()
# ax_main.set_xlabel("Statistical yield-Dry season (kg/ha)")
# ax_main.set_ylabel("Modelling yield-Dry season (kg/ha)")
# =============================================================================

ax_main.scatter(x, y, c='#e69800', label=f"$R^2$={model.score(x.reshape(-1, 1), y):.2f}\n$y={model.coef_[0]:.2f}x{model.intercept_:.2f}$\nMAE=169.42 kg/ha\nRMSE=226.26 kg/ha")
ax_main.plot(x, y_pred, color='black', label="Fit line")
ax_main.plot([0, 6000], [0, 6000], color='red', linestyle='--', label="1:1 line")
ax_main.legend(fontsize=14)
ax_main.set_xlim(0, 6000)  # Set x-axis limits
ax_main.set_ylim(0, 6000)  # Set y-axis limits
ax_main.set_xlabel("Statistical yield - Wet season (kg/ha)", fontsize=14)
ax_main.set_ylabel("Modelling yield - Wet season (kg/ha)", fontsize=14)
ax_main.tick_params(axis='both', which='major', labelsize=14)



# Marginal histograms
ax_xhist.hist(x, bins=20, color='#3aa702', alpha=1, density=True)
sns.kdeplot(x, ax=ax_xhist, color='red', linestyle='--')
ax_xhist.axis('off')
#ax_xhist.set_ylabel("Density")

ax_yhist.hist(y, bins=20, orientation='horizontal', color='#3aa702', alpha=1, density=True)
sns.kdeplot(y, ax=ax_yhist, color='red', linestyle='--', vertical=True)
ax_yhist.axis('off')
#ax_yhist.set_xlabel("Density")

plt.tight_layout()
plt.show()