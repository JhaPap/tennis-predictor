# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ATP tennis match prediction app. A Python/FastAPI backend serves an XGBoost ML model that predicts match outcomes using Elo ratings, surface-specific stats, head-to-head records, and 47 engineered features (including serve/return stats from the Match Charting Project). A Next.js frontend provides the UI.

## Commands

### Data Pipeline (run from repo root)
```bash
# Full pipeline: clean CSV → compute Elo → build features → train model → seed DB
bash scripts/run_pipeline.sh

# Individual steps (run from backend/ with venv activated):
python -m pipeline.clean      # Step 1: CSV → parquet
python -m pipeline.elo        # Step 2: Compute Elo ratings
python -m pipeline.charting   # Step 3: Download charting serve/return stats
python -m pipeline.features   # Step 4: Build 47-feature matrix
python -m pipeline.train      # Step 5: Train XGBoost + isotonic calibration
python -m db.seed             # Step 6: Parquet → SQLite
```

### Backend
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload        # Runs on :8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev     # Runs on :3000
npm run build   # Production build
```

## Architecture

### Backend (`backend/`)

- **`config.py`** — Central config: all file paths, feature column list (`FEATURE_COLUMNS`), Elo K-factors, series/round mappings, CORS origins. This is the source of truth for the 47 ML features.
- **`pipeline/`** — Sequential data pipeline (must run in order: clean → elo → charting → features → train). Each step reads/writes `data/processed/matches_clean.parquet`, progressively enriching it. Anti-leakage is critical: all features use only pre-match data.
  - `clean.py` — Ingests `atp_tennis.csv`, assigns player IDs, flags active vs retired players (`both_active` column, cutoff 2023-01-01)
  - `elo.py` — Chronological Elo (overall + per-surface), records pre-match snapshots to prevent leakage
  - `charting.py` — Downloads Jeff Sackmann Match Charting Project CSVs, normalises player names, computes cumulative pre-match serve/return stats (ace rate, DF rate, 1st serve %, etc.) per player. Outputs `data/processed/charting_player_stats.parquet`. Players with no charting data use league-mean fallback values.
  - `features.py` — Builds all 47 features using running state updated *after* each row
  - `train.py` — XGBoost with temporal split (train ≤2021, val 2022-2023, test 2024+), Optuna hyperparameter tuning, isotonic probability calibration
- **`db/`** — SQLAlchemy ORM with SQLite (`data/tennis.db`). Three models: `Player`, `Match`, `PredictionLog`. `seed.py` populates from parquet files, only seeding active players.
- **`ml/predictor.py`** — Inference: builds feature vectors from live DB state for hypothetical matchups. Lazy-loads the pickled model. H2H is computed from the Match table at prediction time. `compute_confidence` factors in both data quality and prediction margin (margin < 5% = always "low", 5–12% = capped at "medium").
- **`ml/evaluation.py`** — Post-hoc evaluation (accuracy, Brier score, AUC) on resolved predictions.
- **`api/`** — FastAPI routers under `/api/`: `predict` (POST), `players`, `matches`, `leaderboard`, `tournaments`. Pydantic schemas in `schemas.py`. DB sessions via `deps.py` dependency injection.

### Frontend (`frontend/`)

Next.js 16 app with App Router, React 19, TypeScript, Tailwind CSS v4, shadcn/ui (Radix primitives), TanStack React Query, Recharts.

- **`lib/api.ts`** — API client; all backend calls go through `apiFetch()`. Base URL from `NEXT_PUBLIC_API_URL` env var (defaults to `http://localhost:8000`).
- **`lib/types.ts`** — TypeScript interfaces mirroring backend Pydantic schemas.
- **`app/`** — Pages: home (dashboard landing with hero + data panels), predict, players (search + detail), leaderboard, tournaments (list + bracket view), history, about (model details, features, tech stack).
- **`components/`** — `ui/` (shadcn primitives), `layout/` (Sidebar — hover-to-expand, sticky; Providers with React Query), `predict/` (PlayerSelector, PredictionResult, HeadToHeadCard, MatchContext), `players/` (SurfaceBreakdown, RecentForm, EloChart).

### Data Flow

`atp_tennis.csv` → pipeline (parquet intermediates) → SQLite DB → FastAPI → Next.js frontend

The ML model (`data/models/xgboost_model.pkl`) is loaded once at first prediction request and cached in memory. The model must be trained before the prediction endpoint works (returns 503 otherwise).

## Key Conventions

- Backend Python uses `sys.path.insert` for imports from the backend root — always run pipeline modules with `python -m pipeline.X` from `backend/`.
- The 60 feature columns are defined once in `config.py:FEATURE_COLUMNS` and must stay synchronized between `pipeline/features.py` (training) and `ml/predictor.py` (inference). Players without charting history use league-mean fallback values.
- Player "active" status is determined by `ACTIVE_CUTOFF` in `clean.py` — only active players are seeded into the DB and available in the API.
- Player names in the DB are stored as `"LastName FirstInitial."` (e.g., `"Musetti L."`). Use `.split(" ")[0]` to get the last name, `.split(" ").pop()` for the initial. Never assume `"FirstName LastName"` format.

## About Page Rule — MANDATORY

**`frontend/app/about/page.tsx` must be kept in sync with the actual model and data at all times.**

Whenever any of the following change, update the About page in the same task — do not wait to be asked:

| What changed | What to update in about/page.tsx |
|---|---|
| Feature count (`FEATURE_COLUMNS` length) | `STATS` "Engineered Features" value + section heading + step 2 description |
| New feature category added | Add entry to `FEATURES` array with correct `count` and `items` |
| Existing feature removed or renamed | Update or remove its `FEATURES` entry and adjust counts |
| Model retrained (new `model_metadata.json`) | `STATS` "Test Accuracy" and "AUC Score" values + step 3 card text + header paragraph |
| New data source added to pipeline | Add to step 2 description; add feature category if applicable |
| Match count or active player count changes | `STATS` "Matches Analyzed" and "Active Players" values + step 1 card text |

**Current ground truth (update this comment whenever values change):**
- Features: 60 | Accuracy: 65.0% | AUC: 0.722 | Matches: 67,199 | Active players: 457
- Data sources: `atp_tennis.csv` (ATP matches) + Match Charting Project (Overview, KeyPointsServe, KeyPointsReturn, NetPoints, Rally CSVs)
