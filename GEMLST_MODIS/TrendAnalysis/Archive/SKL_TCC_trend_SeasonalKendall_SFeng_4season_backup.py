"""
Pixel-wise trend analysis for seasonal GeoTIFF averages.

This is a seasonal-input version of the original script. Instead of monthly or
	daily rasters, each input file is one seasonal average image, representing one
of the four climate seasons:
    - DJF
    - MAM
    - JJA
    - SON

The seasonal cycle is arranged as a 4-column matrix per year, with the file name
carrying the year of the middle month of the season. In this convention, DJF is
assigned to the January year, so a file named FILE_2001_DJF represents the
season December 2000, January 2001, and February 2001. The sequence therefore
behaves like:
    MAM 2000, JJA 2000, SON 2000, DJF 2001, MAM 2001, ... , SON 2025

Outputs:
    Trend GeoTIFF (6 bands):
        Band 1: linear_slope_per_year
        Band 2: linear_intercept
        Band 3: linear_pvalue
        Band 4: mk_tau
        Band 5: mk_pvalue
        Band 6: sens_slope_per_year

    Seasonal GeoTIFF (8 bands):
        Bands 1-4: seasonal_tau_DJF, seasonal_tau_MAM, seasonal_tau_JJA, seasonal_tau_SON
        Bands 5-8: seasonal_pvalue_DJF, seasonal_pvalue_MAM, seasonal_pvalue_JJA, seasonal_pvalue_SON

Shunan Feng (shunan.feng@envs.au.dk)
Simon Kleiner (wqv321@alumni.ku.dk)
"""
#%%
import glob
import os
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import rasterio as rio
from rasterio.windows import Window
from scipy import stats
from scipy.stats import mstats
from tqdm import tqdm

#%%
# ---------------------------------------------------------------------------
# Configuration — edit these before running
# ---------------------------------------------------------------------------

DATA_MODE = "4seasons"

# Example file naming convention:
#   GEMLST_2000_MAM.tif
#   GEMLST_2000_JJA.tif
#   GEMLST_2000_SON.tif
#   GEMLST_2001_DJF.tif
#
_SEASONAL = dict(
    input_dir="/media/sfm/Local Data/SimonKleiner/CARRA/TCC_quarterly/",
    input_glob="TCC_*.tif",
    output_dir="/media/sfm/Local Data/SimonKleiner/Results/quarterly/",
    output_tif="tcc_trend_{DATA_MODE}.tif",
    date_regex=r"TCC_(\d{4})_(MAM|JJA|SON|DJF)\.tif",
)

_CFG = _SEASONAL
INPUT_DIR = _CFG["input_dir"]
INPUT_GLOB = _CFG["input_glob"]
OUTPUT_DIR = _CFG["output_dir"]
OUTPUT_TIF = _CFG["output_tif"].format(DATA_MODE=DATA_MODE)
DATE_REGEX = _CFG["date_regex"]

# DJF inherits the year of its middle month (January), so FILE_2001_DJF represents
# Dec 2000 + Jan 2001 + Feb 2001, and it is placed after SON 2000.
SEASON_ORDER = ("MAM", "JJA", "SON", "DJF")
SEASON_TO_COL = {season: idx for idx, season in enumerate(SEASON_ORDER)}
SEASON_TO_MONTHS = {
    "DJF": (12, 1, 2),
    "MAM": (3, 4, 5),
    "JJA": (6, 7, 8),
    "SON": (9, 10, 11),
}

# The first valid season is MAM of the first year and the last valid season is
# SON of the last year, with DJF assigned to the January year of the season.
FIRST_SEASON = "MAM"
LAST_SEASON = "SON"

# Band to read from each input file (band 1 is LST and band 2 is QA).
BAND_INDEX = 1

# Optional year filter. Example: (2000, 2025) to restrict to those years.
FILTER_YEARS: Optional[Tuple[int, int]] = None

