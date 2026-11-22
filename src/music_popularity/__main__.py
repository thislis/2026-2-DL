import argparse
from pathlib import Path

from .evaluate import evaluate
from .explain import predict
from .prepare import prepare
from .train import train


def main():
    parser = argparse.ArgumentParser(description="Spotify 인기 예측 PoC")
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare", help="CSV 정제 및 트랙 단위 분할")
    prep.add_argument("--config", type=Path, required=True)
    prep.add_argument("--dataset", required=True)
    fit = commands.add_parser("train", help="회귀 트리 학습")
    fit.add_argument("--config", type=Path, required=True)
    fit.add_argument("--dataset", required=True)
    fit.add_argument("--run", required=True)
    check = commands.add_parser("evaluate", help="홀드아웃 MAE 평가")
    check.add_argument("--run", required=True)
    single = commands.add_parser("predict", help="곡 JSON 한 건의 예측과 설명")
    single.add_argument("--run", required=True)
    single.add_argument("--input", dest="input_path", type=Path, required=True)
    args = vars(parser.parse_args())
    handler = {"prepare": prepare, "train": train, "evaluate": evaluate, "predict": predict}
    try:
        handler[args.pop("command")](**args)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"오류: {exc}\n")


if __name__ == "__main__":
    main()
