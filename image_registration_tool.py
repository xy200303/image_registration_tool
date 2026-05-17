from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from image_registration_tool.cli import main


if __name__ == "__main__":
    args = sys.argv[1:] or ["gui"]
    raise SystemExit(main(args))
