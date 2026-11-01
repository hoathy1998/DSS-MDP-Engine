"""Put src/ on sys.path of the current environment, as a substitute for `pip install -e .`.

`pip install -e .` fails on Python < 3.13 when the project path has characters outside the
Windows locale encoding (here cp1252): .pth files are written and read in that encoding.
An `import` line in a .pth file can hold the path as pure ASCII escapes, which avoids this.
"""
from __future__ import annotations

import site
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
PTH_NAME = "dipmdp_dev.pth"


def pth_line(src: Path) -> str:
    return f"import sys; sys.path.insert(0, {ascii(str(src))})\n"


def main() -> None:
    target = Path(site.getsitepackages()[-1]) / PTH_NAME
    target.write_text(pth_line(SRC), encoding="ascii")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
