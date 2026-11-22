# PoC 실행 가이드

장르와 오디오 속성 네 개를 입력하면 회귀 트리가 예측한 인기 점수와 곡이 거친 분기를 확인할 수 있다. 아래 명령은 저장소 루트에서 실행한다.

## 환경 준비와 학습

Python 3.11과 `uv`를 사용한다. 저장소 루트에서 최초 1회 환경과 데이터를 준비한다. Kaggle 다운로드 도구에 필요한 `six`는 학습 환경과 별도로 설치한다.

```bash
uv sync --locked --python 3.11
mkdir -p data/raw
uvx --with six kaggle datasets download zaheenhamidani/ultimate-spotify-tracks-db --unzip -p data/raw
uv run python -m music_popularity prepare --config configs/data.toml --dataset spotify-poc
uv run python -m music_popularity train --dataset spotify-poc --config configs/models/poc-tree.toml --run poc-tree
uv run python -m music_popularity evaluate --run poc-tree
```

## 곡 한 건 예측

학습 후 아래 한 줄로 실제 홀드아웃 곡의 예상 인기 점수와 분기별 근거를 확인한다. 자신의 곡을 넣으려면 예제 JSON을 복사해 `genre`, `energy`, `valence`, `acousticness`, `tempo`를 채우고 입력 경로를 바꾼다. 장르는 학습 CSV의 표기를 따른다.

```bash
uv run python -m music_popularity predict --run poc-tree --input data/processed/spotify-poc/demo-track.json
```

평가 결과는 `runs/poc-tree/metrics.json`, 원본 체크섬과 분할 기록은 `data/processed/spotify-poc/metadata.json`에 있다. 설정을 바꿔 재학습할 때는 새 실행 이름을 지정한다. 동작 테스트는 `uv run pytest -q`로 실행한다. [모델 구조와 설명 방식](implementation-plan.md#모델과-설명-방식)
