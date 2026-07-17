"""
Classifies every below-base consonant form (the ".below" glyphs `blwf`'s generic
fallback substitutes in - see generate_blwf_feature.py) as a GDEF Mark, and gives
each one a `_bottom` anchor so it actually snaps into place under the preceding
consonant instead of just sitting at normal advance-width position.

Why this is needed: `blwf`'s rule is a plain ligature substitution (conjoiner +
consonant -> consonant.below) - that swaps in the below-base glyph, but doesn't
position it. Without a `_bottom` anchor pairing to the preceding base's own
`bottom` anchor (added by generate_anchors.py), HarfBuzz has no attachment point
to snap it to, so it just renders inline instead of stacking under the previous
consonant like every other mark on this font already does.

Target set: every glyph in glyph_classification.json's "consonant_below_base"
category (61 glyphs - includes the ".alt1"/".alt2" stylistic variants, which need
the same treatment in case they're ever selected via a stylistic-alternate
feature), EXCEPT ya-tutg.below (excluded per project owner - it's a ligature-only
construction piece, not meant to independently attach as a generic fallback
target).

Anchor placement mirrors generate_anchors.py's own mark_pass(MARKS_BOTTOM, "_bottom",
x_from="center", y_edge="max") exactly: x = the glyph's own bbox center, y = the
glyph's own bbox TOP edge (yMax), no gap - so the attachment point sits precisely
at the top of the below-form's own shape, and the shape hangs downward from there,
the same "Lego block" fit every other _bottom-anchored mark on this font already
uses (verified against anudatta-tutg/germinationmark-tutg/etc. before writing this).

Re-runnable: anchor upsert and lib-key set are both idempotent, same as
generate_anchors.py.
"""
import ufoLib2
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")

EXCLUDE = {"ya-tutg.below"}

font = ufoLib2.Font.open(UFO_PATH)
with open(os.path.join(HERE, "glyph_classification.json"), encoding="utf-8") as f:
    d = json.load(f)

targets = [n for n in d["consonant_below_base"] if n not in EXCLUDE]


def find_anchor(glyph, name):
    return next((a for a in glyph.anchors if a.name == name), None)


def upsert_anchor(glyphname, name, x, y):
    g = font[glyphname]
    existing = find_anchor(g, name)
    if existing is not None:
        existing.x, existing.y = round(x, 1), round(y, 1)
        return "updated"
    g.appendAnchor(dict(x=round(x, 1), y=round(y, 1), name=name))
    return "added"


report = {"classified": 0, "already_classified": 0, "anchor_added": 0, "anchor_updated": 0, "no_bounds": []}

for gname in targets:
    g = font[gname]

    if g.lib.get("public.openTypeCategory") == "mark":
        report["already_classified"] += 1
    else:
        g.lib["public.openTypeCategory"] = "mark"
        report["classified"] += 1

    b = g.getBounds(font)
    if b is None:
        report["no_bounds"].append(gname)
        continue
    x = (b.xMin + b.xMax) / 2
    y = b.yMax
    result = upsert_anchor(gname, "_bottom", x, y)
    report["anchor_" + result] += 1

font.save(UFO_PATH, overwrite=True)

print(f"Target glyphs (consonant_below_base minus {sorted(EXCLUDE)}): {len(targets)}")
print("Newly classified as mark:", report["classified"])
print("Already classified as mark:", report["already_classified"])
print("_bottom anchor added:", report["anchor_added"])
print("_bottom anchor updated:", report["anchor_updated"])
print("No bounds / empty glyphs (flag for review):", len(report["no_bounds"]))
for gname in report["no_bounds"]:
    print("  ", gname)
