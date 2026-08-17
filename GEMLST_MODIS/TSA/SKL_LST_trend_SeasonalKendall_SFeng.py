"""
Pixel-wise trend analysis for HSA500m GeoTIFFs (daily or monthly).

Switch between daily and monthly input by setting DATA_MODE below.

Strategy
--------
- All GeoTIFFs are enumerated and sorted by date (filenames parsed).
- The full raster is divided into spatial tiles processed in parallel via
  ProcessPoolExecutor.
- Each worker opens its own rasterio handles per file and reads only its
  spatial tile, then computes statistics with scipy for every non-NaN pixel.
- NaN pixels (masked non-ice areas) produce NaN in all output bands.

Outputs:
    Trend GeoTIFF (6 bands):
        Band 1: linear_slope_per_year
        Band 2: linear_intercept
        Band 3: linear_pvalue
        Band 4: mk_tau
        Band 5: mk_pvalue
        Band 6: sens_slope_per_year

    Seasonal GeoTIFF (24 bands):
        Bands 1-12: seasonal_tau_01 ... seasonal_tau_12
        Bands 13-24: seasonal_pvalue_01 ... seasonal_pvalue_12

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

# Select input data mode: "daily" or "monthly"
DATA_MODE = "monthly"  # <-- change this to switch between modes

# --- Daily settings ---
_DAILY = dict(
    input_dir="/media/sfm/Local Data/SimonKleiner/GEMLST/Gapfilled/",
    input_glob="GEMLST_*.tiff",
    output_dir="/media/sfm/Local Data/SimonKleiner/Results/",
    output_tif="lst_trend_{DATA_MODE}.tif",
    date_regex=r"GEMLST_(\d{8})\.tif",
    date_fmt="%Y%m%d",
)

# --- Monthly settings ---
_MONTHLY = dict(
    input_dir="/media/sfm/Local Data/SimonKleiner/GEMLST/Gapfilled/monthly/",
    input_glob="GEMLST_monthly_*.tif",
    output_dir="/media/sfm/Local Data/SimonKleiner/Results/",
    output_tif="lst_trend_{DATA_MODE}.tif",
    date_regex=r"GEMLST_monthly_(\d{4}_\d{2})\.tif",
    date_fmt="%Y_%m",
)

_CFG = {"daily": _DAILY, "monthly": _MONTHLY}[DATA_MODE]
INPUT_DIR  = _CFG["input_dir"]
INPUT_GLOB = _CFG["input_glob"]
OUTPUT_DIR = _CFG["output_dir"]
OUTPUT_TIF = _CFG["output_tif"].format(DATA_MODE=DATA_MODE)
DATE_REGEX = _CFG["date_regex"]
DATE_FMT   = _CFG["date_fmt"]

# Band to read from each input file (band 1 is LST and band 2 is QA).
BAND_INDEX = 1

# Optional: restrict analysis to specific calendar months (e.g. JJA = 6,7,8).
# Set to None or empty tuple to use all months.
FILTER_MONTHS: Optional[Tuple[int, ...]] = None  # e.g. (6, 7, 8) for JJA, or None for all months
FILTER_YEARS: Optional[Tuple[int, int]] = None  # e.g. (2000, 2020) to restrict to 2000-2020, or None for all years

# Minimum number of valid (non-NaN) observations required to compute stats.
MIN_VALID_OBS = 10

# Parallelism: number of worker processes running simultaneously.
N_WORKERS = 15

# Spatial tile size in pixels (rows × cols per tile).
# Larger tiles = fewer tasks but more memory per worker.
TILE_SIZE = 256 # optimal size for this dataset: minimizes iowait while keeping memory usage reasonable.

BAND_NAMES = [
    "linear_slope_per_year",
    "linear_intercept",
    "linear_pvalue",
    "mk_tau",
    "mk_pvalue",
    "sens_slope_per_year",
] # Must match the keys returned by _process_tile and the order of output bands in the GeoTIFF.

SEASONAL_BAND_NAMES = [
    *(f"seasonal_tau_{month:02d}" for month in range(1, 13)),
    *(f"seasonal_pvalue_{month:02d}" for month in range(1, 13)),
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def decimal_year(ts: pd.DatetimeIndex) -> np.ndarray:
    """Convert DatetimeIndex to decimal years (e.g. 2020.5)."""
    year = ts.year.to_numpy(dtype=np.float64)
    day = ts.dayofyear.to_numpy(dtype=np.float64)
    return year + (day - 1.0) / 365.25


def parse_date(filename: str) -> Optional[pd.Timestamp]:
    m = re.search(DATE_REGEX, filename)
    if not m:
        return None
    return pd.to_datetime(m.group(1), format=DATE_FMT)


def collect_files(input_dir: str, pattern: str) -> Tuple[List[str], np.ndarray, np.ndarray, np.ndarray]:
    """Return sorted file list, decimal-year array, and year/month indices."""
    all_files = sorted(glob.glob(os.path.join(input_dir, pattern)))
    if not all_files:
        raise FileNotFoundError(f"No files matching {os.path.join(input_dir, pattern)}")

    files, timestamps = [], []
    for fp in all_files:
        ts = parse_date(os.path.basename(fp))
        if ts is not None:
            files.append(fp)
            timestamps.append(ts)

    if not files:
        raise RuntimeError("No files matched the date regex.")

    ts_index = pd.DatetimeIndex(timestamps)

    mask = np.ones(len(ts_index), dtype=bool)
    if FILTER_MONTHS:
        mask &= ts_index.month.isin(FILTER_MONTHS).to_numpy()
    if FILTER_YEARS:
        start_year, end_year = FILTER_YEARS
        mask &= ((ts_index.year >= start_year) & (ts_index.year <= end_year)).to_numpy()

    files = [f for f, keep in zip(files, mask) if keep]
    ts_index = ts_index[mask]

    t_year = decimal_year(ts_index).astype(np.float64)
    year_codes = pd.factorize(ts_index.year, sort=True)[0].astype(np.int16)
    month_codes = (ts_index.month.to_numpy(dtype=np.int16) - 1).astype(np.int16)
    print(f"Files found  : {len(files)}")
    print(f"Date range   : {ts_index[0].date()} → {ts_index[-1].date()}")
    if FILTER_MONTHS:
        print(f"Month filter : {FILTER_MONTHS}")
    if FILTER_YEARS:
        print(f"Year filter : {FILTER_YEARS}")
    return files, t_year, year_codes, month_codes


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
    Read one spatial tile across all time steps and compute per-pixel trends.

    Parameters
    ----------
    args : tuple
        (files, t_year, year_codes, month_codes, col_off, row_off, tile_w, tile_h,
         band_idx, min_valid_obs)

    Returns
    -------
    col_off, row_off, result_dict
        result_dict maps band name → 2-D float32 array (tile_h × tile_w).
    """
    (
        files, t_year, year_codes, month_codes,
        col_off, row_off, tile_w, tile_h,
        band_idx, min_valid_obs,
    ) = args

    n_times = len(files)
    win = Window(col_off, row_off, tile_w, tile_h)

    # Read all time steps for this tile.
    tile = np.empty((n_times, tile_h, tile_w), dtype=np.float32)
    for i, fp in enumerate(files):
        with rio.open(fp) as src:
            data = src.read(band_idx, window=win, boundless=True, fill_value=np.nan)
            tile[i] = data.astype(np.float32)


    out_shape = (tile_h, tile_w)
    lin_slope   = np.full(out_shape, np.nan, dtype=np.float32)
    lin_intercept = np.full(out_shape, np.nan, dtype=np.float32)
    lin_pvalue  = np.full(out_shape, np.nan, dtype=np.float32)
    mk_tau      = np.full(out_shape, np.nan, dtype=np.float32)
    mk_pvalue   = np.full(out_shape, np.nan, dtype=np.float32)
    sens_slope  = np.full(out_shape, np.nan, dtype=np.float32)
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
            lin_slope[r, c]     = lr.slope
            lin_intercept[r, c] = lr.intercept
            lin_pvalue[r, c]    = lr.pvalue

            # --- Seasonal Mann-Kendall (months in columns) ---
            seasonal = np.full((int(year_codes.max()) + 1, 12), np.nan, dtype=np.float64)
            for obs_idx, value in enumerate(pixel):
                if np.isfinite(value):
                    seasonal[year_codes[obs_idx], month_codes[obs_idx]] = float(value)

            seasonal_result = mstats.kendalltau_seasonal(np.ma.masked_invalid(seasonal))
            tau = float(seasonal_result["global tau"])
            mk_p = float(seasonal_result["global p-value (dep)"])
            mk_tau[r, c]    = tau
            mk_pvalue[r, c] = mk_p

            seasonal_tau = np.asarray(seasonal_result["seasonal tau"], dtype=np.float32)
            seasonal_pvalue = np.asarray(seasonal_result["seasonal p-value"], dtype=np.float32)
            for month_idx, month in enumerate(range(1, 13)):
                seasonal_maps[f"seasonal_tau_{month:02d}"][r, c] = seasonal_tau[month_idx]
                seasonal_maps[f"seasonal_pvalue_{month:02d}"][r, c] = seasonal_pvalue[month_idx]

            # --- Sen's slope (Theil-Sen estimator, slope in units/year) ---
            theil = stats.theilslopes(y, t)
            sens_slope[r, c] = theil.slope

    return col_off, row_off, {
        "linear_slope_per_year": lin_slope,
        "linear_intercept":      lin_intercept,
        "linear_pvalue":         lin_pvalue,
        "mk_tau":                mk_tau,
        "mk_pvalue":             mk_pvalue,
        "sens_slope_per_year":   sens_slope,
        **seasonal_maps,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_TIF)
    seasonal_output_path = os.path.join(OUTPUT_DIR, f"lst_trend_{DATA_MODE}_seasonal.tif")

    print("=" * 60)
    print(f"MODLST Trend Analysis — {DATA_MODE.upper()} (scipy, multiprocessing)")
    print("=" * 60)
    print(f"Input dir    : {INPUT_DIR}")
    print(f"Output file  : {output_path}")
    print(f"Season file  : {seasonal_output_path}")
    print(f"Workers      : {N_WORKERS}")
    print(f"Tile size    : {TILE_SIZE}×{TILE_SIZE} pixels")
    print()

    files, t_year, year_codes, month_codes = collect_files(INPUT_DIR, INPUT_GLOB)

    profile = raster_profile(files[0])
    height, width = profile["height"], profile["width"]
    print(f"Raster size  : {width} × {height} pixels")

    # Build output arrays in memory (6 bands).
    results_map = {name: np.full((height, width), np.nan, dtype=np.float32)
                   for name in BAND_NAMES}
    seasonal_results_map = {name: np.full((height, width), np.nan, dtype=np.float32)
                            for name in SEASONAL_BAND_NAMES}

    # Generate tile list.
    tiles = list(generate_tiles(height, width, TILE_SIZE))
    print(f"Total tiles  : {len(tiles)}")
    print()

    # Build argument list — only picklable scalars and lists.
    task_args = [
        (
            files, t_year, year_codes, month_codes,
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
                        row_off : row_off + tile_h,
                        col_off : col_off + tile_w,
                    ] = tile_results[name]
                for name in SEASONAL_BAND_NAMES:
                    seasonal_results_map[name][
                        row_off : row_off + tile_h,
                        col_off : col_off + tile_w,
                    ] = tile_results[name]
                pbar.update(1)

    # Write multi-band GeoTIFF.
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
