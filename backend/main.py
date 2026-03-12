import json
from dotenv import load_dotenv
load_dotenv()
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import CORS_ORIGINS, MODEL_METADATA_PATH
from api.deps import get_current_user
from api.routers import predictions, players, matches, leaderboard, tournaments, simulate
from api.routers import auth
from db.database import Base, engine

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

# Public — auth endpoints have no auth requirement
app.include_router(auth.router)

# Protected — all other routers require a valid, verified JWT
_auth_dep = [Depends(get_current_user)]
app.include_router(predictions.router, dependencies=_auth_dep)
app.include_router(players.router, dependencies=_auth_dep)
app.include_router(matches.router, dependencies=_auth_dep)
app.include_router(leaderboard.router, dependencies=_auth_dep)
app.include_router(tournaments.router, dependencies=_auth_dep)
app.include_router(simulate.router, dependencies=_auth_dep)


@app.on_event("startup")
def on_startup():
    # Create any missing tables (including users) without dropping existing data
    Base.metadata.create_all(bind=engine)


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
