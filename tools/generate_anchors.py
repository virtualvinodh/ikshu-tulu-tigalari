"""
Generates GPOS mark-attachment anchors for the Tulu-Tigalari glyph set.

Anchors added (base name / mark name):
  top / _top           -> Repha, Vedic Svarita
  bottom / _bottom      -> Vedic Anudatta, Gemination mark, Vowel Sign Vocalic L, Vowel Sign Vocalic LL
  topright / _topright  -> Virama (USE "Bindu" override behavior)
  bottomright / _bottomright -> Vowel Sign U, Vowel Sign UU (fallback mark-attachment path,
                                 used only when a per-consonant ligature glyph doesn't exist)

Placement:
  top/bottom/topright anchors on base glyphs = glyph's own bbox edge +/- a per-anchor GAP
  (each independently tunable below), X = bbox center (top/bottom) or bbox xMax (topright).
  bottomright is different: it searches the glyph's actual outline (not just the bbox)
  for the point that is simultaneously furthest right and furthest down, so the fallback
  vowel sign visually touches the consonant's ink instead of floating off a bbox corner
  (no gap parameter - it's meant to touch).

Re-runnable: if an anchor of the target name already exists on a glyph, its x/y is
updated in place rather than skipped, so changing a GAP constant and re-running
retunes every affected glyph without needing to delete anything first.

BOTTOM_POP also includes every "*.below.auto" glyph (added 2026-07-17, see
generate_below_auto_glyphs.py) so they get a "bottom" anchor too, letting them
serve as the base for further stacking, matching consonant_below_base - read
directly off the font's own glyph list since these postdate
glyph_classification.json.
"""
import ufoLib2
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")

# Independently tunable Y buffers, in font units (~5% of a 1000 upm each by default).
TOP_GAP = 50          # Repha, Svarita float this far above the base's own top edge
BOTTOM_GAP = 50       # Anudatta, Gemination, Vocalic-L/LL sit this far below the base's own bottom edge
TOPRIGHT_GAP = 50     # Virama-as-Bindu floats this far above the base's own top edge, at its right edge

font = ufoLib2.Font.open(UFO_PATH)
with open(os.path.join(HERE, "glyph_classification.json"), encoding="utf-8") as f:
    d = json.load(f)

# Auto-generated ligature below-base forms (generate_below_auto_glyphs.py) aren't
# in glyph_classification.json - it predates them and classify_glyphs.py has no
# naming rule for ".below.auto" - so they're picked up directly from the font's
# own glyph list instead, same as consonant_below_base gets a "bottom" anchor
# below (a below-base form can itself be the base for further stacking).
BELOW_AUTO_POP = [n for n in font.keys() if n.endswith(".below.auto")]

# classify_glyphs.py classifies purely off the CORE name (before "-tutg"), so a
# ligature's ".below"/".below.auto" form (a below-base positioning variant, not a
# real standalone shaped output) lands in the exact same category
# (conjunct_ligature/vowel_sign_ligature) as its bare counterpart. That's fine for
# BOTTOM_POP (a below-form legitimately needs bottom/_bottom, e.g. to serve as the
# base for further stacking), but top/topright are for a glyph's own upper edge as
# a MAIN-LINE shaped output - a below-base form never sits there, so it must never
# get one. Filtered out here rather than in classify_glyphs.py, since the category
# itself (conjunct_ligature etc.) is still correct - only this script's top/topright
# pools need to exclude below-forms.
def _suffix_tags(name):
    _, _, suffix = name.partition("-tutg")
    return set(t for t in suffix.split(".") if t)


def _is_below_form(name):
    return "below" in _suffix_tags(name)


LIGATURE_BELOW_FORMS = [n for n in d["conjunct_ligature"] + d["vowel_sign_ligature"] if _is_below_form(n)]

TOP_POP = [n for n in d["consonant"] + d["conjunct_ligature"] + d["vowel_sign_ligature"] if not _is_below_form(n)]
BOTTOM_POP = d["consonant"] + d["consonant_below_base"] + d["conjunct_ligature"] + d["vowel_sign_ligature"] + BELOW_AUTO_POP

SPACING_VS_ROOTS = ("aaMatra-tutg", "iMatra-tutg", "iiMatra-tutg", "eeMatra-tutg",
                    "aiMatra-tutg", "ooMatra-tutg", "auMatra-tutg", "aulengthmark-tutg")
spacing_vs = [n for n in d["vowel_sign"] + d["special_mark"] if n in SPACING_VS_ROOTS]
TOPRIGHT_POP = [n for n in d["consonant"] + d["conjunct_ligature"] + d["vowel_sign_ligature"] + spacing_vs
                if not _is_below_form(n)]

# A below-base form can itself be the base a following U/UU vowel sign attaches
# to (same "ink-touching fallback" reasoning as a plain consonant), so it needs
# its own bottomright too - not just bottom/_bottom.
BOTTOMRIGHT_POP = d["consonant"] + d["consonant_below_base"] + LIGATURE_BELOW_FORMS + BELOW_AUTO_POP

MARKS_TOP = ["repha-tutg", "repha-tutg.alt1", "svarita-tutg"]
MARKS_BOTTOM = ["anudatta-tutg", "germinationmark-tutg", "lVocalicMatra-tutg", "llVocalicMatra-tutg"]
MARKS_TOPRIGHT = ["virama-tutg"]
MARKS_BOTTOMRIGHT = ["uMatra-tutg", "uuMatra-tutg"]


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


report = {"added": 0, "updated": 0, "no_bounds": []}


