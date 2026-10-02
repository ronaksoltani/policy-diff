import argparse
from pathlib import Path

from .tracker import check_url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Save policy text locally and report changes.")
    parser.add_argument("url")
    parser.add_argument("--state-dir", type=Path, default=Path(".policy-state"))
    args = parser.parse_args(argv)
    try:
        result = check_url(args.url, args.state_dir)
    except Exception as error:
        parser.error(str(error))
    print(f"{result['status']}: {args.url}")
    if result.get("report"):
        print(f"HTML report: {result['report']}\nUnified diff: {result['diff']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
