import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import rasterio as rio
import tqdm
import vaex as vx
from sklearn.model_selection import train_test_split


# Paths and runtime configuration
LANDMASK_PATH = "/home/jovyan/work/AVOCA/GEM/Development/Data/Masks/Landmask.tif"
ICEMASK_PATH = "/home/jovyan/work/AVOCA/GEM/Development/Data/Masks/Icemask.tif"
SAT_TEMPLATE = "/home/jovyan/work/AVOCA/GEM/Development/Data/BatchExport_LST/YYYY/GEMLST_MODIS_yyyymmdd.tif"
ERA5_FOLDER = "/home/jovyan/work/AVOCA/GEM/Development/Data/ERA5/GL1000m_reproj"

OUTPUT_DIR = "/home/jovyan/work/AVOCA/GEM/Development/Data/ERA5/Output_tables"
OUTPUT_TRAIN_ICE_DIR = os.path.join(OUTPUT_DIR, "Training", "Ice")
OUTPUT_TRAIN_LAND_DIR = os.path.join(OUTPUT_DIR, "Training", "Land")
OUTPUT_TEST_ICE_DIR = os.path.join(OUTPUT_DIR, "Testing", "Ice")
OUTPUT_TEST_LAND_DIR = os.path.join(OUTPUT_DIR, "Testing", "Land")

START_MARKER = "t2m_1000m_2000_d100.tif"
END_MARKER = "t2m_1000m_2000_d149.tif"
NUM_CORES = 10
TEST_SIZE = 0.3
RANDOM_STATE = 42


# Globals populated in each worker via init_worker.
WORKER_IS_ICE: Optional[np.ndarray] = None
WORKER_IS_LAND: Optional[np.ndarray] = None
WORKER_SAT_TEMPLATE: Optional[str] = None
WORKER_OUTPUT_DIRS: Optional[Dict[str, str]] = None

def ensure_output_dirs() -> Dict[str, str]:
    dirs = {
        "train_ice": OUTPUT_TRAIN_ICE_DIR,
        "train_land": OUTPUT_TRAIN_LAND_DIR,
        "test_ice": OUTPUT_TEST_ICE_DIR,
        "test_land": OUTPUT_TEST_LAND_DIR,
    }
    for out_dir in dirs.values():
        os.makedirs(out_dir, exist_ok=True)
    return dirs


def load_masks(landmask_path: str, icemask_path: str) -> Tuple[np.ndarray, np.ndarray]:
    with rio.open(landmask_path) as landmask_file:
        is_land = landmask_file.read(1).ravel() == 1

    with rio.open(icemask_path) as icemask_file:
        is_ice = icemask_file.read(1).ravel() == 1

    return is_land, is_ice


def list_era5_files(era5_folder: str, start_marker: str, end_marker: str) -> list[Path]:
    imfiles = sorted(Path(era5_folder).glob("*.tif"))

    start_idx = next((i for i, p in enumerate(imfiles) if start_marker in p.name), None)
    end_idx = next((i for i, p in enumerate(imfiles) if end_marker in p.name), None)

    if start_idx is None:
        raise FileNotFoundError(f"No file containing '{start_marker}' found under {era5_folder}")
    if end_idx is None:
        raise FileNotFoundError(f"No file containing '{end_marker}' found under {era5_folder}")
    if end_idx < start_idx:
        raise ValueError(
            f"End file '{end_marker}' appears before start file '{start_marker}' in sorted file order"
        )

    return imfiles[start_idx : end_idx + 1]


def parse_date_from_era5(imfile: Path) -> str:
    yearstring = imfile.stem.split("_")[2]
    year = pd.to_datetime(yearstring, format="%Y")
    doy = imfile.stem.split("_")[3][1:]
    date = year + pd.to_timedelta(int(doy) - 1, unit="D")
    return date.strftime("%Y-%m-%d")


def sat_path_from_date(sat_template: str, date: str) -> str:
    yearstring = date[:4]
    datestring = date.replace("-", "")
    return sat_template.replace("YYYY", yearstring).replace("yyyymmdd", datestring), datestring


def init_worker(
    is_ice: np.ndarray,
    is_land: np.ndarray,
    sat_template: str,
    output_dirs: Dict[str, str],
) -> None:
    global WORKER_IS_ICE, WORKER_IS_LAND, WORKER_SAT_TEMPLATE, WORKER_OUTPUT_DIRS
    WORKER_IS_ICE = is_ice
    WORKER_IS_LAND = is_land
    WORKER_SAT_TEMPLATE = sat_template
    WORKER_OUTPUT_DIRS = output_dirs


