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

Paragraph breaks (added 2026-07-18): "text" may contain blank-line-separated
paragraphs (a literal "\\n\\n" between them, e.g. from pasting a passage that
has real paragraph structure - see the "Mahamaya" entry). Single newlines
within a paragraph are treated as ordinary whitespace and collapsed. Each
paragraph break is recorded as a {"paragraphBreak": true} sentinel in the
"words" array (not a real word - no cps/transliteration), so the test page's
renderer can start a new paragraph there instead of flowing the whole passage
into one run of text. Entries without any blank lines are unaffected - they
just produce a single paragraph, same as before this change.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brahmic_translit import transliterate, UnmappedCharacter

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "sample_texts_source.json"), encoding="utf-8") as f:
    source = json.load(f)

out = {"passages": []}
for passage in source["passages"]:
    script = passage["sourceScript"]
    paragraphs = re.split(r"\n\s*\n", passage["text"])
    word_entries = []
    unmapped_words = 0
    for p_index, paragraph in enumerate(paragraphs):
        if p_index > 0:
            word_entries.append({"paragraphBreak": True})
        for w in paragraph.split():
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
    real_word_count = sum(1 for w in word_entries if "paragraphBreak" not in w)
    out["passages"].append({
        "id": passage["id"], "label": passage["label"], "words": word_entries,
        "wordCount": real_word_count, "unmappedCount": unmapped_words,
    })
    print(f"{passage['id']} ({script}): {real_word_count} words, {unmapped_words} unmapped, "
          f"{len(paragraphs)} paragraph(s)")

out_path = os.path.join(HERE, "sample_texts.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)
print("Written to:", out_path)
