from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from api.deps import get_db
from api.schemas import PredictRequest, PredictResponse, PredictionLogEntry, CalibrationBucket, H2HMatch
from ml.predictor import predict_match, get_match_analysis, load_model
from ml.evaluation import get_evaluation_stats
from db.models import PredictionLog, Match, Player

router = APIRouter(prefix="/api/predict", tags=["predictions"])

_calibration_cache: list[CalibrationBucket] | None = None


@router.post("", response_model=PredictResponse)
def predict(req: PredictRequest, db: Session = Depends(get_db)):
    if req.player1_id == req.player2_id:
        raise HTTPException(status_code=400, detail="Players must be different")
    try:
        result = predict_match(
            db=db,
            player1_id=req.player1_id,
            player2_id=req.player2_id,
            surface=req.surface,
            series=req.series,
            round_name=req.round,
            best_of=req.best_of,
            tournament=req.tournament,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Model not trained yet. Run the pipeline first."
        )


@router.post("/analysis")
def analysis(req: PredictRequest, db: Session = Depends(get_db)):
    if req.player1_id == req.player2_id:
        raise HTTPException(status_code=400, detail="Players must be different")
    try:
        text = get_match_analysis(
            db=db,
            player1_id=req.player1_id,
            player2_id=req.player2_id,
            surface=req.surface,
            series=req.series,
            round_name=req.round,
            best_of=req.best_of,
            tournament=req.tournament,
        )
        return {"analysis": text}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Model not trained yet.")


@router.get("/history")
def prediction_history(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    total = db.query(PredictionLog).count()
    logs = (
        db.query(PredictionLog)
        .order_by(PredictionLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "items": [PredictionLogEntry.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/h2h", response_model=list[H2HMatch])
def get_h2h_matches(
    p1_id: int = Query(...),
    p2_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """All historical matches between two players, newest first."""
    matches = (
        db.query(Match)
        .filter(
            or_(
                and_(Match.player1_id == p1_id, Match.player2_id == p2_id),
                and_(Match.player1_id == p2_id, Match.player2_id == p1_id),
            )
        )
        .order_by(Match.date.desc())
        .all()
    )

    result = []
    for m in matches:
        winner = db.query(Player).get(m.winner_id)
        result.append(H2HMatch(
            id=m.id,
            date=m.date,
            tournament=m.tournament,
            surface=m.surface,
            series=m.series,
            round=m.round,
            winner_name=winner.name if winner else "Unknown",
            score=m.score,
            rank1=m.rank1,
            rank2=m.rank2,
        ))
    return result


@router.get("/evaluation")
def model_evaluation(db: Session = Depends(get_db)):
    return get_evaluation_stats(db)


@router.get("/calibration", response_model=list[CalibrationBucket])
def model_calibration():
    """Model calibration on 2024+ test set: predicted probability vs actual win rate."""
    global _calibration_cache
    if _calibration_cache is not None:
        return _calibration_cache

    import pandas as pd
    import numpy as np
    from config import MATCHES_CLEAN_PATH, FEATURE_COLUMNS

    if not MATCHES_CLEAN_PATH.exists():
        raise HTTPException(status_code=503, detail="matches_clean.parquet not found. Run the pipeline first.")

    try:
        model, metadata = load_model()
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Model not trained yet. Run the pipeline first.")

    df = pd.read_parquet(MATCHES_CLEAN_PATH)

    # Test set: 2024+ (use both_active filter if available)
    if "both_active" in df.columns:
        df = df[df["both_active"]].copy()
    test = df[df["Date"] >= "2024-01-01"].copy()
    if test.empty:
        raise HTTPException(status_code=404, detail="No test data found for 2024+.")

    # Use only the feature columns the model was actually trained on so that
    # adding new features to FEATURE_COLUMNS doesn't break an existing model.
    model_cols = metadata.get("feature_columns", FEATURE_COLUMNS)
    available_cols = [c for c in model_cols if c in test.columns]
    X_test = test[available_cols].values
    y_test = test["p1_won"].values
    probs = model.predict_proba(X_test)[:, 1]

    # For below-50% predictions, flip so we always work with the favored player
    flipped_probs = np.where(probs >= 0.5, probs, 1 - probs)
    flipped_wins = np.where(probs >= 0.5, y_test, 1 - y_test)

    # Bin into 10 buckets: 50-55, 55-60, ..., 95-100
    bins = np.arange(0.50, 1.01, 0.05)
    bucket_labels = [f"{int(b*100)}–{int((b+0.05)*100)}%" for b in bins[:-1]]

    buckets = []
    for i, (lo, label) in enumerate(zip(bins[:-1], bucket_labels)):
        hi = bins[i + 1]
        mask = (flipped_probs >= lo) & (flipped_probs < hi)
        count = int(mask.sum())
        if count == 0:
            predicted_avg = float(lo + 0.025)
            actual_rate = 0.0
        else:
            predicted_avg = float(flipped_probs[mask].mean())
            actual_rate = float(flipped_wins[mask].mean())
        buckets.append(CalibrationBucket(
            bucket_label=label,
            predicted_avg=round(predicted_avg, 3),
            actual_rate=round(actual_rate, 3),
            count=count,
        ))

    _calibration_cache = buckets
    return _calibration_cache
