"""
update_data.py — Pull fresh ATP match data from tennis-data.co.uk and re-run the pipeline.

Mirrors the logic of the Kaggle notebook (dissfya/atp-tennis-daily-pull):
  - Downloads 2024, 2025, and 2026 Excel files from tennis-data.co.uk
  - Falls back to local files in data/raw/ if the download fails
  - Applies the same preprocessing (completed-only, Player_1/Player_2 assignment, score building)
  - Deduplicates against the existing atp_tennis.csv
  - Appends new matches and re-runs: clean → elo → features → seed
  - Pass --retrain to also retrain the XGBoost model (slow, not needed for daily runs)

Usage (from backend/ with venv active):
    python update_data.py
    python update_data.py --retrain

If tennis-data.co.uk is unreachable, place the Excel files here and re-run:
    backend/data/raw/2024.xlsx
    backend/data/raw/2025.xlsx
    backend/data/raw/2026.xlsx
Download them from: http://tennis-data.co.uk/YEAR/YEAR.xlsx
"""

import sys
import zipfile
import subprocess
import numpy as np
import pandas as pd
import requests
from io import BytesIO
from pathlib import Path

# ── Ensure config imports work when run from backend/ ──────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from config import CSV_PATH

# Years to refresh — always re-download these since the files grow as matches complete
REFRESH_YEARS = [2024, 2025, 2026]

# Local fallback directory — place downloaded Excel files here if network fails
RAW_DIR = Path(__file__).parent / "data" / "raw"


# ─────────────────────────────────────────────────────────────────────────────
# Download helpers
# ─────────────────────────────────────────────────────────────────────────────

def _year_url(year: int) -> str:
    """tennis-data.co.uk URL for a given year."""
    base = f"http://tennis-data.co.uk/{year}/{year}"
    if year == 2008:
        return base + ".zip"
    if year <= 2012:
        return base + ".xls"
    return base + ".xlsx"


def _local_path(year: int) -> Path | None:
    """Return a local file path for the year if one exists in data/raw/."""
    for ext in (".xlsx", ".xls", ".zip"):
        p = RAW_DIR / f"{year}{ext}"
        if p.exists():
            return p
    return None


def download_year(year: int) -> pd.DataFrame | None:
    """Download and return the raw DataFrame for one year.

    Tries the network first; falls back to data/raw/YEAR.xlsx if download fails.
    Returns None if neither source is available.
    """
    url = _year_url(year)
    print(f"  GET {url}")
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        content = BytesIO(resp.content)
        if url.endswith(".zip"):
            zf = zipfile.ZipFile(content)
            return pd.read_excel(zf.open(zf.namelist()[0]))
        return pd.read_excel(content)
    except Exception as exc:
        print(f"  ⚠  Download failed: {exc}")

    # Network failed — try local file
    local = _local_path(year)
    if local:
        print(f"  → Using local file: {local.name}")
        try:
            if local.suffix == ".zip":
                zf = zipfile.ZipFile(local)
                return pd.read_excel(zf.open(zf.namelist()[0]))
            return pd.read_excel(local)
        except Exception as exc:
            print(f"  ⚠  Could not read local file: {exc}")
            return None

    print(f"  ✗  No data for {year} (network failed, no local file in data/raw/)")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Processing (matches the Kaggle notebook logic)
# ─────────────────────────────────────────────────────────────────────────────

def _build_score(row: pd.Series, p1_is_winner: bool) -> str:
    """Reconstruct a score string from per-set columns."""
    if p1_is_winner:
        pairs = [
            (row.get("W1", 0), row.get("L1", 0)),
            (row.get("W2", 0), row.get("L2", 0)),
            (row.get("W3", 0), row.get("L3", 0)),
            (row.get("W4", 0), row.get("L4", 0)),
            (row.get("W5", 0), row.get("L5", 0)),
        ]
    else:
        pairs = [
            (row.get("L1", 0), row.get("W1", 0)),
            (row.get("L2", 0), row.get("W2", 0)),
            (row.get("L3", 0), row.get("W3", 0)),
            (row.get("L4", 0), row.get("W4", 0)),
            (row.get("L5", 0), row.get("W5", 0)),
        ]
    return " ".join(f"{a}-{b}" for a, b in pairs if not (a == 0 and b == 0))


