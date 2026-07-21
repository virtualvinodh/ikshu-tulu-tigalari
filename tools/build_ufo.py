"""
Pipeline: turns a fresh/raw Ikshu-Regular.ufo into the final, feature-complete UFO
ready for compile_font.py, by running every fix/generator script in the one order
that actually works, instead of remembering and re-running them by hand.

    wsl python3 build_ufo.py

Backs up Ikshu-Regular.ufo (timestamped copy, same convention used throughout this
project's history) before touching anything, then runs, in order:

  1. classify_glyphs.py       - glyph_classification.json (read-only on the UFO;
                                 generate_anchors.py, generate_variant_registry.py,
                                 and generate_akhn_feature.py all depend on this file)
  2. fix_guillemet_duplicate_cmap.py  - cmap fix (idempotent)
  3. fix_unicode_mappings.py          - cmap fix (idempotent)
  4. generate_anchors.py      - GPOS anchors (idempotent/upsert-based)
  5. classify_blwf_marks.py   - classifies every ".below" glyph (blwf's fallback
                                 output, except ya-tutg.below) as GDEF Mark and gives
                                 it a _bottom anchor, so it actually snaps under the
                                 preceding consonant instead of sitting at normal
                                 advance-width position (idempotent/upsert-based,
                                 same pattern as generate_anchors.py)
  6. export_svg_data.py       - glyph_svg_data.json (read-only on the UFO; every
                                 ".altN" glyph the font currently has is what
                                 generate_variant_registry.py scans next - added
                                 2026-07-21, previously only ever run manually as
                                 part of build_test_page.py, which meant a fresh
                                 build_ufo.py run silently used whatever stale
                                 variant_registry.json/glyph_svg_data.json happened
                                 to already be on disk instead of the font's real
                                 current glyph inventory)
  7. generate_variant_registry.py  - variant_registry.json, from every ".altN"
                                 glyph currently in the font (added 2026-07-21;
                                 must run before generate_akhn_feature.py, which
                                 reads this file for TutgVariantSelect/
                                 TutgConjunctVariantSelect and the
                                 names_override.json-driven ligature_alt_overrides/
                                 single_glyph_alt_overrides)
  8. generate_akhn_feature.py - tutg_akhn.fea + tutg_blws.fea + tutg_akhn_rules.json
                                 (regenerated fresh every run; not a UFO write).
                                 Vowel-sign ligature formation (consonant + its own
                                 vowel sign) lives in tutg_blws.fea/`feature blws`,
                                 split out 2026-07-21 - empirically confirmed (via
                                 uharfbuzz on a throwaway test font) that blws runs
                                 BEFORE blwf for this script/HarfBuzz combination.
  9. merge_akhn_feature.py    - merges tutg_akhn.fea into features.fea (has its own
                                 idempotency guard - skips if already merged, so
                                 this pipeline is safe to run on its own output too)
  10. merge_blws_feature.py   - merges tutg_blws.fea into features.fea, right after
                                 the akhn block (own idempotency guard; must run
                                 after merge_akhn_feature.py)
  11. generate_blwf_feature.py - tutg_blwf.fea + tutg_pstf.fea + BLWF_TODO.md
                                 (regenerated fresh every run; not a UFO write). YA/RA's
                                 own post-base combining forms (ya-tutg.below,
                                 raMatra-tutg/"the Rakar form") live in tutg_pstf.fea/
                                 `feature pstf` instead of blwf's generic below-base
                                 fallback, split out 2026-07-21 - they're genuinely
                                 different allographs, not below-base miniatures
                                 (BELOW_BASE_MINIATURE_GLYPHS.md).
  12. merge_blwf_feature.py    - merges tutg_blwf.fea into features.fea, right after
                                 the akhn block (own idempotency guard, same pattern
                                 as merge_akhn_feature.py - must run after it, see
                                 that script's docstring)
  13. merge_pstf_feature.py    - merges tutg_pstf.fea into features.fea, right after
                                 the blwf block (own idempotency guard; must run
                                 after merge_blwf_feature.py)
  14. remove_stub_numeral_features.py  - strips incomplete numr/dnom/frac (idempotent)

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
    "classify_blwf_marks.py",
    "export_svg_data.py",
    "generate_variant_registry.py",
    "generate_akhn_feature.py",
    "merge_akhn_feature.py",
    "merge_blws_feature.py",
    "generate_blwf_feature.py",
    "merge_blwf_feature.py",
    "merge_pstf_feature.py",
    "merge_rkrf_feature.py",
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
