import json
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import CORS_ORIGINS, MODEL_METADATA_PATH
from api.routers import predictions, players, matches, leaderboard, tournaments, simulate

app = FastAPI(
    title="Tennis Predictor API",
    description="ATP match prediction using Elo ratings and XGBoost",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predictions.router)
app.include_router(players.router)
app.include_router(matches.router)
app.include_router(leaderboard.router)
app.include_router(tournaments.router)
app.include_router(simulate.router)


@app.get("/api/health")
def health():
    model_trained = MODEL_METADATA_PATH.exists()
    metadata = {}
    if model_trained:
        with open(MODEL_METADATA_PATH) as f:
            metadata = json.load(f)
    return {
        "status": "ok",
        "model_trained": model_trained,
        "model_metadata": metadata,
    }
