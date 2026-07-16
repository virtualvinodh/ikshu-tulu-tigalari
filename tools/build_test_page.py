"""
Pipeline: rebuilds glyph_test_page.html from the current compiled font + UFO state,
by running every data-generation step in order, instead of remembering and
re-running them by hand.

    wsl python3 build_test_page.py

Requires tools/Ikshu-Regular.ttf to already exist (see compile_font.py) and
Ikshu-Regular.ufo to be in its final state (see build_ufo.py) - this script only
regenerates test-page data and HTML, it doesn't touch the UFO or font.

Runs, in order:

  1. export_svg_data.py       - glyph_svg_data.json (every glyph's outline/anchors/
                                 bounds; depends on glyph_classification.json, which
                                 build_ufo.py's classify_glyphs.py step produces)
  2. build_test_page_data.py  - test_page_data.json (consonants/vowels/akhn tests/
                                 mark tests/syllable matrix/conjunct matrix, as real
                                 Unicode code points)
  3. build_sample_texts.py    - sample_texts.json (transliterates every passage in
                                 sample_texts_source.json per its sourceScript)
  4. export_brahmic_tables.py - brahmic_tables.json (the same codepoint tables
                                 brahmic_translit.py uses, for the Live Input tab's
                                 in-browser Kannada/Devanagari -> Tigalari typing)
  5. build_conjunct_lists.py  - conjunct_lists.json (satisarsharada's own 13-file
                                 conjunct corpus, transliterated into Tigalari, for
                                 the Standard Conjunct List tab)
  6. compile_test_page.py     - embeds all of the above + the font into the final,
                                 self-contained glyph_test_page.html

To add a new sample text, edit sample_texts_source.json first (add an
{id, label, sourceScript, text} entry), then run this script - no other change
needed. See sample_texts_source.json's existing entries for the shape, and
brahmic_translit.py's docstring for which sourceScript values are supported
(devanagari / kannada / sharada / tigalari).
"""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    "export_svg_data.py",
    "build_test_page_data.py",
    "build_sample_texts.py",
    "export_brahmic_tables.py",
    "build_conjunct_lists.py",
    "compile_test_page.py",
]


def run_step(script_name):
    print()
    print("=" * 70)
    print("Running", script_name)
    print("=" * 70)
    result = subprocess.run([sys.executable, script_name], cwd=HERE)
    if result.returncode != 0:
        raise SystemExit(f"{script_name} failed (exit {result.returncode}) - stopping pipeline.")


if __name__ == "__main__":
    for step in STEPS:
        run_step(step)
    print()
    print("=" * 70)
    print("build_test_page.py complete: ../glyph_test_page.html")
    print("=" * 70)
