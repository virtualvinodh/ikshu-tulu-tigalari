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
with open(os.path.join(HERE, "variant_registry.json"), encoding="utf-8") as f:
    variant_registry = json.load(f)

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

# Bare (non-below-form) conjunct ligatures ending in "_ya"/"_ra" share YA's/
# RA's own descending-tail shape (confirmed 2026-07-21 by project owner, same
# reasoning as the below-form family above) but never had a bottomright anchor
# at all - only consonants/below-forms did. Computed dynamically (any bare
# glyph ending in "_ya-tutg"/"_ra-tutg", no further suffix) so a newly added
# ligature is covered automatically.
BARE_YA_LIGATURES = {n for n in font.keys() if n.endswith("_ya-tutg")}
BARE_RA_LIGATURES = {n for n in font.keys() if n.endswith("_ra-tutg")}

# A below-base form can itself be the base a following U/UU vowel sign attaches
# to (same "ink-touching fallback" reasoning as a plain consonant), so it needs
# its own bottomright too - not just bottom/_bottom.
#
# raMatra-tutg (RA's own post-base "Rakar" form) added 2026-07-22 (project
# owner request, same "bottom" gap fixed just above): a further vowel sign can
# follow it directly (the generic "consonant+RA+vowel-sign" fallback path, no
# dedicated ligature), so it needs bottomright too, computed the same way as
# every other plain consonant (find_ink_bottom_right below) - not folded into
# BOTTOMRIGHT_LOWEST_POINT_OVERRIDE, which is for ligatures built FROM
# raMatra-tutg as a component, a different concern from raMatra-tutg's own anchor.
BOTTOMRIGHT_POP = (
    d["consonant"] + d["consonant_below_base"] + LIGATURE_BELOW_FORMS + BELOW_AUTO_POP
    + list(BARE_YA_LIGATURES) + list(BARE_RA_LIGATURES) + ["raMatra-tutg"]
)

MARKS_TOP = ["repha-tutg", "repha-tutg.alt1", "svarita-tutg"]
MARKS_BOTTOM = ["anudatta-tutg", "germinationmark-tutg", "lVocalicMatra-tutg", "llVocalicMatra-tutg"]
MARKS_TOPRIGHT = ["virama-tutg"]
# rVocalicMatra/rrVocalicMatra added 2026-07-21: needed as a GPOS fallback for
# the "_ya"/"_ra"-ending conjuncts excluded from generate_blwf_feature.py's
# decompose fix (see BARE_YA_LIGATURES/BARE_RA_LIGATURES above) - those rely on
# bottomright/_bottomright to attach ALL 4 of U/UU/Vocalic-R/Vocalic-RR
# directly to the intact ligature, not just U/UU. Safe for the other 34
# consonants too: they always have their own dedicated compound for all 4
# roots (confirmed in VOWEL_SIGN_LIGATURE_GAP.md), so GSUB always merges the
# vowel sign into a single glyph before GPOS ever sees a bare mark glyph to
# attach - this anchor pair only ever activates when GSUB left it unmerged.
MARKS_BOTTOMRIGHT = ["uMatra-tutg", "uuMatra-tutg", "rVocalicMatra-tutg", "rrVocalicMatra-tutg"]

# Every registered .altN variant of the 4 names above ALSO needs its own
# _bottomright (added 2026-07-22, project owner request): mark_pass only ever
# wrote this anchor for the 4 plain glyphs, so an alt form substituted in via
# TutgVariantSelect (uMatra-tutg.alt1 etc.) had NO _bottomright at all - if the
# bottomright/_bottomright GPOS fallback path ever activates while an alt form
# is on screen, it would have nothing to attach to and just sit at default
# advance-width position. Read the real glyph name straight out of
# variant_registry.json (not reconstructed as f"{base}.alt{n}") since at least
# one entry uses a different separator on disk (rVocalicMatra-tutg-alt1, a
# hyphen, not a dot) - same "trust the registry, not a naming assumption"
# principle generate_blwf_feature.py's VARIANT_REGISTRY lookups already follow.
MARKS_BOTTOMRIGHT_MISSING_VARIANT = []  # (base_name, variant_name) registered but not a real glyph
for _base_name in list(MARKS_BOTTOMRIGHT):
    for _variant_name in variant_registry.get(_base_name, {}).values():
        if _variant_name not in font:
            MARKS_BOTTOMRIGHT_MISSING_VARIANT.append((_base_name, _variant_name))
            continue
        MARKS_BOTTOMRIGHT.append(_variant_name)