def process_single_era5_file(imfile: str) -> Dict[str, Any]:
    if WORKER_IS_ICE is None or WORKER_IS_LAND is None or WORKER_SAT_TEMPLATE is None or WORKER_OUTPUT_DIRS is None:
        raise RuntimeError("Worker is not initialized")

    imfile_path = Path(imfile)
    date = parse_date_from_era5(imfile_path)
    sat_image_path, datestring = sat_path_from_date(WORKER_SAT_TEMPLATE, date)

    with rio.open(sat_image_path) as sat:
        sat_lst = sat.read(1)
        sat_qa = sat.read(2)
    sat_lst = np.where(sat_qa == 0, np.nan, sat_lst)

    with rio.open(imfile_path) as era5_file:
        era5_t2m = era5_file.read(1)

    era5_1d = era5_t2m.ravel()
    satlst_1d = sat_lst.ravel()

    na_mask = ~np.isnan(era5_1d) & ~np.isnan(satlst_1d)
    na_mask_ice = na_mask & WORKER_IS_ICE
    na_mask_land = na_mask & WORKER_IS_LAND

    era5_1d_nona_ice = era5_1d[na_mask_ice]
    satlst_1d_nona_ice = satlst_1d[na_mask_ice]
    era5_1d_nona_land = era5_1d[na_mask_land]
    satlst_1d_nona_land = satlst_1d[na_mask_land]

    if len(era5_1d_nona_ice) < 2 or len(era5_1d_nona_land) < 2:
        return {
            "status": "skipped",
            "file": imfile_path.name,
            "date": date,
            "ice_points": int(len(era5_1d_nona_ice)),
            "land_points": int(len(era5_1d_nona_land)),
            "reason": "not enough valid points for train_test_split",
        }

    df_ice = pd.DataFrame({"date": [date] * len(era5_1d_nona_ice), "era5": era5_1d_nona_ice, "satlst": satlst_1d_nona_ice})
    df_land = pd.DataFrame({"date": [date] * len(era5_1d_nona_land), "era5": era5_1d_nona_land, "satlst": satlst_1d_nona_land})

    ice_train, ice_test = train_test_split(df_ice, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    land_train, land_test = train_test_split(df_land, test_size=TEST_SIZE, random_state=RANDOM_STATE)

    vx.from_pandas(ice_train, copy_index=False).export_hdf5(
        os.path.join(WORKER_OUTPUT_DIRS["train_ice"], f"comparison_train_ice_{datestring}.h5"), mode="w"
    )
    vx.from_pandas(ice_test, copy_index=False).export_hdf5(
        os.path.join(WORKER_OUTPUT_DIRS["test_ice"], f"comparison_test_ice_{datestring}.h5"), mode="w"
    )
    vx.from_pandas(land_train, copy_index=False).export_hdf5(
        os.path.join(WORKER_OUTPUT_DIRS["train_land"], f"comparison_train_land_{datestring}.h5"), mode="w"
    )
    vx.from_pandas(land_test, copy_index=False).export_hdf5(
        os.path.join(WORKER_OUTPUT_DIRS["test_land"], f"comparison_test_land_{datestring}.h5"), mode="w"
    )

    return {
        "status": "ok",
        "file": imfile_path.name,
        "date": date,
        "ice_points": int(len(era5_1d_nona_ice)),
        "land_points": int(len(era5_1d_nona_land)),
    }


def run_parallel_processing(imfiles: list[Path], is_ice: np.ndarray, is_land: np.ndarray, output_dirs: Dict[str, str]) -> None:
    success = 0
    failed = 0
    skipped = 0

    with ProcessPoolExecutor(
        max_workers=NUM_CORES,
        initializer=init_worker,
        initargs=(is_ice, is_land, SAT_TEMPLATE, output_dirs),
    ) as executor:
        future_to_file = {executor.submit(process_single_era5_file, str(imfile)): imfile for imfile in imfiles}

        with tqdm.tqdm(total=len(future_to_file), desc="Processing") as pbar:
            for future in as_completed(future_to_file):
                imfile = future_to_file[future]
                try:
                    result = future.result()
                    status = result["status"]
                    if status == "ok":
                        success += 1
                    elif status == "skipped":
                        skipped += 1
                    else:
                        failed += 1
                except Exception as exc:
                    failed += 1
                    result = {"status": "failed", "file": imfile.name, "reason": str(exc)}

                pbar.update(1)
                pbar.set_postfix(success=success, skipped=skipped, failed=failed, last_file=result["file"])

    print(f"ALL FILES DONE | success={success}, skipped={skipped}, failed={failed}")


def main() -> None:
    output_dirs = ensure_output_dirs()
    is_land, is_ice = load_masks(LANDMASK_PATH, ICEMASK_PATH)
    imfiles = list_era5_files(ERA5_FOLDER, START_MARKER, END_MARKER)
    run_parallel_processing(imfiles, is_ice, is_land, output_dirs)


if __name__ == "__main__":
    main()
