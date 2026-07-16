"""
Exports brahmic_translit.py's SCRIPTS/BLOCK_RANGES/DIGIT_BASES tables to JSON, so
the test page's Live Input tab can run the same Kannada/Devanagari/Tigalari <->
Tigalari transliteration in the browser (for live typing) without hand-copying
~150 codepoints into JavaScript and risking the two copies drifting apart. Only
the *tables* are exported - the parsing/rendering control flow is still ported to
JS by hand in glyph_test_page_template.html, mirroring text_to_phonemes() /
phonemes_to_script() exactly (that logic is short and easy to keep in sync;
codepoint tables are not).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brahmic_translit import (
    SCRIPTS, BLOCK_RANGES, DIGIT_BASES,
    IAST_INDEPENDENT_VOWELS, IAST_VOWEL_SIGNS, IAST_CONSONANTS, IAST_SIGNS,
)

HERE = os.path.dirname(os.path.abspath(__file__))

out = {
    "scripts": SCRIPTS,
    "blockRanges": BLOCK_RANGES,
    "digitBases": DIGIT_BASES,
    "iast": {
        "independentVowels": IAST_INDEPENDENT_VOWELS,
        "vowelSigns": IAST_VOWEL_SIGNS,
        "consonants": IAST_CONSONANTS,
        "signs": IAST_SIGNS,
    },
}

out_path = os.path.join(HERE, "brahmic_tables.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)
print("Written to:", out_path)
