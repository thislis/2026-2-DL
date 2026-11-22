# 후속 버전 실행 계획

다음은 모델 비교와 조언 카드 생성을 위한 설계안이다. 명령과 경로는 해당 기능을 구현할 때 적용한다. 현재 실행할 수 있는 명령은 PoC 가이드에 있다. [PoC 실행 가이드](../PoC/run-guide.md)

## 예정 디렉터리 구조

```text
2026-2-DL/
├── README.md
├── AGENTS.md                   # 기여 지침
├── docs/                       # 프로젝트 개요, 작업 기록 등의 문서들
├── pyproject.toml              # Python 버전, 패키지, 의존성, 개발 도구
├── uv.lock                     # 실험에 사용한 의존성 버전
├── configs/
│   ├── data.toml               # 원본 경로, 데이터 버전, 입력 열, 분할 시드
│   ├── models/                 # 모델·장르 표현별 설정 (예: rf.toml)
│   └── cases/                  # 사례 트랙 ID, 고정 속성, 허용 변화량, 후보 장르
├── data/
│   ├── raw/                    # 다운로드한 원본 CSV
│   └── processed/<dataset-id>/ # 정제 데이터, 열 사전, 트랙별 분할·폴드 목록
├── src/music_popularity/
│   ├── __init__.py
│   ├── __main__.py             # 명령과 인자를 읽고 해당 단계를 호출
│   ├── prepare.py              # 스키마 확인, 정제, 분할
│   ├── models/                 # 선형 회귀, RF, LightGBM, 두 Transformer
│   ├── train.py                # 전처리 학습, 교차검증, 최종 모델 저장
│   ├── evaluate.py             # 홀드아웃 예측과 오차 집계
│   ├── explain.py              # 곡별 기여도와 전체·장르별 중요도
│   └── prescribe.py            # 제약 최적화와 조언 카드 출력
├── tests/                      # 예: test_prepare.py, test_prescribe.py
└── runs/<run-id>/              # 실험 한 건의 설정, 모델, 지표, 설명, 카드
```

## 실험 실행 예시

Python 3.11과 `uv`를 사용한다. 작업 디렉터리는 저장소 루트이며, 패키지를 `src/`에서 설치하도록 `pyproject.toml`에 설정한다. 모델이나 사례를 바꿀 때는 해당 TOML 파일을 선택한다. 다음은 랜덤 포레스트 실험 한 건의 실행 예시다.

```bash
# 환경 준비. 첫 구현에서 생성해 커밋한 uv.lock을 사용한다.
uv sync --locked

# Kaggle의 Ultimate Spotify Tracks DB 원본을 data/raw/SpotifyFeatures.csv에 둔다.
uv run python -m music_popularity prepare --config configs/data.toml --dataset spotify-v1

# 같은 데이터 분할로 모델을 학습하고 실행 이름을 지정한다.
uv run python -m music_popularity train --dataset spotify-v1 --config configs/models/rf.toml --run rf-seed42

# 저장된 모델과 전처리기로 평가·설명·조언 카드 생성을 이어간다.
uv run python -m music_popularity evaluate --run rf-seed42
uv run python -m music_popularity explain --run rf-seed42
uv run python -m music_popularity prescribe --run rf-seed42 --case configs/cases/track-01.toml
```

## 전체 프로젝트의 단계별 입출력과 비교 기준

| 단계 | 결과와 사용 방법 |
|---|---|
| `prepare` | 실제 CSV 헤더에서 입력·식별 열과 목표값을 확정한다. 트랙 ID 단위로 학습 80%와 홀드아웃 20%를 나누고, 학습용 10개 폴드의 배정을 함께 저장한다. 데이터 버전이나 분할 규칙이 바뀌면 새 데이터셋 ID를 쓴다. |
| `train` | 동일 데이터셋 ID를 지정해 모델 간 비교에 같은 표본을 쓴다. 각 폴드의 학습 부분에서 전처리를 맞추고 설정을 고른 뒤, 전체 학습 표본으로 다시 학습한다. 모델·전처리기와 사용한 설정, 시드, 데이터셋 ID를 새 실행 폴더에 보관한다. |
| `evaluate` | 해당 실행의 홀드아웃 예측을 `predictions.csv`에, 전체 RMSE·MAE·R²를 `metrics.json`에, 장르별 표본 수와 오차를 `metrics-by-genre.csv`에 쓴다. |
| `explain` | `explanations/`에 곡별 속성 기여도와 전체·장르별 중요도 표를 저장한다. 모델 간 설명 비교에는 같은 곡을 사용한다. |
| `prescribe` | 사례 설정에 지정된 속성을 고정하고 변경 가능한 속성만 탐색한다. `cards/<case-id>.md`에 장르 유지·전환 후보의 변경값과 원곡 대비 예측 점수 차이를 기록한다. |

평가·설명·카드 경로는 모두 `runs/<run-id>/` 기준이다. 예를 들어 RF와 FT-Transformer를 비교할 때는 `spotify-v1`을 공유하고 서로 다른 모델 설정과 실행 이름을 사용한다. 변경한 기능은 해당 테스트부터 확인한다. 예를 들어 분할 로직을 수정한 뒤에는 `uv run pytest tests/test_prepare.py`로 같은 트랙이 여러 분할에 섞이는지 검사한다.
