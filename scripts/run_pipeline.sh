#!/bin/bash
# Full pipeline: clean → elo → charting → features → train → seed
# Run from TennisPredictor/ root directory

set -e

BACKEND_DIR="$(dirname "$0")/../backend"
cd "$BACKEND_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "=========================================="
echo " Tennis Predictor Pipeline"
echo "=========================================="

echo ""
echo "[1/5] Cleaning CSV data..."
python -m pipeline.clean

echo ""
echo "[2/5] Computing Elo ratings..."
python -m pipeline.elo

echo ""
echo "[3/5] Downloading charting stats (Match Charting Project)..."
python -m pipeline.charting

echo ""
echo "[4/5] Building feature matrix..."
python -m pipeline.features

echo ""
echo "[5/5] Training XGBoost model..."
python -m pipeline.train

echo ""
echo "[6/6] Seeding database..."
python -m db.seed

echo ""
echo "=========================================="
echo " Pipeline complete!"
echo " Start the API with: uvicorn main:app --reload"
echo "=========================================="
