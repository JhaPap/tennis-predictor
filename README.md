# ATP Tennis Predictor

A full-stack machine learning web app that predicts ATP tennis match outcomes using 60 engineered features, Elo ratings, and real match data from 2000–2026.

**Live site:** [tennis-predictor.com](https://tennis-predictor.com)

---

## Features

- **Match Prediction** — Pick any two active ATP players, choose surface and tournament context, get a win probability with confidence level and AI-generated match analysis
- **Player Profiles** — 457 active players with Elo history, surface breakdowns, serve/return stats, and recent form
- **Leaderboard** — Live ATP Elo rankings with surface-specific ratings and trending players
- **Tournament Browser** — Browse results by tournament with full bracket views
- **Bracket Simulator** — Simulate a custom 8-player bracket and see title probabilities
- **Match History** — Full historical match log with prediction calibration chart
- **User Accounts** — Register, verify your email, and log in to access the full site

---

## How the Model Works

The prediction engine is an **XGBoost classifier** trained on 67,199 ATP matches (2000–2026) with **65% accuracy** and **0.722 AUC** on held-out 2024+ test data.

### Features (60 total)

| Category | Features |
|---|---|
| Elo ratings | Overall Elo diff, surface-specific Elo diff |
| Rankings | Rank diff, log rank ratio, points diff |
| Win rates | Overall, surface, last 20, last 5 matches |
| Head-to-head | H2H record overall and on surface |
| Match context | Grand Slam flag, best-of-5, surface, round, indoor/outdoor |
| Tournament history | Per-tournament win rate and match count |
| Serve stats | Ace rate, double fault rate, 1st serve %, 1st/2nd serve win % |
| Return stats | Return win % |
| Clutch | Break point save rate, break point conversion rate |
| Net play | Net point win rate |
| Shot quality | Unforced error rate, winner rate |

**Training:** Temporal split — train on pre-2022, validate on 2022–2023, test on 2024+. Hyperparameters tuned with Optuna (200 trials). Final probabilities calibrated with isotonic regression.

**Serve/return and clutch stats** come from Jeff Sackmann's [Match Charting Project](https://github.com/JeffSackmann/tennis_MatchChartingProject) — a crowdsourced shot-by-shot dataset. Players without charting history use league-mean fallbacks.

### AI Analysis

After the model produces a win probability, a **Claude Haiku** call generates a 2–3 sentence qualitative analysis grounded in the actual feature values (Elo gap, surface win rates, H2H, serve stats). The LLM explains the prediction — it does not change it.

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML model | XGBoost + isotonic calibration |
| Hyperparameter tuning | Optuna |
| AI analysis | Anthropic Claude Haiku |
| Backend | Python, FastAPI, SQLAlchemy, SQLite |
| Auth | JWT (python-jose), bcrypt, Resend (email verification) |
| Frontend | Next.js 16, React, TypeScript, Tailwind CSS |
| UI components | shadcn/ui |
| Data fetching | TanStack React Query |
| Charts | Recharts |
| Hosting | Vercel (frontend) + Render (backend) |

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:
```
ANTHROPIC_API_KEY=your_key_here
SECRET_KEY=any_long_random_string
RESEND_API_KEY=re_your_key        # optional — emails print to console if missing
RESEND_FROM_EMAIL=onboarding@resend.dev
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000
```

```bash
uvicorn main:app --reload         # API runs on http://localhost:8000
```

The ML model and database are pre-built and included — no pipeline run needed to start.

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

```bash
npm run dev                       # runs on http://localhost:3000
```

---

## Data Pipeline

To update match data and re-seed the database:

```bash
cd backend
source venv/bin/activate
python update_data.py             # pulls latest matches, re-runs pipeline
python update_data.py --retrain   # also retrains the XGBoost model
```

To run pipeline steps individually:

```bash
python -m pipeline.clean      # CSV → parquet
python -m pipeline.elo        # compute Elo ratings
python -m pipeline.charting   # download & process Match Charting Project stats
python -m pipeline.features   # build 60-feature matrix
python -m pipeline.train      # train XGBoost model
python -m db.seed             # populate SQLite database
```

---

## Environment Variables

### Backend

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | AI match analysis |
| `SECRET_KEY` | Yes | JWT signing key — use a long random string |
| `RESEND_API_KEY` | Yes (prod) | Email verification via Resend |
| `RESEND_FROM_EMAIL` | Yes (prod) | Sender address (must use verified domain) |
| `FRONTEND_URL` | Yes (prod) | Used in verification email links |
| `CORS_ORIGINS` | Yes (prod) | Comma-separated allowed origins |

### Frontend

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend URL (default: `http://localhost:8000`) |

---

## Data Sources

- **ATP match results (2000–2026):** Tour-level match history sourced from tennis-data.co.uk
- **Match Charting Project:** Serve, return, net, rally, and break-point stats from [JeffSackmann/tennis_MatchChartingProject](https://github.com/JeffSackmann/tennis_MatchChartingProject)