def base_pass(pop, anchor_name, gap, x_from="center", y_edge="max"):
    for gname in pop:
        g = font[gname]
        b = g.getBounds(font)
        if b is None:
            report["no_bounds"].append((gname, anchor_name))
            continue
        x = (b.xMin + b.xMax) / 2 if x_from == "center" else b.xMax
        y = b.yMax + gap if y_edge == "max" else b.yMin - gap
        report[upsert_anchor(gname, anchor_name, x, y)] += 1


def mark_pass(names, anchor_name, x_from="center", y_edge="min"):
    for gname in names:
        g = font[gname]
        b = g.getBounds(font)
        if b is None:
            report["no_bounds"].append((gname, anchor_name))
            continue
        x = (b.xMin + b.xMax) / 2 if x_from == "center" else (b.xMin if x_from == "left" else b.xMax)
        y = b.yMin if y_edge == "min" else b.yMax
        report[upsert_anchor(gname, anchor_name, x, y)] += 1


# --- ink-touching search for the U/UU fallback anchor ---
def flatten_cubic(p0, p1, p2, p3, steps=24):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = (mt**3) * p0[0] + 3 * (mt**2) * t * p1[0] + 3 * mt * (t**2) * p2[0] + (t**3) * p3[0]
        y = (mt**3) * p0[1] + 3 * (mt**2) * t * p1[1] + 3 * mt * (t**2) * p2[1] + (t**3) * p3[1]
        pts.append((x, y))
    return pts


def outline_points(glyph, font=None, _depth=0):
    """Flatten all contours (cubic 'curve' and straight 'line' segments) into a dense point list.
    Resolves components recursively (glyphs built purely from components have no direct contours)."""
    pts = []
    if font is not None and _depth < 5:
        for comp in glyph.components:
            base = font.get(comp.baseGlyph)
            if base is None:
                continue
            sub_pts = outline_points(base, font, _depth + 1)
            dx, dy = comp.transformation.dx, comp.transformation.dy
            xx, xy, yx, yy = (comp.transformation.xx, comp.transformation.xy,
                               comp.transformation.yx, comp.transformation.yy)
            for (x, y) in sub_pts:
                pts.append((xx * x + yx * y + dx, xy * x + yy * y + dy))
    for contour in glyph.contours:
        points = contour.points
        n = len(points)
        # find on-curve indices to walk segment by segment
        i = 0
        # rotate so we start on an on-curve point
        start = next((k for k, p in enumerate(points) if p.type is not None), 0)
        ordered = points[start:] + points[:start]
        cur = (ordered[0].x, ordered[0].y)
        pts.append(cur)
        idx = 1
        pending_offcurve = []
        while idx <= n:
            p = ordered[idx % n]
            if p.type is None:
                pending_offcurve.append((p.x, p.y))
            else:
                end = (p.x, p.y)
                if len(pending_offcurve) == 2:
                    pts.extend(flatten_cubic(cur, pending_offcurve[0], pending_offcurve[1], end)[1:])
                elif len(pending_offcurve) == 0:
                    pts.append(end)
                else:
                    # quadratic or irregular offcurve count - just take the on-curve end
                    pts.append(end)
                cur = end
                pending_offcurve = []
                if idx >= n:
                    break
            idx += 1
    return pts


def find_ink_bottom_right(glyph, font):
    b = glyph.getBounds(font)
    if b is None:
        return None
    pts = outline_points(glyph, font)
    if not pts:
        return None
    w = b.xMax - b.xMin or 1
    h = b.yMax - b.yMin or 1
    best = None
    best_score = -1
    for (x, y) in pts:
        xn = (x - b.xMin) / w
        yn = (y - b.yMin) / h
        score = xn + (1 - yn)  # far right + far down, normalized
        if score > best_score:
            best_score = score
            best = (x, y)
    return best


# --- run all passes ---
base_pass(TOP_POP, "top", TOP_GAP, x_from="center", y_edge="max")
base_pass(BOTTOM_POP, "bottom", BOTTOM_GAP, x_from="center", y_edge="min")
base_pass(TOPRIGHT_POP, "topright", TOPRIGHT_GAP, x_from="edge", y_edge="max")

for gname in BOTTOMRIGHT_POP:
    g = font[gname]
    pt = find_ink_bottom_right(g, font)
    if pt is None:
        report["no_bounds"].append((gname, "bottomright"))
        continue
    report[upsert_anchor(gname, "bottomright", pt[0], pt[1])] += 1

mark_pass(MARKS_TOP, "_top", x_from="center", y_edge="min")
mark_pass(MARKS_BOTTOM, "_bottom", x_from="center", y_edge="max")
mark_pass(MARKS_TOPRIGHT, "_topright", x_from="left", y_edge="min")
mark_pass(MARKS_BOTTOMRIGHT, "_bottomright", x_from="left", y_edge="max")

# Cleanup: strip any "top"/"topright" anchor a below-form glyph picked up from a
# run before TOP_POP/TOPRIGHT_POP excluded below-forms (see above) - upsert_anchor
# only ever adds/updates, so a stale anchor here would otherwise never get removed
# just by fixing the pool it's built from.
removed_stray = 0
for gname in font.keys():
    if not _is_below_form(gname):
        continue
    g = font[gname]
    for anchor_name in ("top", "topright"):
        existing = find_anchor(g, anchor_name)
        if existing is not None:
            g.anchors.remove(existing)
            removed_stray += 1

font.save(UFO_PATH, overwrite=True)

print("Added:", report["added"])
print("Updated (already existed):", report["updated"])
print("Removed stray top/topright from below-forms:", removed_stray)
print("No bounds / empty glyphs (flag for review):", len(report["no_bounds"]))
for item in report["no_bounds"]:
    print("  ", item)
