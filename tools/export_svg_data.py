"""
Exports every -tutg glyph (outline as an SVG path, anchors, bounds, advance width)
into a single JSON file for the HTML glyph viewer (glyph_viewer.html).
"""
import ufoLib2
import json
import os
from fontTools.pens.svgPathPen import SVGPathPen

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")

font = ufoLib2.Font.open(UFO_PATH)

with open(os.path.join(HERE, "glyph_classification.json"), encoding="utf-8") as f:
    classification = json.load(f)
category_of = {}
for cat, names in classification.items():
    for n in names:
        category_of[n] = cat

# Export EVERY glyph in the font, no filtering - including empty ones (no contours,
# no components, e.g. "space", ".notdef", or genuinely unbuilt glyphs like
# "ooMatra-tutg"). "-tutg" glyphs are still flagged isPrimary for the default grid
# view; everything else (Latin, digits, punctuation, sub-parts, empties) is reachable
# via search / category filter / component drill-down.
primary = {g.name for g in font if "-tutg" in g.name}

data = {}
for g in font:
    pen = SVGPathPen(font)
    try:
        g.draw(pen)
    except Exception as e:
        print("skip (draw error):", g.name, e)
        continue
    d = pen.getCommands()
    b = g.getBounds(font)
    anchors = [{"name": a.name, "x": a.x, "y": a.y} for a in g.anchors]
    components = [{
        "baseGlyph": c.baseGlyph,
        "dx": c.transformation.dx, "dy": c.transformation.dy,
        "xx": c.transformation.xx, "xy": c.transformation.xy,
        "yx": c.transformation.yx, "yy": c.transformation.yy,
    } for c in g.components]
    is_empty = not d and not components
    data[g.name] = {
        "d": d,
        "width": g.width,
        "bounds": [b.xMin, b.yMin, b.xMax, b.yMax] if b else None,
        "anchors": anchors,
        "category": category_of.get(g.name, "empty" if is_empty else ("latin/other" if g.name not in primary else "uncategorized")),
        "components": components,
        "isPrimary": g.name in primary,
        "isEmpty": is_empty,
        "unicodes": list(g.unicodes),
    }

out_path = os.path.join(HERE, "glyph_svg_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print("Exported", len(data), "glyphs to", out_path)
print("File size:", os.path.getsize(out_path) / 1024, "KB")
