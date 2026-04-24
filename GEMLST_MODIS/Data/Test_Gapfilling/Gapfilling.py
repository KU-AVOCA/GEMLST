# %%
import numpy as np
import rasterio as rio
import pandas as pd
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import tqdm

# %%
# Create markers if necessary, otherwise mute.

satfolder = "/home/jovyan/work/AVOCA/GEM/Development/Data/BatchExport_LST/YYYY/GEMLST_MODIS_yyyymmdd.tif"

# ERA5 Data:
imfolder = "/home/jovyan/work/AVOCA/GEM/Development/Data/ERA5/GL1000mCalSAT"
imfiles = sorted(Path(imfolder).glob("*.tif"))

# markers (adjust if you need case-insensitive match or different substrings)
start_marker = "t2m_1000m_cal_2016_d001.tif"  # Missing: t2m_rc_2007_d357.tif
end_marker = "t2m_1000m_cal_2016_d016.tif"    # 27.02.2020 = start orbital drift terra

output_dir = Path("/home/jovyan/work/AVOCA/GEM/Production/Gapfilled")
output_dir.mkdir(parents=True, exist_ok=True)


def process_one(imfile_str: str, satfolder_pattern: str, output_dir_str: str) -> str:
    imfile = Path(imfile_str)
    output_dir = Path(output_dir_str)

    # Find and match dates
    yearstring = imfile.stem.split("_")[3]
    year = pd.to_datetime(yearstring, format="%Y")
    doy = imfile.stem.split("_")[4][1:]
    date = year + pd.to_timedelta(int(doy) - 1, unit="D")
    datestring = date.strftime("%Y%m%d")

    imagepath = satfolder_pattern.replace("YYYY", yearstring).replace("yyyymmdd", datestring)
    output_path = output_dir / f"GEMLST_{datestring}.tiff"

    with rio.open(imagepath) as modis, rio.open(imfile) as era5:
        qa = modis.read(2)
        gapfilled = np.where(qa == 0, era5.read(1), modis.read(1)).astype(np.float32)

        # Save gapfilled as new GeoTIFF including the original qa band (qa)
        with rio.open(
            output_path,
            "w",
            driver="GTiff",
            height=gapfilled.shape[0],
            width=gapfilled.shape[1],
            count=2,
            dtype=np.float32,
            crs=modis.crs,
            transform=modis.transform,
        ) as dst:
            dst.write(gapfilled, 1)
            dst.write(qa, 2)

    return f"GEMLST_{datestring} done"


def main() -> None:
    # find first index containing the start marker and last index containing the end marker
    start_idx = next((i for i, p in enumerate(imfiles) if start_marker in p.name), None)
    end_idx = next((i for i, p in enumerate(imfiles) if end_marker in p.name), None)

    if start_idx is None:
        raise FileNotFoundError(f"No file containing '{start_marker}' found under {imfolder}")
    if end_idx is None:
        raise FileNotFoundError(f"No file containing '{end_marker}' found under {imfolder}")
    if end_idx < start_idx:
        raise ValueError(f"End file '{end_marker}' appears before start file '{start_marker}' in sorted file order")

    # slice inclusive range
    selected = imfiles[start_idx:end_idx + 1]

    # Use all CPUs minus one (at least 1 worker)
    max_workers = max(15, (os.cpu_count() or 1) - 1)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_one, str(p), satfolder, str(output_dir))
            for p in selected
        ]

        failures = 0
        with tqdm(total=len(futures), desc="Gapfilling", unit="file") as pbar:
            for fut in as_completed(futures):
                try:
                    print(fut.result())
                except Exception as e:
                    failures += 1
                    print(f"Failed: {e}")
                finally:
                    pbar.update(1)

    print(f"years {start_marker.split('_', 3)[2]} - {end_marker.split('_', 3)[2]} done")
    if failures:
        print(f"Finished with {failures} failed file(s).")


if __name__ == "__main__":
    main()