"""Entry point: `python -m relevantr` (GUI) or `python -m relevantr <cmd>` (CLI)."""

import logging
import sys


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    from dotenv import load_dotenv

    load_dotenv()

    from .cli import run_cli

    return run_cli(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
