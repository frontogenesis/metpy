# ── Cell 1: Install ───────────────────────────────────────────────────────────
%pip install -q siphon xarray netCDF4 numpy pandas matplotlib

# ── Cell 2: Imports ───────────────────────────────────────────────────────────
import warnings
warnings.filterwarnings("ignore")

from datetime import datetime, timezone, timedelta

import numpy as np
import pandas as pd
import xarray as xr
from xarray.backends import NetCDF4DataStore
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from siphon.catalog import TDSCatalog

# ── Cell 3: Configuration — edit this ─────────────────────────────────────────
LAT   =  29.77      # Latitude  (decimal degrees, positive = North)
LON   = -93.90      # Longitude (decimal degrees, negative = West)
MODEL = "auto"      # "auto" | "hrrr" | "gfs"
HOURS = 48          # Forecast hours to display
SAVE_PNG = False
SAVE_CSV = False

# ── Cell 4: Constants ─────────────────────────────────────────────────────────
CATEGORIES = {
    "LIFR": (0,     500),
    "IFR":  (500,   1000),
    "MVFR": (1000,  3000),
    "VFR":  (3000,  99999),
}
CAT_COLORS = {
    "LIFR": "#cc00cc",
    "IFR":  "#ff0000",
    "MVFR": "#0000ff",
    "VFR":  "#00aa00",
}

THREDDS = "https://thredds.ucar.edu/thredds/catalog"

HRRR_CATALOG = (
    f"{THREDDS}/grib/NCEP/HRRR/CONUS_2p5km/catalog.xml"
    "?dataset=grib/NCEP/HRRR/CONUS_2p5km/Best"
)
GFS_CATALOG = (
    f"{THREDDS}/grib/NCEP/GFS/Global_0p25deg/catalog.xml"
    "?dataset=grib/NCEP/GFS/Global_0p25deg/Best"
)

# Fallback pressure levels if ceiling variable isn't available
LOW_P  = 925 * 100   # Pa
MID_P  = 700 * 100   # Pa
HIGH_P = 400 * 100   # Pa

# ── Cell 5: Helpers ───────────────────────────────────────────────────────────
def _pa_to_ft(pressure_pa, surface_pa):
    if pressure_pa >= surface_pa:
        return 0.0
    return 8000.0 * np.log(surface_pa / pressure_pa) * 3.28084

def classify(ceiling_ft):
    for cat, (lo, hi) in CATEGORIES.items():
        if lo <= ceiling_ft < hi:
            return cat
    return "VFR"

def _get_var(data, keywords):
    """Find first variable whose name contains any of the keywords (case-insensitive)."""
    for v in data.data_vars:
        if any(k.lower() in v.lower() for k in keywords):
            arr = data[v].values.squeeze().astype(float)
            return arr
    return None

# ── Cell 6: Fetch via Siphon NCSS ─────────────────────────────────────────────
def _fetch(catalog_url, lat, lon, hours, cloud_keywords, psfc_keywords):
    print("  Connecting to THREDDS catalog …")
    cat  = TDSCatalog(catalog_url)
    ds   = list(cat.datasets.values())[0]
    ncss = ds.subset()

    want_cloud = [v for v in ncss.variables
                  if any(k.lower() in v.lower() for k in cloud_keywords)]
    want_psfc  = [v for v in ncss.variables
                  if any(k.lower() in v.lower() for k in psfc_keywords)]
    want = want_cloud + want_psfc

    if not want_cloud:
        print(f"  No cloud variables found. Available:\n  {sorted(ncss.variables)[:30]}")
        return None

    print(f"  Requesting: {want}")

    now   = datetime.now(timezone.utc)
    query = ncss.query()
    query.lonlat_point(lon, lat)
    query.time_range(now, now + timedelta(hours=hours))
    query.variables(*want)
    query.accept("netcdf4")

    print("  Fetching time series …")
    raw  = ncss.get_data(query)
    data = xr.open_dataset(NetCDF4DataStore(raw))
    print(f"  Done — variables returned: {list(data.data_vars)}")
    return data


def fetch_hrrr(lat, lon, hours):
    if not (-134 <= lon <= -60 and 21 <= lat <= 53):
        print("  Location outside HRRR CONUS domain.")
        return None
    print("[ HRRR ]")
    return _fetch(
        HRRR_CATALOG, lat, lon, hours,
        cloud_keywords=["Geopotential_height_cloud_ceiling",
                        "Geopotential_height_Cloud_ceiling",
                        "Low_cloud", "Medium_cloud", "High_cloud"],
        psfc_keywords=["Pressure_surface"],
    )


def fetch_gfs(lat, lon, hours):
    print("[ GFS 0.25° ]")
    return _fetch(
        GFS_CATALOG, lat, lon, hours,
        cloud_keywords=["Geopotential_height_cloud_ceiling",
                        "Geopotential_height_Cloud_ceiling",
                        "Low_cloud", "Medium_cloud", "High_cloud"],
        psfc_keywords=["Pressure_surface"],
    )

