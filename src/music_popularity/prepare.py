import hashlib
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from .artifacts import COLUMNS, FEATURES, NUMERIC, artifact_path, load_config, new_directory, write_json


def prepare(config, dataset):
    settings = load_config(config)
    path = Path(settings["raw_csv"])
    header = pd.read_csv(path, nrows=0).columns
    missing = sorted(set(COLUMNS) - set(header))
    if missing:
        raise ValueError(f"{path} 필수 열 누락: {', '.join(missing)}")
    raw = pd.read_csv(path, dtype={"track_id": "string", "genre": "string"})
    # Deduplicate on the full original schema, before projecting to PoC features.
    unique = raw.drop_duplicates()
    rows = unique[COLUMNS].copy()
    for key in ["genre", "track_id"]:
        rows[key] = rows[key].str.strip().replace("", pd.NA)
    for key in NUMERIC + ["popularity"]:
        rows[key] = pd.to_numeric(rows[key], errors="coerce")
    complete = rows.dropna()
    valid = complete["popularity"].between(0, 100)
    for key in ["energy", "valence", "acousticness"]:
        valid &= complete[key].between(0, 1)
    valid &= complete["tempo"].ge(0) & complete["tempo"].lt(float("inf"))
    clean = complete.loc[valid]
    splitter = GroupShuffleSplit(n_splits=1, test_size=settings["holdout_fraction"],
                                 random_state=settings["seed"])
    train_idx, test_idx = next(splitter.split(clean, groups=clean["track_id"]))
    train, holdout = clean.iloc[train_idx], clean.iloc[test_idx]
    demo = holdout.loc[holdout["genre"].isin(train["genre"])]
    if demo.empty:
        raise ValueError("학습 분할과 장르가 겹치는 시연 곡이 없습니다.")
    example = demo.iloc[0]
    with path.open("rb") as source:
        checksum = hashlib.file_digest(source, "sha256").hexdigest()
    metadata = dict(dataset=dataset, source="zaheenhamidani/ultimate-spotify-tracks-db",
                    raw_sha256=checksum, settings=settings, raw_rows=len(raw),
                    duplicate_rows=len(raw)-len(unique), missing_or_unparseable=len(rows)-len(complete),
                    out_of_range=len(complete)-len(clean), clean_rows=len(clean),
                    train_rows=len(train), holdout_rows=len(holdout), demo_track_id=example["track_id"])
    destination = artifact_path("data/processed", dataset)
    with new_directory(destination) as out:
        train.to_csv(out / "train.csv", index=False)
        holdout.to_csv(out / "holdout.csv", index=False)
        write_json(out / "metadata.json", metadata)
        write_json(out / "demo-track.json", example[FEATURES].to_dict())
    print(f"{destination} · 학습 {len(train):,}행 · 홀드아웃 {len(holdout):,}행")
