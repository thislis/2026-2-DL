# 2026-2-DL · Spotify 트랙 인기 예측과 설명

곡의 오디오 속성과 장르로 Spotify 인기 지수(0~100점)를 예측하고, 장르별로 예측 근거를 설명한다. 최종 산출물은 아티스트가 유지하고 싶은 속성을 고정한 채 편곡 후보와 예상 점수 변화를 비교하는 **곡별 조언 카드**다. [프로젝트 개요](docs/project-overview.md) · [제안서 PDF](docs/prepare/proposal_music_popularity_xai-1.pdf)

## 저장소 구조

| 경로 | 용도 |
|---|---|
| `src/music_popularity/` | 음악 인기 예측 패키지 |
| `configs/` | 데이터와 모델의 실험 설정 |
| `tests/` | 패키지 동작을 확인하는 테스트 |
| `pyproject.toml`, `uv.lock` | 패키지 정의와 의존성 버전 |
| `data/raw/`, `data/processed/<dataset-id>/` | 원본 데이터와 데이터셋별 전처리 결과 |
| `runs/<run-id>/` | 실험별 모델과 평가 결과 |
| `docs/<버전>/` | 해당 버전의 구현 계획, 실행 가이드, 모델 설명 |

코드·설정·잠금 파일은 Git으로 관리한다. 원본 및 가공 데이터, 실험 결과, 가상 환경은 로컬에 보관한다. 저장소 작업 규칙과 변경 내역은 [기여 지침](AGENTS.md)과 [작업 기록](docs/history.md)에서 확인할 수 있다.

## 버전별 문서

| 버전 | 문서 |
|---|---|
| PoC | [실행 가이드](docs/PoC/run-guide.md) · [구현 계획과 모델 구조](docs/PoC/implementation-plan.md) |
| 후속 버전 | [실행 및 산출물 계획](docs/next-version/execution-plan.md) |
