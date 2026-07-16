"""
Builds sample_texts.json for the Ikshu-Regular test page from sample_texts_source.json
- a plain {id, label, sourceScript, text} list. Per passage, based on sourceScript:

  - "sharada" / "devanagari" / "kannada": transliterate word-by-word (via
    brahmic_translit.py) into Tigalari (main text) plus Kannada and IAST (ruby
    annotation options).
  - "tigalari": already Tulu-Tigalari text - used as the main text unchanged (no
    round-trip through the phoneme stream), with Kannada/IAST annotations derived
    from it the same way.

To add a new sample text: add an entry to sample_texts_source.json with whichever
sourceScript it's actually written in - no other script needs to change.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brahmic_translit import transliterate, UnmappedCharacter

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "sample_texts_source.json"), encoding="utf-8") as f:
    source = json.load(f)

out = {"passages": []}
for passage in source["passages"]:
    script = passage["sourceScript"]
    words = passage["text"].split(" ")
    word_entries = []
    unmapped_words = 0
    for w in words:
        if not w:
            continue
        try:
            tigalari_cps = [ord(c) for c in transliterate(w, script, "tigalari")]
            kannada_cps = [ord(c) for c in transliterate(w, script, "kannada")]
            iast_cps = [ord(c) for c in transliterate(w, script, "iast")]
            word_entries.append({"tigalariCps": tigalari_cps, "kannadaCps": kannada_cps, "iastCps": iast_cps})
        except UnmappedCharacter as e:
            unmapped_words += 1
            word_entries.append({"tigalariCps": None, "kannadaCps": None, "iastCps": None, "error": str(e), "word": w})
    out["passages"].append({
        "id": passage["id"], "label": passage["label"], "words": word_entries,
        "wordCount": len(word_entries), "unmappedCount": unmapped_words,
    })
    print(f"{passage['id']} ({script}): {len(word_entries)} words, {unmapped_words} unmapped")

out_path = os.path.join(HERE, "sample_texts.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)
print("Written to:", out_path)
