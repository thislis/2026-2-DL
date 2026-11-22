import json
import math
from pathlib import Path

import joblib
import pandas as pd

from .artifacts import FEATURES, NUMERIC, artifact_path


def explain_track(pipeline, track):
    if not isinstance(track, dict):
        raise ValueError("입력은 곡 한 건의 JSON 객체여야 합니다.")
    missing = sorted(set(FEATURES) - track.keys())
    if missing:
        raise ValueError(f"필수 입력 누락: {', '.join(missing)}")
    transform = pipeline.named_steps["transform"]
    genres = transform.named_transformers_["genre"].categories_[0]
    genre = track["genre"]
    if not isinstance(genre, str) or genre not in genres:
        raise ValueError(f"genre: 학습 데이터에 없는 장르 {genre!r}")
    for field in NUMERIC:
        value = track[field]
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"{field}: 유한한 숫자가 필요합니다.")
        if value < 0 or (field != "tempo" and value > 1):
            raise ValueError(f"{field}: 허용 범위를 벗어났습니다.")
    frame = pd.DataFrame([track], columns=FEATURES)
    values = transform.transform(frame)
    estimator = pipeline.named_steps["tree"]
    tree = estimator.tree_
    path = estimator.decision_path(values).indices
    means = tree.value[:, 0, 0]
    steps = []
    for parent, child in zip(path, path[1:]):
        index = tree.feature[parent]
        left = tree.children_left[parent] == child
        if index < len(genres):
            condition = f"입력 장르 {genre} · {genres[index]} 여부 = {'아니요' if left else '예'}"
        else:
            field = NUMERIC[index - len(genres)]
            condition = f"{field} {track[field]:g} {'≤' if left else '>'} {tree.threshold[parent]:.8g}"
        steps.append((condition, means[child], means[child] - means[parent]))
    return estimator.predict(values)[0], means[0], steps


def predict(run, input_path):
    model = joblib.load(artifact_path("runs", run) / "model.joblib")
    track = json.loads(Path(input_path).read_text(encoding="utf-8"))
    score, base, steps = explain_track(model, track)
    print(f"예측 인기 점수 {score:.2f} / 100\n학습 곡 전체 평균 {base:.2f}점")
    for i, (condition, mean, change) in enumerate(steps, start=1):
        print(f"{i}. {condition} → 그룹 평균 {mean:.2f}점 ({change:+.2f})")
