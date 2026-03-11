# ATP Tennis Predictor

A machine learning web app that predicts ATP tennis match outcomes using 60 engineered features, Elo ratings, and real match data from 2000–2026.

## What It Does

- **Match Prediction** — Select any two active ATP players, choose a surface and tournament context, and get a win probability with confidence level and an AI-generated match analysis
- **Player Profiles** — Browse 457 active players with Elo history, surface breakdowns, recent form, and career stats
- **Leaderboard** — Live ATP Elo rankings with surface-specific ratings
- **Tournament Browser** — Explore results by tournament and view bracket outcomes
- **Match History** — Full historical match log with filtering

## How the Model Works

The prediction engine is an **XGBoost classifier** trained on 67,199 ATP matches (2000–2026) with **65% accuracy** and **0.722 AUC** on held-out 2024+ test data.

### Features (60 total)

| Category | Examples |
|---|---|
| Elo ratings | Overall Elo diff, surface-specific Elo diff |
| Rankings | Rank diff, log rank ratio, points diff |
| Win rates | Overall, surface, last 20, last 5 matches |
| Head-to-head | H2H record overall and on surface |
| Match context | Grand Slam flag, best-of-5, surface, round, indoor |
| Tournament history | Per-tournament win rate and match count |
| Serve stats | Ace rate, DF rate, 1st serve %, 1st/2nd serve win % |
| Return stats | Return win % |
| Clutch (break points) | BP save rate, BP conversion rate |
| Net play | Net point win rate |
| Shot quality | Unforced error rate, winner rate |

**Training setup:** Temporal split — train on pre-2022, validate on 2022–2023, test on 2024+. Hyperparameters tuned with Optuna (200 trials). Final probabilities calibrated with isotonic regression.

**Serve/return and clutch stats** come from Jeff Sackmann's [Match Charting Project](https://github.com/JeffSackmann/tennis_MatchChartingProject) — a crowdsourced shot-by-shot dataset covering thousands of matches. Players without charting history use league-mean fallbacks.

### AI Match Analysis

After the model produces a win probability, a **Claude Haiku** LLM call generates a 2–3 sentence qualitative analysis grounded in the actual feature values (Elo gap, surface win rates, H2H, serve stats). The LLM explains — it does not override the probability.

## Tech Stack

| Layer | Technology |
|---|---|
| ML model | XGBoost + isotonic calibration (scikit-learn) |
| Hyperparameter tuning | Optuna |
| AI analysis | Anthropic Claude Haiku |
| Backend | Python, FastAPI, SQLAlchemy, SQLite |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS v4 |
| UI components | shadcn/ui (Radix primitives) |
| Data fetching | TanStack React Query |
| Charts | Recharts |

## Data Sources

- **ATP match results (2000–2026):** Historical CSV covering all ATP tour-level matches
- **Match Charting Project:** Serve, return, net, rally, and break-point stats from Jeff Sackmann's crowdsourced dataset

## Local Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your ANTHROPIC_API_KEY
uvicorn main:app --reload     # runs on :8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                   # runs on :3000
```

The ML model and database are pre-built and included in the repo — no pipeline run needed to start the server.

## Running the Data Pipeline

To retrain the model from scratch (requires `atp_tennis.csv` in the repo root):

```bash
bash scripts/run_pipeline.sh
```

Or run steps individually from `backend/` with the venv activated:

```bash
python -m pipeline.clean      # CSV → parquet
python -m pipeline.elo        # Compute Elo ratings
python -m pipeline.charting   # Download & process charting stats
python -m pipeline.features   # Build 60-feature matrix
python -m pipeline.train      # Train XGBoost model
python -m db.seed             # Populate SQLite database
```

## Environment Variables

| Variable | Where | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | backend `.env` | Required for AI match analysis |
| `CORS_ORIGINS` | backend `.env` | Comma-separated allowed origins (production) |
| `NEXT_PUBLIC_API_URL` | frontend `.env.local` | Backend URL (default: `http://localhost:8000`) |
