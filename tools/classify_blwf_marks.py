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
target) - PLUS every "*.below.auto" glyph (added 2026-07-17, see
generate_below_auto_glyphs.py), read directly off the font's own glyph list
since these postdate glyph_classification.json and classify_glyphs.py has no
naming rule that would ever put them in "consonant_below_base" itself - PLUS the
9 ligatures that already had a real hand-drawn ".below" before
generate_below_auto_glyphs.py ran (ga_uMatra-tutg, ha_ya-tutg, ja_uuMatra-tutg,
na_uMatra-tutg, na_ya-tutg, pa_ya-tutg, sha_ya-tutg, ssa_va-tutg, ta_uMatra-tutg -
added 2026-07-17, found the same way generate_blwf_feature.py finds them: default-
form conjunct_ligature/vowel_sign_ligature entries where "{name}.below" exists).
These already carried top/bottom/topright anchors (swept in by generate_anchors.py's
general ligature pass, which doesn't filter out ".below"-suffixed compound names),
but had no _bottom anchor or mark classification until now - same gap as the
.below.auto glyphs, just for pre-existing artwork instead of auto-generated.

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

# Auto-generated ligature below-base forms (generate_below_auto_glyphs.py) aren't
# in glyph_classification.json - it predates them and classify_glyphs.py has no
# naming rule for ".below.auto" - so they're picked up directly from the font's
# own glyph list and get the exact same treatment as consonant_below_base.
below_auto = [n for n in font.keys() if n.endswith(".below.auto")]


def is_default_form(name):
    return "-tutg" in name and "." not in name.partition("-tutg")[2]


# The 9 ligatures with a real pre-existing ".below" - same discovery logic
# generate_blwf_feature.py uses (default-form ligature candidates where
# "{name}.below" already exists as a real glyph).
ligature_candidates = set(d.get("conjunct_ligature", []) + d.get("vowel_sign_ligature", []))
ligature_below_real = [f"{n}.below" for n in ligature_candidates if is_default_form(n) and f"{n}.below" in font]

targets = [n for n in d["consonant_below_base"] + below_auto + ligature_below_real if n not in EXCLUDE]


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