# ── Cell 7: Parse into ceiling series ────────────────────────────────────────
def _parse_ceiling_derived(data, times):
    """Fallback: derive ceiling from low/mid/high cloud cover layers."""
    lcdc = _get_var(data, ["Low_cloud",    "low_cloud"])
    mcdc = _get_var(data, ["Medium_cloud", "mid_cloud"])
    hcdc = _get_var(data, ["High_cloud",   "high_cloud"])
    psfc = _get_var(data, ["Pressure_surface", "pressure_surface"])
    if psfc is None:
        psfc = np.full(len(times), 101325.0)

    ceilings = []
    for i in range(len(times)):
        ps         = float(psfc[i])
        ceiling_ft = 99999.0
        for arr, p_pa in [(lcdc, LOW_P), (mcdc, MID_P), (hcdc, HIGH_P)]:
            if arr is not None and float(arr[i]) >= 50:
                ceiling_ft = _pa_to_ft(p_pa, ps)
                break
        ceilings.append(ceiling_ft)

    return pd.Series(ceilings, index=times, name="ceiling_ft")


def parse_ceiling(data):
    time_coord = next((c for c in data.coords if "time" in c.lower()), None)
    times = pd.to_datetime(data[time_coord].values).tz_localize("UTC").tz_convert("US/Central")

    # Prefer the direct cloud ceiling geopotential height field
    hgt_ceil = _get_var(data, ["Geopotential_height_cloud_ceiling",
                                "Geopotential_height_Cloud_ceiling"])

    if hgt_ceil is not None:
        print("  Using direct cloud ceiling variable (gpm → ft).")
        # gpm → feet; NaN = clear sky / no ceiling → unlimited
        ceilings = np.where(np.isnan(hgt_ceil), 99999.0, hgt_ceil * 3.28084)
        return pd.Series(ceilings, index=times, name="ceiling_ft")

    print("  Cloud ceiling variable not found — falling back to layer derivation.")
    return _parse_ceiling_derived(data, times)

# ── Cell 8: Plot ──────────────────────────────────────────────────────────────
def plot_ceiling(series, lat, lon, model):
    cats    = series.apply(classify)
    display = series.clip(upper=25000)

    fig, ax = plt.subplots(figsize=(14, 5))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    ax.fill_between(series.index, display, alpha=0.15, color="#4fc3f7", step="post")
    ax.step(series.index, display, where="post", color="#4fc3f7", linewidth=1.2, alpha=0.6)

    for cat, color in CAT_COLORS.items():
        mask = cats == cat
        if mask.any():
            ax.scatter(series.index[mask], display[mask], color=color, s=30, zorder=5)

    for label, ft in {"LIFR/IFR": 500, "IFR/MVFR": 1000, "MVFR/VFR": 3000}.items():
        ax.axhline(ft, color="white", alpha=0.2, linewidth=0.8, linestyle="--")
        ax.text(series.index[-1], ft + 200, label, color="white", alpha=0.45, fontsize=7, ha="right")

    ax.set_ylim(0, 6000)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xlabel("Valid Time (CT)", color="white")
    ax.set_ylabel("Cloud Ceiling (ft AGL)", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")

    ax.set_title(
        f"{model} Cloud Ceiling Forecast (via Unidata THREDDS / Siphon NCSS)\n"
        f"Lat {lat:.2f}°  Lon {lon:.2f}°  |  "
        f"Init: {series.index[0].strftime('%Y-%m-%d %H:%M CT')}",
        color="white", fontsize=11
    )

    patches = [mpatches.Patch(color=c, label=k) for k, c in CAT_COLORS.items()]
    ax.legend(handles=patches, loc="upper right", framealpha=0.3, labelcolor="white", fontsize=9)
    plt.tight_layout()
    plt.show()

    if SAVE_PNG:
        fname = f"ceiling_{LAT:.2f}_{LON:.2f}.png"
        fig.savefig(fname, dpi=150, bbox_inches="tight")
        from google.colab import files
        files.download(fname)

# ── Cell 9: Run ───────────────────────────────────────────────────────────────
raw_data, model_used = None, ""

if MODEL in ("hrrr", "auto"):
    raw_data = fetch_hrrr(LAT, LON, HOURS)
    if raw_data is not None:
        model_used = "HRRR 2.5km"

if raw_data is None:
    raw_data = fetch_gfs(LAT, LON, HOURS)
    model_used = "GFS 0.25°"

series = parse_ceiling(raw_data)
cats   = series.apply(classify)

print(f"\n  Model      : {model_used}")
print(f"  Range      : {series.index[0]}  →  {series.index[-1]}")
print(f"  Steps      : {len(series)}")
print(f"  Min ceiling: {series.min():,.0f} ft  ({classify(series.min())})")
print(f"  Max ceiling: {series.max():,.0f} ft  ({classify(series.max())})")

plot_ceiling(series, LAT, LON, model_used)

# ── Cell 10: Optional CSV ─────────────────────────────────────────────────────
if SAVE_CSV:
    fname = f"ceiling_{LAT:.2f}_{LON:.2f}.csv"
    pd.DataFrame({"ceiling_ft": series, "category": cats}).to_csv(fname)
    from google.colab import files
    files.download(fname)