# uMatra-tutg.below/uuMatra-tutg.below added 2026-07-22 (project owner request):
# not a registered TutgVariantSelect alt, just the below-base form these two
# vowel signs get when THEY serve as the base for further stacking - same
# "needs its own _bottomright too" reasoning as the .altN variants above, but
# not discoverable via variant_registry.json since it isn't a selectable variant.
for _below_name in ("uMatra-tutg.below", "uuMatra-tutg.below"):
    if _below_name in font:
        MARKS_BOTTOMRIGHT.append(_below_name)

# Most of the above are round/circular enough that the blended "furthest right
# + furthest up" ink search (find_ink_top_right) lands in a sensible spot, but
# uMatra-tutg/uMatra-tutg.alt2/.below and uuMatra-tutg/.alt4/.below specifically
# were checked and confirmed wrong by the project owner (2026-07-22) - these
# read as a simple round dot shape, so the intended attachment point is just
# the shape's own topmost point (its "12 o'clock", where quadrant 1 starts
# going clockwise), not a right-biased corner. The rest (other alt shapes,
# rVocalicMatra/rrVocalicMatra) were confirmed fine as-is and left on
# find_ink_top_right.
MARKS_BOTTOMRIGHT_TOPMOST_OVERRIDE = {
    "uMatra-tutg", "uMatra-tutg.alt2", "uMatra-tutg.alt3", "uMatra-tutg.alt4",
    "uMatra-tutg.alt5", "uMatra-tutg.alt6", "uMatra-tutg.below",
    "uuMatra-tutg", "uuMatra-tutg.alt4", "uuMatra-tutg.below",
}


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


def find_lowest_point(glyph, font):
    pts = outline_points(glyph, font)
    if not pts:
        return None
    return min(pts, key=lambda p: p[1])


def find_topmost_point(glyph, font):
    """The glyph's own topmost outline point, at its true x (not forced to
    bbox center) - for a round/circular shape this naturally lands near the
    horizontal center anyway, since that's where the top of a circle sits.
    Mirrors find_lowest_point (min y) but for the opposite extreme."""
    pts = outline_points(glyph, font)
    if not pts:
        return None
    return max(pts, key=lambda p: p[1])


def find_ink_top_right(glyph, font):
    """Same blended-score ink search as find_ink_bottom_right, but for the
    corner diagonally opposite: furthest right AND furthest up. Leftmost-point
    was tried first and rejected (2026-07-22, project owner) - U/UU are round/
    circular shapes, so their true leftmost point sits at the vertical middle,
    nowhere near where the sign visually starts. Top-right is where these
    marks actually begin, matching the base glyph's own bottomright anchor
    (furthest right + furthest down), which is where they're meant to attach."""
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
        score = xn + yn  # far right + far up, normalized
        if score > best_score:
            best_score = score
            best = (x, y)
    return best