def process_raw(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transform a raw tennis-data.co.uk DataFrame into the atp_tennis.csv format.
    Mirrors the Kaggle notebook exactly.
    """
    df = raw.copy()

    # Fill missing best-of
    if "Best of" in df.columns:
        df["Best of"] = df["Best of"].fillna(3)

    # Completed matches only
    if "Comment" in df.columns:
        df = df[df["Comment"] == "Completed"].reset_index(drop=True)

    # Drop rows missing core ranking / set data
    for col in ["WRank", "LRank", "W1", "W2", "L1", "L2"]:
        if col in df.columns:
            df = df[df[col].notna()].reset_index(drop=True)

    if df.empty:
        return df

    # Fill missing set columns (W3-W5, L3-L5)
    for col in ["W3", "W4", "W5", "L3", "L4", "L5"]:
        if col in df.columns:
            df[col] = df[col].replace(" ", 0).fillna(0)

    # Convert set columns to int
    for col in ["W1", "L1", "W2", "L2", "W3", "L3", "W4", "L4", "W5", "L5"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Fill betting odds — prefer B365, fall back to market average or AvgW/L
    w_fallbacks = [c for c in ["CBW", "GBW", "IWW", "SBW", "EXW", "PSW", "UBW", "LBW"] if c in df.columns]
    l_fallbacks = [c for c in ["CBL", "GBL", "IWL", "SBL", "EXL", "PSL", "UBL", "LBL"] if c in df.columns]
    if "B365W" not in df.columns:
        df["B365W"] = np.nan
    if "B365L" not in df.columns:
        df["B365L"] = np.nan
    if w_fallbacks:
        df["B365W"] = df["B365W"].fillna(df[w_fallbacks].mean(axis=1))
    if "AvgW" in df.columns:
        df["B365W"] = df["B365W"].fillna(df["AvgW"])
    if l_fallbacks:
        df["B365L"] = df["B365L"].fillna(df[l_fallbacks].mean(axis=1))
    if "AvgL" in df.columns:
        df["B365L"] = df["B365L"].fillna(df["AvgL"])

    # Deterministic Player_1 / Player_2 assignment.
    # Use a hash of (Date, Winner, Loser) so repeated runs give the same result,
    # regardless of row order — unlike the notebook's row-index modulo approach.
    winner_col = "Winner" if "Winner" in df.columns else None
    loser_col  = "Loser"  if "Loser"  in df.columns else None
    if winner_col is None or loser_col is None:
        print("  ⚠  Missing Winner/Loser columns — skipping.")
        return pd.DataFrame()

    df["_ind"] = df.apply(
        lambda r: hash(
            str(r.get("Date", "")) + str(r[winner_col]) + str(r[loser_col])
        ) % 2,
        axis=1,
    )

    df["Player_1"] = df.apply(lambda r: r[winner_col] if r["_ind"] == 0 else r[loser_col], axis=1)
    df["Player_2"] = df.apply(lambda r: r[winner_col] if r["_ind"] == 1 else r[loser_col], axis=1)
    df["Rank_1"]   = df.apply(lambda r: r["WRank"] if r["_ind"] == 0 else r["LRank"], axis=1)
    df["Rank_2"]   = df.apply(lambda r: r["WRank"] if r["_ind"] == 1 else r["LRank"], axis=1)
    df["Pts_1"]    = df.apply(lambda r: r.get("WPts", np.nan) if r["_ind"] == 0 else r.get("LPts", np.nan), axis=1)
    df["Pts_2"]    = df.apply(lambda r: r.get("WPts", np.nan) if r["_ind"] == 1 else r.get("LPts", np.nan), axis=1)
    df["Odd_1"]    = df.apply(lambda r: r["B365W"] if r["_ind"] == 0 else r["B365L"], axis=1)
    df["Odd_2"]    = df.apply(lambda r: r["B365W"] if r["_ind"] == 1 else r["B365L"], axis=1)
    df["Score"]    = df.apply(lambda r: _build_score(r, r["_ind"] == 0), axis=1)

    # Keep only the columns the backend pipeline expects
    keep = [
        "Tournament", "Date", "Series", "Court", "Surface", "Round", "Best of",
        "Player_1", "Player_2", "Winner",
        "Rank_1", "Rank_2", "Pts_1", "Pts_2", "Odd_1", "Odd_2", "Score",
    ]
    out = df[[c for c in keep if c in df.columns]].copy()

    # Normalise ranks/pts: -1 sentinel → NaN
    for col in ["Rank_1", "Rank_2", "Pts_1", "Pts_2"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").replace({-1: np.nan, -1.0: np.nan})

    out["Date"] = pd.to_datetime(out["Date"], errors="coerce")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline runner
# ─────────────────────────────────────────────────────────────────────────────

def run_step(module: str, backend_dir: Path) -> None:
    """Run a backend pipeline module via subprocess using the venv Python."""
    venv_python = backend_dir / "venv" / "bin" / "python"
    python = str(venv_python) if venv_python.exists() else sys.executable
    result = subprocess.run([python, "-m", module], cwd=str(backend_dir))
    if result.returncode != 0:
        print(f"\n❌  {module} failed (exit {result.returncode}). Aborting.")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    retrain = "--retrain" in sys.argv
    backend_dir = Path(__file__).parent

    print("=" * 55)
    print("  ATP Tennis Data Update")
    print("=" * 55)

    # ── 1. Load existing CSV ─────────────────────────────────
    print(f"\nLoading existing data → {CSV_PATH.name}")
    existing = pd.read_csv(CSV_PATH)
    existing["Date"] = pd.to_datetime(existing["Date"], errors="coerce")
    max_date = existing["Date"].max()
    print(f"  {len(existing):,} rows  |  latest match: {max_date.date()}")

    # Deduplication key: (date-as-string, winner-name) — one winner per day per match
    existing_keys = set(
        zip(
            existing["Date"].dt.strftime("%Y-%m-%d"),
            existing["Winner"].astype(str).str.strip(),
        )
    )

    # ── 2. Download & process recent years ──────────────────
    new_frames: list[pd.DataFrame] = []

    for year in REFRESH_YEARS:
        print(f"\nYear {year}")
        raw = download_year(year)
        if raw is None or raw.empty:
            print(f"  (no data)")
            continue

        processed = process_raw(raw)
        if processed.empty:
            continue

        # Only consider matches after an overlap window (re-check last 14 days
        # to catch any late-uploaded results for the period around max_date)
        overlap_start = max_date - pd.Timedelta(days=14)
        candidate = processed[processed["Date"] > overlap_start].copy()

        # Deduplicate
        candidate_keys = list(
            zip(
                candidate["Date"].dt.strftime("%Y-%m-%d"),
                candidate["Winner"].astype(str).str.strip(),
            )
        )
        mask = [k not in existing_keys for k in candidate_keys]
        new_matches = candidate[mask].copy()

        total_in_file = len(processed)
        print(f"  {total_in_file:,} completed matches in file → {len(new_matches):,} new")

        if not new_matches.empty:
            new_frames.append(new_matches)
            # Register keys so later years don't double-add
            for k in candidate_keys:
                existing_keys.add(k)

    # ── 3. Merge & save ──────────────────────────────────────
    if not new_frames:
        print("\n✓ No new matches found — data is already current.")
    else:
        added = pd.concat(new_frames, ignore_index=True)
        added["Date"] = added["Date"].dt.strftime("%Y-%m-%d")
        existing["Date"] = existing["Date"].dt.strftime("%Y-%m-%d")

        combined = pd.concat([existing, added], ignore_index=True)
        combined.to_csv(CSV_PATH, index=False)
        print(f"\nSaved {len(combined):,} rows to {CSV_PATH.name}  (+{len(added):,} new)")

    # ── 4. Re-run pipeline ───────────────────────────────────
    steps = ["pipeline.clean", "pipeline.elo", "pipeline.charting", "pipeline.features"]
    if retrain:
        steps.append("pipeline.train")
        print("\n⚠  --retrain flag set: XGBoost will be retrained (this takes a few minutes)")
    steps.append("db.seed")

    print(f"\n{'─'*55}")
    print("  Running pipeline")
    print(f"{'─'*55}")
    for step in steps:
        print(f"\n▶  {step}")
        run_step(step, backend_dir)

    print(f"\n{'='*55}")
    print("  ✓ Update complete!")
    if not retrain:
        print("  Tip: run with --retrain to also retrain the model.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