# Minimum number of valid (non-NaN) observations required to compute stats.
MIN_VALID_OBS = 10

# Parallelism: number of worker processes running simultaneously.
N_WORKERS = 15

# Spatial tile size in pixels (rows × cols per tile).
TILE_SIZE = 256

BAND_NAMES = [
    "linear_slope_per_year",
    "linear_intercept",
    "linear_pvalue",
    "mk_tau",
    "mk_pvalue",
    "sens_slope_per_year",
]

SEASONAL_BAND_NAMES = [
    *(f"seasonal_tau_{season}" for season in SEASON_ORDER),
    *(f"seasonal_pvalue_{season}" for season in SEASON_ORDER),
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def seasonal_decimal_year(year: int, season: str) -> float:
    """Return a decimal-year position for each seasonal composite to calculate linear trends.
    The decimal-year is placed at the middle of the season."""

    offsets = {"MAM": 0.25, "JJA": 0.50, "SON": 0.75, "DJF": 0.00}
    return float(year) + offsets[season]


def parse_date(filename: str) -> Optional[Tuple[int, str, pd.Timestamp]]:
    """Return (year, season, representative timestamp) or None if it does not match."""
    m = re.search(DATE_REGEX, filename)
    if not m:
        return None

    year = int(m.group(1))
    season = m.group(2)
    if season not in SEASON_TO_COL:
        return None

    month_map = {
        "DJF": 1,
        "MAM": 4,
        "JJA": 7,
        "SON": 10,
    }
    day_map = {"DJF": 15, "MAM": 15, "JJA": 15, "SON": 15}
    ts = pd.Timestamp(year=year, month=month_map[season], day=day_map[season])
    return year, season, ts


def collect_files(input_dir: str, pattern: str) -> Tuple[List[str], np.ndarray, np.ndarray, np.ndarray]:
    """Return sorted file list, decimal-year array, year codes, and season codes."""
    all_files = sorted(glob.glob(os.path.join(input_dir, pattern)))
    if not all_files:
        raise FileNotFoundError("No files matching the input_glob pattern (double-check parameters)")

    records = []
    for fp in all_files:
        parsed = parse_date(os.path.basename(fp))
        if parsed is None:
            continue
        year, season, timestamp = parsed
        if FILTER_YEARS and not (FILTER_YEARS[0] <= year <= FILTER_YEARS[1]):
            continue
        records.append((fp, year, season, timestamp))

    if not records:
        raise RuntimeError("No files matched the seasonal date regex or the chosen year filter.")

    records.sort(key=lambda x: x[3])
    files = [fp for fp, _, _, _ in records]
    years = np.array([year for _, year, _, _ in records], dtype=np.int32)
    seasons = [season for _, _, season, _ in records]

    t_year = np.array(
        [seasonal_decimal_year(year, season) for year, season in zip(years, seasons)],
        dtype=np.float64,
    )
    year_codes = pd.factorize(years, sort=True)[0].astype(np.int16)
    season_codes = np.array([SEASON_TO_COL[season] for season in seasons], dtype=np.int16)

    print(f"Files found   : {len(files)}")
    print(f"Season range  : {min(years)}-{max(years)}")
    print(f"First season  : {FIRST_SEASON}")
    print(f"Last season   : {LAST_SEASON}")
    print(f"Season order  : {SEASON_ORDER}")
    if FILTER_YEARS:
        print(f"Year filter   : {FILTER_YEARS}")
    return files, t_year, year_codes, season_codes


def raster_profile(filepath: str) -> dict:
    with rio.open(filepath) as src:
        return {
            "width": src.width,
            "height": src.height,
            "crs": src.crs,
            "transform": src.transform,
        }


def generate_tiles(height: int, width: int, tile_size: int):
    """Yield (col_off, row_off, tile_w, tile_h) for all tiles."""
    for row_off in range(0, height, tile_size):
        tile_h = min(tile_size, height - row_off)
        for col_off in range(0, width, tile_size):
            tile_w = min(tile_size, width - col_off)
            yield col_off, row_off, tile_w, tile_h


# ---------------------------------------------------------------------------
# Worker function (must be module-level for pickling)
# ---------------------------------------------------------------------------


def _process_tile(args):
    """
    Read one spatial tile across all seasonal time steps and compute per-pixel trends.

    Parameters
    ----------
    args : tuple
        (files, t_year, year_codes, season_codes, col_off, row_off, tile_w, tile_h,
         band_idx, min_valid_obs)

    Returns
    -------
    col_off, row_off, result_dict
        result_dict maps band name → 2-D float32 array (tile_h × tile_w).
    """
    (
        files, t_year, year_codes, season_codes,
        col_off, row_off, tile_w, tile_h,
        band_idx, min_valid_obs,
    ) = args

    n_times = len(files)
    win = Window(col_off, row_off, tile_w, tile_h)

    # Read all seasonal time steps for this tile.
    tile = np.empty((n_times, tile_h, tile_w), dtype=np.float32)
    for i, fp in enumerate(files):
        with rio.open(fp) as src:
            data = src.read(band_idx, window=win, boundless=True, fill_value=np.nan)
            tile[i] = data.astype(np.float32)

    out_shape = (tile_h, tile_w)
    lin_slope = np.full(out_shape, np.nan, dtype=np.float32)
    lin_intercept = np.full(out_shape, np.nan, dtype=np.float32)
    lin_pvalue = np.full(out_shape, np.nan, dtype=np.float32)
    mk_tau = np.full(out_shape, np.nan, dtype=np.float32)
    mk_pvalue = np.full(out_shape, np.nan, dtype=np.float32)
    sens_slope = np.full(out_shape, np.nan, dtype=np.float32)
    seasonal_maps = {
        name: np.full(out_shape, np.nan, dtype=np.float32)
        for name in SEASONAL_BAND_NAMES
    }

    for r in range(tile_h):
        for c in range(tile_w):
            pixel = tile[:, r, c]
            valid = np.isfinite(pixel)
            n_valid = int(valid.sum())

            # Skip masked (non-ice) pixels — output stays NaN.
            if n_valid < min_valid_obs:
                continue

            y = pixel[valid].astype(np.float64)
            t = t_year[valid]

            # --- Linear regression ---
            lr = stats.linregress(t, y)
            lin_slope[r, c] = lr.slope
            lin_intercept[r, c] = lr.intercept
            lin_pvalue[r, c] = lr.pvalue

            # --- Seasonal Mann-Kendall (four seasons per year) ---
            seasonal = np.full((int(year_codes.max()) + 1, len(SEASON_ORDER)), np.nan, dtype=np.float64)
            for obs_idx, value in enumerate(pixel):
                if np.isfinite(value):
                    seasonal[year_codes[obs_idx], season_codes[obs_idx]] = float(value)

            seasonal_result = mstats.kendalltau_seasonal(np.ma.masked_invalid(seasonal))
            tau = float(seasonal_result["global tau"])
            mk_p = float(seasonal_result["global p-value (dep)"])
            mk_tau[r, c] = tau
            mk_pvalue[r, c] = mk_p

            seasonal_tau = np.asarray(seasonal_result["seasonal tau"], dtype=np.float32)
            seasonal_pvalue = np.asarray(seasonal_result["seasonal p-value"], dtype=np.float32)
            for season_idx, season in enumerate(SEASON_ORDER):
                seasonal_maps[f"seasonal_tau_{season}"][r, c] = seasonal_tau[season_idx]
                seasonal_maps[f"seasonal_pvalue_{season}"][r, c] = seasonal_pvalue[season_idx]

            # --- Sen's slope (Theil-Sen estimator, slope in units/year) ---
            theil = stats.theilslopes(y, t)
            sens_slope[r, c] = theil.slope

    return col_off, row_off, {
        "linear_slope_per_year": lin_slope,
        "linear_intercept": lin_intercept,
        "linear_pvalue": lin_pvalue,
        "mk_tau": mk_tau,
        "mk_pvalue": mk_pvalue,
        "sens_slope_per_year": sens_slope,
        **seasonal_maps,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_TIF)
    seasonal_output_path = os.path.join(OUTPUT_DIR, f"tcc_trend_{DATA_MODE}_quarters.tif")

    print("=" * 60)
    print(f"Seasonal TCC Trend Analysis — {DATA_MODE.upper()} (scipy, multiprocessing)")
    print("=" * 60)
    print(f"Input dir   : {INPUT_DIR}")
    print(f"Output file : {output_path}")
    print(f"Season file : {seasonal_output_path}")
    print(f"Workers     : {N_WORKERS}")
    print(f"Tile size   : {TILE_SIZE}×{TILE_SIZE} pixels")
    print()

    files, t_year, year_codes, season_codes = collect_files(INPUT_DIR, INPUT_GLOB)

    profile = raster_profile(files[0])
    height, width = profile["height"], profile["width"]
    print(f"Raster size : {width} × {height} pixels")

    # Build output arrays in memory (6 bands).
    results_map = {name: np.full((height, width), np.nan, dtype=np.float32)
                   for name in BAND_NAMES}
    seasonal_results_map = {name: np.full((height, width), np.nan, dtype=np.float32)
                            for name in SEASONAL_BAND_NAMES}

    tiles = list(generate_tiles(height, width, TILE_SIZE))
    print(f"Total tiles : {len(tiles)}")
    print()

    task_args = [
        (
            files, t_year, year_codes, season_codes,
            col_off, row_off, tile_w, tile_h,
            BAND_INDEX, MIN_VALID_OBS,
        )
        for col_off, row_off, tile_w, tile_h in tiles
    ]

    with ProcessPoolExecutor(max_workers=N_WORKERS) as executor:
        futures = {executor.submit(_process_tile, arg): arg for arg in task_args}
        with tqdm(total=len(futures), unit="tile", desc="Processing") as pbar:
            for future in as_completed(futures):
                col_off, row_off, tile_results = future.result()
                tile_h = tile_results["linear_slope_per_year"].shape[0]
                tile_w = tile_results["linear_slope_per_year"].shape[1]
                for name in BAND_NAMES:
                    results_map[name][
                        row_off: row_off + tile_h,
                        col_off: col_off + tile_w,
                    ] = tile_results[name]
                for name in SEASONAL_BAND_NAMES:
                    seasonal_results_map[name][
                        row_off: row_off + tile_h,
                        col_off: col_off + tile_w,
                    ] = tile_results[name]
                pbar.update(1)

    print(f"\nWriting output: {output_path}")
    with rio.open(files[0]) as src:
        out_profile = src.profile.copy()

    out_profile.update(
        count=len(BAND_NAMES),
        dtype="float32",
        nodata=np.nan,
        compress="LZW",
        predictor=3,
        tiled=True,
        blockxsize=256,
        blockysize=256,
        driver="GTiff",
    )

    with rio.open(output_path, "w", **out_profile) as dst:
        for i, name in enumerate(BAND_NAMES, start=1):
            dst.write(results_map[name], i)
            dst.set_band_description(i, name)

    seasonal_profile = out_profile.copy()
    seasonal_profile.update(count=len(SEASONAL_BAND_NAMES))

    print(f"Writing seasonal output: {seasonal_output_path}")
    with rio.open(seasonal_output_path, "w", **seasonal_profile) as dst:
        for i, name in enumerate(SEASONAL_BAND_NAMES, start=1):
            dst.write(seasonal_results_map[name], i)
            dst.set_band_description(i, name)

    print("Done.")


if __name__ == "__main__":
    main()

# %%
