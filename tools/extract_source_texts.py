"""
One-time migration: pulls the 7 real Sanskrit sample-text passages out of
satisarsharada's testing.html (each written in Sharada script there) and writes
them into sample_texts_source.json - {id, label, sourceScript, text} per passage.

After this runs once, sample_texts_source.json is the actual source of truth for
sample texts; satisarsharada isn't touched again. New entries (including text
that's *already* Tigalari) get added directly to that JSON with the right
sourceScript - build_sample_texts.py transliterates or passes each through based on
that field.
"""
import json
import os
import re

SHARADA_HTML = r"/mnt/c/Users/vinod/Projects/satisarsharada/testing.html"
HERE = os.path.dirname(os.path.abspath(__file__))

PASSAGES = [
    ("Hridaya", "Prajnaparamita Hridaya (Heart Sutra)"),
    ("Ushnisha", "Ushnisha Vijaya Dharani"),
    ("Nilakantha", "Nilakantha Dharani (Great Compassion Mantra)"),
    ("Lotus", "Saddharmapundarika (Lotus Sutra), Samantamukha-parivarta"),
    ("Lalitavistara", "Lalitavistara excerpt"),
    ("Dhammachakka", "Dhammacakkappavattana Sutta"),
    ("Vedic", "Vedic passage"),
]


def extract_div(html, div_id):
    m = re.search(r'id="' + re.escape(div_id) + r'"[^>]*>(.*?)</div>', html, re.S)
    if not m:
        return None
    inner = m.group(1)
    inner = re.sub(r'<h1[^>]*>.*?</h1>', ' ', inner, flags=re.S)
    inner = re.sub(r'<br\s*/?>', ' ', inner)
    inner = re.sub(r'<[^>]+>', '', inner)
    inner = re.sub(r'\[.*?\]', ' ', inner)  # bracketed editorial notes, e.g. transliteration hints
    inner = re.sub(r'\s+', ' ', inner).strip()
    return inner


with open(SHARADA_HTML, encoding="utf-8") as f:
    html = f.read()

out = {"passages": []}
for div_id, label in PASSAGES:
    raw = extract_div(html, "Text-" + div_id)
    if raw is None:
        print("MISSING:", div_id)
        continue
    out["passages"].append({"id": div_id, "label": label, "sourceScript": "sharada", "text": raw})
    print(f"{div_id}: {len(raw.split())} words")

out_path = os.path.join(HERE, "sample_texts_source.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("Written to:", out_path)
