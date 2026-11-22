"""Shared paths and publication of complete dataset and model directories."""

import json
import re
import tomllib
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

FEATURES = ["genre", "energy", "valence", "acousticness", "tempo"]
NUMERIC = FEATURES[1:]
COLUMNS = FEATURES + ["popularity", "track_id"]


def artifact_path(parent, name):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
        raise ValueError(f"잘못된 산출물 ID: {name}")
    return Path(parent) / name


def load_config(path):
    with Path(path).open("rb") as source:
        return tomllib.load(source)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")


@contextmanager
def new_directory(destination):
    if destination.exists():
        raise FileExistsError(f"{destination} 경로가 이미 있습니다. 새 ID를 사용하세요.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as tmp:
        staging = Path(tmp) / "output"
        staging.mkdir()
        yield staging
        staging.rename(destination)
