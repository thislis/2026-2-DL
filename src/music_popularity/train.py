import json

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeRegressor

from .artifacts import FEATURES, NUMERIC, artifact_path, load_config, new_directory, write_json


def train(config, dataset, run):
    data = artifact_path("data/processed", dataset)
    frame = pd.read_csv(data / "train.csv")
    settings = load_config(config)
    transform = ColumnTransformer([
        ("genre", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["genre"]),
        ("numeric", "passthrough", NUMERIC),
    ])
    pipeline = Pipeline([("transform", transform), ("tree", DecisionTreeRegressor(**settings))])
    pipeline.fit(frame[FEATURES], frame["popularity"])
    destination = artifact_path("runs", run)
    with new_directory(destination) as out:
        joblib.dump(pipeline, out / "model.joblib")
        write_json(out / "metadata.json", {
            "dataset": dataset, "features": FEATURES, "model_settings": settings,
            "data": json.loads((data / "metadata.json").read_text()),
            "train_mean": frame["popularity"].mean(),
        })
    print(f"{destination}/model.joblib")
