# 곡 한 건의 인기 예측과 설명을 위한 PoC 구현 계획

**완료 장면**은 터미널에서 실제 곡 한 건을 입력하고, 한 번의 명령으로 “예측 인기 점수는 몇 점인가?”와 “이 곡의 어떤 속성 때문에 그 점수가 나왔는가?”에 대한 답을 함께 보는 것이다. 여기서 곡 입력은 Spotify 스냅샷과 같은 형식의 **장르와 오디오 속성**을 뜻한다. 시연용 입력은 실제 홀드아웃 트랙에서 자동으로 만들고, 같은 형식이면 사용자가 준비한 곡도 넣을 수 있게 한다.

이번에는 CPU에서 얕은 회귀 트리 하나를 학습해 데이터 준비부터 곡별 설명까지 연결한다. 원음 파일에서 속성을 추출하는 기능, Transformer 비교, 전체·장르별 SHAP 분석, 편곡 추천은 후속 단계로 둔다. [전체 프로젝트 개요](../project-overview.md) · [PoC 실행 가이드](run-guide.md)

## 데이터셋 확보와 준비

학습 원본은 Kaggle의 `zaheenhamidani/ultimate-spotify-tracks-db`에서 받는 `SpotifyFeatures.csv`로 정한다. `tgel0/spotify-data`는 Spotify Web API의 오디오 속성을 BigQuery로 수집하는 과정을 참고할 수 있는 저장소다. 이 저장소의 README가 연결하는 Kaggle 데이터는 별도 배포본인 `tomigelo/spotify-audio-features`다. PoC는 첫 번째 배포본의 장르·오디오 속성·인기 점수를 함께 사용하므로, CSV 하나를 받으면 Spotify API 키나 Google Cloud 배포 없이 로컬에서 진행할 수 있다. [PoC 학습 데이터](https://www.kaggle.com/datasets/zaheenhamidani/ultimate-spotify-tracks-db/data) · [수집 코드와 노트북](https://github.com/tgel0/spotify-data) · [수집 저장소가 연결한 별도 데이터](https://www.kaggle.com/datasets/tomigelo/spotify-audio-features)

### 원본 CSV 배치

저장소 루트에서 다음 명령을 실행한다. `uvx`로 Kaggle CLI를 실행하면 프로젝트의 학습 의존성에 다운로드 도구를 추가할 필요가 없다. 브라우저를 사용한다면 위 Kaggle 학습 데이터 페이지에서 **Download**를 선택하고 압축을 풀어 같은 경로에 CSV를 둔다. [Kaggle CLI 다운로드 명세](https://github.com/Kaggle/kaggle-cli/blob/main/docs/datasets.md#kaggle-datasets-download)

```bash
mkdir -p data/raw
uvx --with six kaggle datasets download zaheenhamidani/ultimate-spotify-tracks-db --unzip -p data/raw
head -n 1 data/raw/SpotifyFeatures.csv
sha256sum data/raw/SpotifyFeatures.csv
```

`configs/data.toml`에는 저장소 루트 기준 원본 경로 `data/raw/SpotifyFeatures.csv`를 지정한다. 다운로드한 CSV는 그대로 보관하고, `prepare`가 원본의 SHA-256과 데이터셋 식별자를 분할 정보에 함께 기록하도록 한다. 같은 이름의 파일을 다시 받았을 때도 어느 스냅샷으로 학습했는지 확인할 수 있다.

### 학습에 넘길 열과 분할

| CSV 열 | 준비 단계에서의 용도 |
|---|---|
| `genre`, `energy`, `valence`, `acousticness`, `tempo` | 예측 입력 5개. 장르는 문자열로, 나머지는 수치로 읽는다. |
| `popularity` | 0~100의 학습·평가 정답. 0도 유효한 값이다. |
| `track_id` | 같은 곡을 같은 분할에 배정하는 문자열 키. 모델 입력에서 제외한다. |

`prepare`는 먼저 헤더에서 이 일곱 열을 확인한다. 열이 빠졌다면 누락된 이름과 사용한 파일 경로를 출력해 배포본을 확인할 수 있게 한다. 제안서의 232,725행 × 18열은 참고 규모로 두고, 실제 원본 행 수와 정제 후 행 수를 기록한다.

완전히 중복된 행과 필수값 누락 행을 집계한 뒤 제외한다. 한 트랙이 여러 장르에 등장하면 장르별 행은 보존하되 `track_id`를 묶어 시드 42로 학습·홀드아웃을 약 80/20으로 나눈다. **준비 완료 기준**은 두 분할의 트랙 ID가 겹치지 않고, 홀드아웃의 실제 곡에서 입력 5개만 추출한 `data/processed/spotify-poc/demo-track.json`을 얻는 것이다. 시연 곡은 학습 분할에도 등장한 장르에서 고른다.

## 곡 입력과 출력

PoC는 원본 스키마에서 소수의 열을 골라 사용한다. 필수 입력은 장르 `genre`, 에너지 `energy`, 정서적 밝기 `valence`, 어쿠스틱 정도 `acousticness`, 템포 `tempo`다. 앞의 세 수치 속성은 0~1, 템포 단위는 BPM이다. 사용자는 이 값들이 담긴 JSON 한 건을 넘긴다. 다음은 형식을 보여주는 예다.

```json
{"genre": "Folk", "energy": 0.25, "valence": 0.30, "acousticness": 0.85, "tempo": 95}
```

`popularity`는 학습·평가용 정답이며 추론 입력에서 제외한다. CLI는 필수 키와 값의 형식을 확인한다. 값이 빠지거나 학습 때 보지 못한 장르가 들어오면 해당 필드와 이유를 표시한다.

**출력 예시**는 아래와 같다. 수치는 시연 형식을 위한 가상 값이다. 구현 시에는 저장한 모델에서 분기 조건과 점수를 직접 읽는다.

```text
예측 인기 점수  44.0 / 100
학습 곡 전체의 평균 예측은 50.0점입니다.
1. energy 0.25가 0.40 이하인 가지로 이동했습니다. 이 그룹의 평균은 42.0점입니다 (−8.0).
2. acousticness 0.85가 0.70을 넘는 가지로 이동했습니다. 이 그룹의 평균은 44.0점입니다 (+2.0).
```

## 모델과 설명 방식

scikit-learn의 전처리와 회귀기를 하나의 `Pipeline`으로 저장한다. 장르는 원-핫 인코딩하고 네 수치 열은 원래 단위로 전달한다. 회귀기는 `DecisionTreeRegressor(max_depth=3, min_samples_leaf=20, random_state=42)`로 고정한다. 한 곡의 예측을 최대 세 번의 분기로 읽을 수 있고, 리프에 도달한 학습 곡들의 평균 인기 점수가 곧 예측값이므로 출력도 0~100 범위에 있다.

설명기는 해당 곡이 실제로 거친 노드만 순서대로 읽는다. 각 노드에서 원래 속성명, 입력값, 분기 조건, **자식 평균 − 부모 평균**을 출력한다. 장르 분기는 ‘장르가 Folk인가?’처럼 표시한다. 루트 평균에 경로의 모든 점수 차이를 더하면 최종 예측과 일치한다. 이 차이는 모델이 곡을 더 좁은 그룹에 배정하며 바뀐 예측값이다. 속성을 편집했을 때 얻을 인기 상승량은 별도의 연구 질문이다.

## 구현 순서

| 순서 | 작업 | 다음 단계로 넘길 결과 |
|---|---|---|
| 1. 데이터 준비 | `prepare.py`에서 위의 CSV 열 검사, 정제, 트랙 단위 분할을 구현한다. | `data/processed/spotify-poc/`에 학습·홀드아웃 표본, 분할 정보, `demo-track.json` 저장 |
| 2. 학습 | `train.py`에서 학습 표본만으로 인코더와 트리를 맞춘다. 고정 설정으로 한 번 학습한다. | `runs/poc-tree/`에 전처리를 포함한 모델, 입력 열 순서, 데이터셋 ID와 설정 저장 |
| 3. 평가 | `evaluate.py`에서 저장한 모델로 홀드아웃을 예측한다. MAE를 학습 표본 평균을 항상 출력하는 기준선의 MAE와 나란히 보고한다. | 같은 실행 폴더의 `metrics.json`에 표본 수와 두 MAE 기록 |
| 4. 단건 예측과 설명 | `__main__.py`에 `predict` 명령을 연결한다. 모델을 다시 불러와 JSON 한 건을 변환한 뒤 예측하고, `explain.py`에서 같은 트리 경로를 사람이 읽을 수 있는 문장으로 바꾼다. | 표준 출력에 예측 점수, 비교 기준인 루트 평균, 해당 곡이 거친 분기별 설명 표시 |

## 시연 절차와 완료 기준

다음은 구현 후 저장소 루트에서 사용할 명령이다. 원본 CSV 위치는 `configs/data.toml`에, 트리 설정은 `configs/models/poc-tree.toml`에 둔다.

```bash
uv sync --locked
uv run python -m music_popularity prepare --config configs/data.toml --dataset spotify-poc
uv run python -m music_popularity train --dataset spotify-poc --config configs/models/poc-tree.toml --run poc-tree
uv run python -m music_popularity evaluate --run poc-tree
uv run python -m music_popularity predict --run poc-tree --input data/processed/spotify-poc/demo-track.json
```

- **실제 곡 시연** — 마지막 명령만 새 프로세스에서 실행해도 저장된 모델이 홀드아웃 곡의 0~100점 예측과 분기 설명을 함께 출력한다. 다른 곡은 `--input` 경로만 바꿔 넣는다.
- **설명의 일치** — 시연 곡에서 루트 평균과 분기별 변화량의 합이 반올림 전 모델 예측과 수치 오차 범위에서 일치하는지 확인한다.
- **평가 기록** — 학습·홀드아웃 간 트랙 ID 중복이 없음을 확인하고 두 MAE를 기록한다. 이 PoC의 통과 기준은 실제 곡에서 예측과 설명이 끝까지 이어지는 것이며, 성능 비교 결과는 다음 모델의 출발점으로 남긴다.
