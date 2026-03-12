import json
from dotenv import load_dotenv
load_dotenv()
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from config import CORS_ORIGINS, ENVIRONMENT, MODEL_METADATA_PATH
from api.deps import get_current_user
from api.limiter import limiter
from api.routers import predictions, players, matches, leaderboard, tournaments, simulate
from api.routers import auth
from db.database import Base, engine, UserBase, user_engine

_is_prod = ENVIRONMENT == "production"

app = FastAPI(
    title="Tennis Predictor API",
    description="ATP match prediction using Elo ratings and XGBoost",
    version="1.0.0",
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    Base.metadata.create_all(bind=engine)
    UserBase.metadata.create_all(bind=user_engine)
    # Add password-reset columns if they don't exist yet (safe to run repeatedly)
    from sqlalchemy import text
    with user_engine.connect() as conn:
        for col, col_type in [("reset_token", "TEXT"), ("reset_token_expires", "DATETIME")]:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass  # Column already exists


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
