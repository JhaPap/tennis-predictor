"""
Model evaluation utilities: Brier score, AUC, rolling accuracy.
"""

from sqlalchemy.orm import Session
from db.models import PredictionLog
from sklearn.metrics import roc_auc_score, brier_score_loss, accuracy_score
import numpy as np


def get_evaluation_stats(db: Session) -> dict:
    logs = (
        db.query(PredictionLog)
        .filter(PredictionLog.was_correct.isnot(None))
        .all()
    )

    if not logs:
        return {"message": "No resolved predictions yet"}

    probs = np.array([l.p1_win_prob for l in logs])
    actuals = np.array([int(l.was_correct) for l in logs])

    stats = {
        "total_predictions": len(logs),
        "accuracy": float(accuracy_score(actuals, (probs >= 0.5).astype(int))),
        "brier_score": float(brier_score_loss(actuals, probs)),
    }

    if len(set(actuals)) > 1:
        stats["auc"] = float(roc_auc_score(actuals, probs))

    # By surface
    surface_stats = {}
    for surface in ["Hard", "Clay", "Grass"]:
        surface_logs = [l for l in logs if l.surface == surface]
        if surface_logs:
            sp = np.array([l.p1_win_prob for l in surface_logs])
            sa = np.array([int(l.was_correct) for l in surface_logs])
            surface_stats[surface] = {
                "count": len(surface_logs),
                "accuracy": float(accuracy_score(sa, (sp >= 0.5).astype(int))),
                "brier_score": float(brier_score_loss(sa, sp)),
            }
    stats["by_surface"] = surface_stats

    return stats
