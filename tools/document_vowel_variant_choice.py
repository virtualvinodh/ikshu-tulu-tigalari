"""
For every consonant + {U, UU, Vocalic-R, Vocalic-RR} vowel-sign ligature, documents
which specific shape-variant component was actually used to draw the vowel-sign part
(these shapes vary per host consonant by design choice - see Figure 38 in the
proposal - not by a derivable geometric rule, so this is captured as reference data
rather than a formula).
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "glyph_svg_data.json"), encoding="utf-8") as f:
    data = json.load(f)
with open(os.path.join(HERE, "glyph_classification.json"), encoding="utf-8") as f:
    classification = json.load(f)

VOWEL_KIND_PATTERNS = {
    "uu": re.compile(r"uu.?matra", re.I),
    "rr": re.compile(r"rr.?vocalic", re.I),
    "u": re.compile(r"(?<!u)u.?matra", re.I),   # avoid double-matching "uu" as "u"
    "r": re.compile(r"(?<!r)r.?vocalic", re.I),
}


def classify_vowel_kind(name):
    if VOWEL_KIND_PATTERNS["uu"].search(name):
        return "uu"
    if VOWEL_KIND_PATTERNS["rr"].search(name):
        return "rr"
    if VOWEL_KIND_PATTERNS["u"].search(name):
        return "u"
    if VOWEL_KIND_PATTERNS["r"].search(name):
        return "r"
    return None


def parse_ligature_name(name):
    m = re.match(r"^(.*?)_(uMatra|uuMatra|rVocalicMatra|rrVocalicMatra)-tutg(.*)$", name)
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3)  # consonant, vowelsign-token, suffix (e.g. '.alt1')


records = []
for name in classification.get("vowel_sign_ligature", []):
    parsed = parse_ligature_name(name)
    if not parsed:
        continue
    consonant, vowel_token, suffix = parsed
    g = data[name]
    variant_components = []
    for c in g.get("components", []):
        kind = classify_vowel_kind(c["baseGlyph"])
        if kind:
            variant_components.append({"name": c["baseGlyph"], "kind": kind})
    # also walk one level into any variant component that is itself a ligature
    # (e.g. the RR form often re-uses the R-form ligature glyph as a component)
    expanded = list(variant_components)
    for vc in variant_components:
        sub_g = data.get(vc["name"])
        if sub_g:
            for sc in sub_g.get("components", []):
                skind = classify_vowel_kind(sc["baseGlyph"])
                if skind:
                    expanded.append({"name": sc["baseGlyph"], "kind": skind, "viaComponent": vc["name"]})
    has_own_ink = bool(g.get("d"))
    is_hand_drawn = len(g.get("components", [])) == 0
    if expanded:
        vowel_shape_status = "reused-named-variant"
    elif is_hand_drawn:
        vowel_shape_status = "fully-hand-drawn"
    elif has_own_ink:
        vowel_shape_status = "bespoke-shape-only-consonant-componentized"
    else:
        vowel_shape_status = "empty-or-unexpected"
    records.append({
        "glyph": name,
        "consonant": consonant,
        "vowelSign": vowel_token,
        "variant": suffix if suffix else "(default)",
        "vowelShapeStatus": vowel_shape_status,
        "shapeComponentsUsed": expanded,
        "allComponents": [c["baseGlyph"] for c in g.get("components", [])],
        "isHandDrawn": is_hand_drawn,
    })

out_path = os.path.join(HERE, "vowel_sign_variant_choices.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

# quick summary: which shape variant name is used per (vowelSign) across consonants
by_vowel = {}
for r in records:
    names = [c["name"] for c in r["shapeComponentsUsed"]] or [f"<{r['vowelShapeStatus']}>"]
    by_vowel.setdefault(r["vowelSign"], {}).setdefault(tuple(sorted(set(names))), []).append(r["consonant"] + r["variant"])

print(f"Documented {len(records)} consonant+U/UU/VocR/VocRR ligatures.")
print("Written to:", out_path)
print()
for vowel, groups in by_vowel.items():
    print(f"--- {vowel} : {len(groups)} distinct shape-variant groupings ---")
    for shapes, consonants in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"  {shapes}: {len(consonants)} consonants -> {consonants[:6]}{'...' if len(consonants)>6 else ''}")
