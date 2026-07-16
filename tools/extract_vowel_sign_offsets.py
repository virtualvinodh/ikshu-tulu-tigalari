"""
Extracts every component placement found in the existing vowel-sign ligatures
(U/UU/Vocalic-R/RR/L/LL forms attached to a specific consonant) - dx/dy offsets,
full transform, and both glyphs' own bounds - purely as a reference dataset.

Unlike the conjunct (consonant+consonant.below) case, this family showed a real
discoverable pattern earlier: components like lVocalicMatra-tutg/rVocalicMatra-tutg
tend to attach at the host consonant's own right ink edge. This dataset lets that
be checked/reused precisely instead of re-deriving it, and also surfaces where the
pattern does NOT hold (varying stylistic-variant choice per consonant, etc).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "glyph_svg_data.json"), encoding="utf-8") as f:
    data = json.load(f)
with open(os.path.join(HERE, "glyph_classification.json"), encoding="utf-8") as f:
    classification = json.load(f)

records = []
for name in classification.get("vowel_sign_ligature", []):
    g = data.get(name)
    if not g or not g.get("components"):
        continue
    host_bounds = None
    for c in g["components"]:
        base_g = data.get(c["baseGlyph"])
        entry = {
            "parentGlyph": name,
            "parentBounds": g["bounds"],
            "component": c["baseGlyph"],
            "transform": {k: c[k] for k in ("dx", "dy", "xx", "xy", "yx", "yy")},
            "componentOwnBounds": base_g["bounds"] if base_g else None,
            "siblingComponents": [oc["baseGlyph"] for oc in g["components"] if oc is not c],
        }
        # if this component IS (or resolves toward) the plain consonant, record its
        # own right edge for quick comparison against sibling offsets
        if base_g and base_g["bounds"]:
            entry["componentRightEdge"] = base_g["bounds"][2]
        records.append(entry)

out_path = os.path.join(HERE, "vowel_sign_ligature_offsets.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

n_glyphs = len({r["parentGlyph"] for r in records})
print(f"Found {len(records)} component placements across {n_glyphs} vowel-sign ligatures "
      f"(of {len(classification.get('vowel_sign_ligature', []))} total in that category).")
print("Written to:", out_path)
