"""
Extracts every real consonant+below-base component pairing found in the existing
conjunct ligatures (dx/dy offsets, full transform, and both glyphs' own bounds),
purely as a reference dataset. This is NOT a clean formula - see the 2026-07-16
conversation notes / GSUB_TODO.md: the same below-component attaches at different
offsets depending on host width and stacking depth, so these numbers are hand-tuned
per combination, not derivable from one rule. Kept here so future work (building the
Tier 2 generic fallback, or manually refining specific conjuncts) has the real
attested data to check against instead of re-deriving it from scratch each time.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "glyph_svg_data.json"), encoding="utf-8") as f:
    data = json.load(f)
with open(os.path.join(HERE, "glyph_classification.json"), encoding="utf-8") as f:
    classification = json.load(f)

records = []
for name in classification.get("conjunct_ligature", []):
    g = data.get(name)
    if not g:
        continue
    for c in g.get("components", []):
        base = c["baseGlyph"]
        if not (base.endswith("-tutg.below") or ".below." in base or base.endswith(".below")):
            continue
        below_g = data.get(base)
        # the "host" is whichever other component (or the glyph's own name prefix) precedes it;
        # record all sibling components too so the full stacking context is preserved
        siblings = [oc["baseGlyph"] for oc in g["components"] if oc is not c]
        records.append({
            "parentGlyph": name,
            "parentBounds": g["bounds"],
            "belowComponent": base,
            "transform": {k: c[k] for k in ("dx", "dy", "xx", "xy", "yx", "yy")},
            "belowComponentOwnBounds": below_g["bounds"] if below_g else None,
            "siblingComponents": siblings,
        })

out_path = os.path.join(HERE, "consonant_stacking_offsets.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"Found {len(records)} consonant+below-base component pairings across "
      f"{len(classification.get('conjunct_ligature', []))} conjunct ligatures.")
print("Written to:", out_path)
