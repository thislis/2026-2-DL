import json
from tempfile import NamedTemporaryFile
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error

from .artifacts import FEATURES, artifact_path


def evaluate(run):
    out = artifact_path("runs", run)
    metadata = json.loads((out / "metadata.json").read_text())
    data = artifact_path("data/processed", metadata["dataset"])
    if json.loads((data / "metadata.json").read_text()) != metadata["data"]:
        raise ValueError("학습에 사용한 데이터셋과 현재 분할 정보가 다릅니다.")
    holdout = pd.read_csv(data / "holdout.csv")
    scores = joblib.load(out / "model.joblib").predict(holdout[FEATURES])
    target = holdout["popularity"]
    metrics = {"holdout_rows": len(target), "tree_mae": mean_absolute_error(target, scores),
               "mean_baseline_mae": (target - metadata["train_mean"]).abs().mean()}
    report = json.dumps(metrics, indent=2)
    with NamedTemporaryFile(mode="w", dir=out, delete=False) as tmp:
        tmp.write(report + "\n")
    Path(tmp.name).replace(out / "metrics.json")
    print(report)