# ya-tutg.below (and every "<...>_ya-tutg.below[.auto]" ligature ending in YA,
# which all carry the same descending tail via their own ya component) extends
# much further down than it does right, so find_ink_bottom_right()'s "far right
# + far down" blended score picks a point on the tail's side, well above the
# actual bottom - confirmed 2026-07-21 by project owner (checked all 47 "_ya"
# ligature below-forms, every one differs from its true lowest point by 8-251
# units): bottomright here should be the glyph's true lowest ink point instead
# of the blended-corner heuristic. Computed from the font's own glyph list
# (not a static name list) so any "_ya" ligature added later is covered too.
# Extended 2026-07-21 to the bare (non-below-form) "_ya" conjuncts too (see
# BARE_YA_LIGATURES above) - same tail shape, same fix. Extended again
# 2026-07-21 to "_ra"-ending ligatures (bare - BARE_RA_LIGATURES - and
# below-form) for the same reason: they're built with raMatra-tutg (RA's own
# traditional combining form) as a component, which carries the same kind of
# descending-tail divergence from the blended heuristic.
BOTTOMRIGHT_LOWEST_POINT_OVERRIDE = {
    n for n in font.keys()
    if n == "ya-tutg.below"
    or n.endswith("_ya-tutg.below") or n.endswith("_ya-tutg.below.auto")
    or n.endswith("_ra-tutg.below") or n.endswith("_ra-tutg.below.auto")
} | BARE_YA_LIGATURES | BARE_RA_LIGATURES

# --- run all passes ---
base_pass(TOP_POP, "top", TOP_GAP, x_from="center", y_edge="max")
base_pass(BOTTOM_POP, "bottom", BOTTOM_GAP, x_from="center", y_edge="min")
base_pass(TOPRIGHT_POP, "topright", TOPRIGHT_GAP, x_from="edge", y_edge="max")

for gname in BOTTOMRIGHT_POP:
    g = font[gname]
    if gname in BOTTOMRIGHT_LOWEST_POINT_OVERRIDE:
        pt = find_lowest_point(g, font)
        if pt is None:
            report["no_bounds"].append((gname, "bottomright"))
            continue
        report[upsert_anchor(gname, "bottomright", pt[0], pt[1])] += 1
        continue
    pt = find_ink_bottom_right(g, font)
    if pt is None:
        report["no_bounds"].append((gname, "bottomright"))
        continue
    report[upsert_anchor(gname, "bottomright", pt[0], pt[1])] += 1

# raMatra-tutg (RA's own post-base "Rakar" form) had NO anchors at all -
# classified under vowel_sign_component in glyph_classification.json, not
# consonant/consonant_below_base, so it fell through every POP list above
# (found 2026-07-22 while investigating why "consonant+RA+vowel-sign" never
# mark-attaches via GPOS). Added directly here (not folded into BOTTOM_POP)
# per project owner's explicit request for the bottommost ink point specifically,
# not base_pass()'s generic bbox-center-minus-gap formula every other
# consonant's "bottom" anchor uses.
_ramatra_bottom = find_lowest_point(font["raMatra-tutg"], font)
if _ramatra_bottom is None:
    report["no_bounds"].append(("raMatra-tutg", "bottom"))
else:
    report[upsert_anchor("raMatra-tutg", "bottom", _ramatra_bottom[0], _ramatra_bottom[1])] += 1

mark_pass(MARKS_TOP, "_top", x_from="center", y_edge="min")
mark_pass(MARKS_BOTTOM, "_bottom", x_from="center", y_edge="max")
mark_pass(MARKS_TOPRIGHT, "_topright", x_from="left", y_edge="min")

# Ink-based, not bbox-based (see find_ink_top_right/find_topmost_point
# docstrings) - same "touch the real outline" principle the base bottomright
# anchor already uses. MARKS_BOTTOMRIGHT_TOPMOST_OVERRIDE picks the simpler
# topmost-point search for the round-dot shapes it was confirmed wrong for;
# everything else keeps the blended top-right search.
for gname in MARKS_BOTTOMRIGHT:
    g = font[gname]
    if gname in MARKS_BOTTOMRIGHT_TOPMOST_OVERRIDE:
        pt = find_topmost_point(g, font)
    else:
        pt = find_ink_top_right(g, font)
    if pt is None:
        report["no_bounds"].append((gname, "_bottomright"))
        continue
    report[upsert_anchor(gname, "_bottomright", pt[0], pt[1])] += 1

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
print("MARKS_BOTTOMRIGHT variants skipped (registered but not a real glyph):", len(MARKS_BOTTOMRIGHT_MISSING_VARIANT))
for item in MARKS_BOTTOMRIGHT_MISSING_VARIANT:
    print("  ", item)
