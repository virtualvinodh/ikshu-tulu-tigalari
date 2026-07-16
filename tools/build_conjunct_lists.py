"""
Builds conjunct_lists.json for the "Standard Conjunct List" tab: satisarsharada's
own actual conjunct corpus (conjuncts_Sharada_*.json - real attested Sanskrit
consonant clusters), transliterated into Tigalari via brahmic_translit.py, instead
of a list derived from our own limited akhn GSUB coverage. That corpus is real
linguistic data (which clusters actually occur in Sanskrit) - our own 452 akhn
rules only tell us what happens to have a drawn ligature, a much smaller and
differently-shaped set.

satisarsharada's 13 files (conjuncts_Sharada_a/aa/i/ii/u/uu/r/e/o/au/am/ah/vir.json)
turn out to be the *same* underlying consonant-cluster skeleton repeated 13 times,
each with a different single trailing vowel-sign/mark character baked on (verified
directly: conjuncts_Sharada_aa.json's every entry is conjuncts_Sharada_a.json's
matching entry + one AA-matra character; _vir.json is + one virama; _am.json is +
one anusvara; and so on). So instead of shipping 13 near-duplicate transliterated
copies, this transliterates only the "a" file's bare skeleton once, and the test
page applies the trailing vowel-sign/mark client-side (same mechanism as the
Conjunct Matrix's dropdown+marks selectors) - one dataset, any combination.

Sharada's own updateConj() only ever displays conjuncts2S1 through conjuncts5S1 -
conjuncts1S1 turns out not to be conjuncts at all (a leading independent-vowel
letter followed by a single consonant+virama, some other kind of proofing row) and
is never rendered by their page, so it's skipped here too. conjuncts2S1 (2-consonant
pairs) is also skipped - the Conjunct Matrix tab already covers every 2-consonant
combination exhaustively, so repeating it here would just be noise.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brahmic_translit import transliterate, UnmappedCharacter

HERE = os.path.dirname(os.path.abspath(__file__))
CONJUNCTS_DIR = r"/mnt/c/Users/vinod/Projects/satisarsharada/conjuncts"
GROUP_NS = [3, 4, 5]


def load_conj_json(suffix):
    path = os.path.join(CONJUNCTS_DIR, f"conjuncts_Sharada_{suffix}.json")
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    raw = re.sub(r'^\s*var\s+\w+\s*=\s*', '', raw.strip())
    raw = raw.rstrip(';\n \t')
    return json.loads(raw)


# --- base skeleton: bare consonant clusters (the "a" file - inherent vowel,
# nothing appended), transliterated once ---
data = load_conj_json("a")
counts = []
total_items = 0
total_unmapped = 0
for n in GROUP_NS:
    entries = data.get(f"conjuncts{n}S1", [])
    items = []
    unmapped = 0
    for entry in entries:
        try:
            tigalari_cps = [ord(c) for c in transliterate(entry, "sharada", "tigalari")]
            items.append({"tigalariCps": tigalari_cps})
        except UnmappedCharacter:
            unmapped += 1
    counts.append({"n": n, "items": items})
    total_items += len(items)
    total_unmapped += unmapped
    print(f"n={n}: {len(items)} items, {unmapped} unmapped")

# --- selectable vowel-sign/ending and overlay-mark options: reuse the *exact
# same* tables already built for the Conjunct Matrix in test_page_data.json,
# rather than independently re-deriving an equivalent set - guarantees both
# dropdowns stay identical by construction instead of by two constructions
# happening to agree. build_test_page_data.py always runs before this script
# (see build_test_page.py's STEPS list). ---
with open(os.path.join(HERE, "test_page_data.json"), encoding="utf-8") as f:
    test_page_data = json.load(f)
vowel_sign_options = test_page_data["conjunctMatrix"]["vowelSignOptions"]
mark_options = test_page_data["matrix"]["markOptions"]

out = {
    "counts": counts,
    "vowelSignOptions": vowel_sign_options,
    "markOptions": mark_options,
}
out_path = os.path.join(HERE, "conjunct_lists.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)

print()
print("Total items:", total_items, " Total unmapped (skipped):", total_unmapped)
print("Written to:", out_path)
