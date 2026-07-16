"""
Pipeline: turns a fresh/raw Ikshu-Regular.ufo into the final, feature-complete UFO
ready for compile_font.py, by running every fix/generator script in the one order
that actually works, instead of remembering and re-running them by hand.

    wsl python3 build_ufo.py

Backs up Ikshu-Regular.ufo (timestamped copy, same convention used throughout this
project's history) before touching anything, then runs, in order:

  1. classify_glyphs.py       - glyph_classification.json (read-only on the UFO;
                                 generate_anchors.py and generate_akhn_feature.py
                                 both depend on this file)
  2. fix_guillemet_duplicate_cmap.py  - cmap fix (idempotent)
  3. fix_unicode_mappings.py          - cmap fix (idempotent)
  4. generate_anchors.py      - GPOS anchors (idempotent/upsert-based)
  5. generate_akhn_feature.py - tutg_akhn.fea + tutg_akhn_rules.json (regenerated
                                 fresh every run; not a UFO write)
  6. merge_features.py        - merges tutg_akhn.fea into features.fea (has its own
                                 idempotency guard - skips if already merged, so
                                 this pipeline is safe to run on its own output too)
  7. remove_stub_numeral_features.py  - strips incomplete numr/dnom/frac (idempotent)

Everything else in tools/ (extract_stacking_offsets.py, extract_vowel_sign_offsets.py,
document_vowel_variant_choice.py, generate_gsub_rules.py, _selfcheck_render.py) is
reference/historical material that nothing in this pipeline depends on - see
GSUB_TODO.md for what each one was for.
"""
import shutil
import subprocess
import sys
import time
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UFO_PATH = os.path.join(ROOT, "Ikshu-Regular.ufo")

STEPS = [
    "classify_glyphs.py",
    "fix_guillemet_duplicate_cmap.py",
    "fix_unicode_mappings.py",
    "generate_anchors.py",
    "generate_akhn_feature.py",
    "merge_features.py",
    "remove_stub_numeral_features.py",
]


def backup_ufo():
    if not os.path.isdir(UFO_PATH):
        raise SystemExit(f"No UFO found at {UFO_PATH}")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = UFO_PATH + f".backup-{stamp}"
    shutil.copytree(UFO_PATH, backup_path)
    print("Backed up UFO to:", backup_path)


def run_step(script_name):
    print()
    print("=" * 70)
    print("Running", script_name)
    print("=" * 70)
    result = subprocess.run([sys.executable, script_name], cwd=HERE)
    if result.returncode != 0:
        raise SystemExit(f"{script_name} failed (exit {result.returncode}) - stopping pipeline.")


if __name__ == "__main__":
    backup_ufo()
    for step in STEPS:
        run_step(step)
    print()
    print("=" * 70)
    print("build_ufo.py complete. UFO ready at:", UFO_PATH)
    print("Next: wsl python3 compile_font.py")
    print("=" * 70)
