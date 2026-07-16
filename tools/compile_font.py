"""
Compiles the final Ikshu-Regular.ufo (produced by build_ufo.py) into a .ttf via
fontmake, then copies the result into tools/ where compile_test_page.py expects it.

    wsl python3 compile_font.py
"""
import shutil
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UFO_PATH = os.path.join(ROOT, "Ikshu-Regular.ufo")
MASTER_TTF = os.path.join(ROOT, "master_ttf", "Ikshu-Regular.ttf")
TOOLS_TTF = os.path.join(HERE, "Ikshu-Regular.ttf")

if __name__ == "__main__":
    if not os.path.isdir(UFO_PATH):
        raise SystemExit(f"No UFO found at {UFO_PATH} - run build_ufo.py first.")

    result = subprocess.run(
        [sys.executable, "-m", "fontmake", "-u", "Ikshu-Regular.ufo", "-o", "ttf", "--keep-overlaps"],
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise SystemExit(f"fontmake failed (exit {result.returncode}).")

    if not os.path.isfile(MASTER_TTF):
        raise SystemExit(f"fontmake reported success but {MASTER_TTF} wasn't produced.")

    shutil.copy2(MASTER_TTF, TOOLS_TTF)
    print()
    print("Compiled:", MASTER_TTF)
    print("Copied to:", TOOLS_TTF)
    print("Next: wsl python3 build_test_page_data.py && wsl python3 build_sample_texts.py && wsl python3 compile_test_page.py")
