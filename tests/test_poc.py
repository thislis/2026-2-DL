import json

import joblib
import pandas as pd
import pytest

from music_popularity.artifacts import FEATURES
from music_popularity.evaluate import evaluate
from music_popularity.explain import explain_track
from music_popularity.prepare import prepare
from music_popularity.train import train


def test_group_split_and_explanation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rows = []
    for i in range(40):
        for genre, genre_score in (("Folk", 0), ("Pop", 60)):
            rows.append(dict(genre=genre, energy=i / 40, valence=0.5, acousticness=0.2,
                             tempo=95, track_id=f"id-{i}", popularity=genre_score + i))
    pd.DataFrame(rows + [rows[0], {**rows[1], "energy": None}]).to_csv("raw.csv", index=False)
    config = tmp_path / "data.toml"
    config.write_text('raw_csv="raw.csv"\nseed=42\nholdout_fraction=0.2\n')
    prepare(config, "demo")
    data = tmp_path / "data/processed/demo"
    training = pd.read_csv(data / "train.csv")
    holdout = pd.read_csv(data / "holdout.csv")
    assert set(training.track_id).isdisjoint(holdout.track_id)
    assert len(training) + len(holdout) == len(rows)
    assert 0 in [*training.popularity, *holdout.popularity]

    model_config = tmp_path / "tree.toml"
    model_config.write_text("max_depth=3\nrandom_state=42\nmin_samples_leaf=2\n")
    train(model_config, "demo", "tree")
    evaluate("tree")
    run = tmp_path / "runs/tree"
    assert json.loads((run / "metrics.json").read_text())["holdout_rows"] == len(holdout)
    model = joblib.load(run / "model.joblib")
    example = json.loads((data / "demo-track.json").read_text())
    assert list(example) == FEATURES
    score, base, steps = explain_track(model, example)
    assert 0 < len(steps) <= 3
    assert base + sum(delta for _, _, delta in steps) == pytest.approx(score)
    assert score == pytest.approx(model.predict(pd.DataFrame([example]))[0])
    with pytest.raises(ValueError, match="genre"):
        explain_track(model, {**example, "genre": "unknown"})
    with pytest.raises(ValueError, match="energy"):
        explain_track(model, {**example, "energy": -1})
