#%%
import pandas as pd
import numpy as np
import statsmodels.api as sm
import rasterio as rio
import matplotlib.pyplot as plt


#%%
# Import images

lst_file = "lst_trend_4seasons_quarters.tif"
tcc_file = "tcc_trend_4seasons_quarters.tif"
lst_agg = "lst_trend_4seasons.tif"
tcc_agg = "tcc_trend_4seasons.tif"
path = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Output_Trends/quarterly/"

# Quarterly LST
with rio.open(path+lst_file) as src:
    lst_mam_1d = src.read(1).ravel()
    lst_jja_1d = src.read(2).ravel()
    lst_son_1d = src.read(3).ravel()
    lst_djf_1d = src.read(4).ravel()

# Quarterly TCC
with rio.open(path+tcc_file) as src:
    tcc_mam_1d = src.read(1).ravel()
    tcc_jja_1d = src.read(2).ravel()
    tcc_son_1d = src.read(3).ravel()
    tcc_djf_1d = src.read(4).ravel()

# Aggregated LST & TCC
with rio.open(path+lst_agg) as src:
    lst_1d = src.read(1).ravel()
with rio.open(path+tcc_agg) as src:
    tcc_1d = src.read(1).ravel()


#%% 

# Create masks to filter out NaN values for each season
mam_mask = ~np.isnan(lst_mam_1d) & ~np.isnan(tcc_mam_1d)
jja_mask = ~np.isnan(lst_jja_1d) & ~np.isnan(tcc_jja_1d)
son_mask = ~np.isnan(lst_son_1d) & ~np.isnan(tcc_son_1d)
djf_mask = ~np.isnan(lst_djf_1d) & ~np.isnan(tcc_djf_1d)

agg_mask = ~np.isnan(lst_1d) & ~np.isnan(tcc_1d)

lst_mam = lst_mam_1d[mam_mask]
tcc_mam = tcc_mam_1d[mam_mask]
lst_jja = lst_jja_1d[jja_mask]
tcc_jja = tcc_jja_1d[jja_mask]
lst_son = lst_son_1d[son_mask]
tcc_son = tcc_son_1d[son_mask]
lst_djf = lst_djf_1d[djf_mask]
tcc_djf = tcc_djf_1d[djf_mask]
lst_agg = lst_1d[agg_mask]
tcc_agg = tcc_1d[agg_mask]

seasons = {
    "MAM" : (lst_mam, tcc_mam),
    "JJA" : (lst_jja, tcc_jja),
    "SON" : (lst_son, tcc_son),
    "DJF" : (lst_djf, tcc_djf),
    "Overall" : (lst_agg, tcc_agg)
}

#%%

# OLS

def run_regression_statsmodels(lst, tcc):
    lst = sm.add_constant(lst)  # Adds a constant term to the predictor
    model = sm.OLS(tcc, lst).fit()
    predictions = model.predict(lst)

    print(model.summary())
    return model

for season, (lst, tcc) in seasons.items():
    print(f"Season: {season}")
    model = run_regression_statsmodels(lst, tcc)
    print("\n")

# Export results as a CSV file
results = []
for season, (lst, tcc) in seasons.items():
    X = sm.add_constant(lst)
    model = sm.OLS(tcc, X).fit()
    results.append({
        "Season": season,
        "Slope": model.params[1],
        "Intercept": model.params[0],
        "R-squared": model.rsquared,
        "P-value": model.pvalues[1],
        "N": model.nobs,
    })


results_df = pd.DataFrame(results)
results_df.to_csv("TSA_OLS_results_LST_TCC.csv", index=False)

#%%

xlim = (-0.8, 1)
ylim = (-0.8, 1)

fig, axs = plt.subplots(2, 3, figsize=(15, 10))
for ax, (season, (lst, tcc)) in zip(axs.flatten(), seasons.items()):
    X = sm.add_constant(lst)
    model = sm.OLS(tcc, X).fit()
    fitted = model.predict(X)

    ax.scatter(lst, tcc, alpha=0.5, color="tab:blue")
    ax.plot(lst, fitted, color="tab:red", linewidth=2)
    ax.set_xlabel("LST Trend (Tau-b)")
    ax.set_ylabel("TCC Trend (Tau-b)")
    ax.set_title(f"{season}", loc='left')
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    stats_text = (
        f"Slope: {model.params[1]:.4f}\n"
        f"Intercept: {model.params[0]:.4f}\n"
        f"R$^2$: {model.rsquared:.4f}\n"
        f"P-value: {model.pvalues[1]:.3e}\n"
        f"N: {model.nobs}"
    )
    ax.text(
        0.05,
        0.77,
        stats_text,
        transform=ax.transAxes,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", alpha=0.9),
        fontsize=9,
        va="bottom",
    )

# Hide any unused subplot axis in the 2x3 layout
for ax in axs.flatten()[len(seasons):]:
    ax.axis("off")

plt.tight_layout()
plt.show()

# # Plotting the regression results for each season
# for season, (lst, tcc) in seasons.items():
#     plt.figure(figsize=(8, 6))
#     plt.scatter(lst, tcc, alpha=0.5)
#     plt.xlabel("LST Trend (Tau-b)")
#     plt.ylabel("TCC Trend (Tau-b)")
#     plt.title(f"{season}", loc='left')
#     plt.show()

#%%

# Export the plot as a PNG file
fig.savefig("TSA_OLS_results_LST_TCC.png", dpi=300, bbox_inches='tight')
plt.close()

