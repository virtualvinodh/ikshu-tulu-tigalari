"""One-off: rasterize a few glyphs with the exact same math as glyph_viewer.html's
glyphSVG() function, to visually confirm the orientation + shared-scale fix before
reporting back. Not part of the permanent toolset."""
import json
import re
from PIL import Image, ImageDraw

with open("glyph_svg_data.json", encoding="utf-8") as f:
    DATA = json.load(f)

SHARED = dict(xMin=-100, xMax=2100, yMin=-1000, yMax=850)


def parse_path(d):
    """Parse the M/L/C/Z-only path fontTools SVGPathPen emits into a list of polygons
    (each polygon a flattened list of (x,y) points in font-space, cubic curves sampled)."""
    tokens = re.findall(r"[MLCZ]|-?[0-9.]+", d)
    polys = []
    cur_poly = []
    i = 0
    cur = (0, 0)
    while i < len(tokens):
        cmd = tokens[i]
        if cmd == "M":
            if cur_poly:
                polys.append(cur_poly)
            x, y = float(tokens[i+1]), float(tokens[i+2])
            cur = (x, y)
            cur_poly = [cur]
            i += 3
        elif cmd == "L":
            x, y = float(tokens[i+1]), float(tokens[i+2])
            cur = (x, y)
            cur_poly.append(cur)
            i += 3
        elif cmd == "C":
            x1, y1, x2, y2, x3, y3 = (float(tokens[i+k]) for k in range(1, 7))
            p0 = cur
            for t in [k/16 for k in range(1, 17)]:
                mt = 1 - t
                x = mt**3*p0[0] + 3*mt**2*t*x1 + 3*mt*t**2*x2 + t**3*x3
                y = mt**3*p0[1] + 3*mt**2*t*y1 + 3*mt*t**2*y2 + t**3*y3
                cur_poly.append((x, y))
            cur = (x3, y3)
            i += 7
        elif cmd == "Z":
            i += 1
        else:
            i += 1
    if cur_poly:
        polys.append(cur_poly)
    return polys


def component_bbox(comp):
    base = DATA.get(comp["baseGlyph"])
    if not base or not base["bounds"]:
        return None
    x0, y0, x1, y1 = base["bounds"]
    corners = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
    tx = [comp["xx"]*x + comp["yx"]*y + comp["dx"] for x, y in corners]
    ty = [comp["xy"]*x + comp["yy"]*y + comp["dy"] for x, y in corners]
    return (min(tx), min(ty), max(tx), max(ty))


def render(name, size=400, autofit=False, show_anchors=False, show_components=False):
    g = DATA[name]
    b = g["bounds"]
    if autofit and b:
        padX = (b[2]-b[0])*0.12+20
        padY = (b[3]-b[1])*0.12+20
        frame = dict(xMin=b[0]-padX, xMax=b[2]+padX, yMin=b[1]-padY, yMax=b[3]+padY)
    else:
        frame = SHARED
    vbW = frame["xMax"] - frame["xMin"]
    vbH = frame["yMax"] - frame["yMin"]
    scale = size / vbW
    img_h = round(vbH * scale)
    img = Image.new("RGB", (size, img_h), "#f2e8d3")
    draw = ImageDraw.Draw(img)

    def to_px(pt):
        # font-space (y-up) -> pixel-space (y-down), matching the SVG group's scale(1,-1)
        # combined with viewBox origin (xMin, -yMax): pixel_x = (x - xMin) * scale,
        # pixel_y = (yMax - y) * scale
        x, y = pt
        return ((x - frame["xMin"]) * scale, (frame["yMax"] - y) * scale)

    # baseline
    draw.line([to_px((frame["xMin"], 0)), to_px((frame["xMax"], 0))], fill="#00000055", width=1)

    polys = parse_path(g["d"])
    for poly in polys:
        pts = [to_px(p) for p in poly]
        if len(pts) >= 2:
            draw.polygon(pts, fill="#2b2013")

    if show_components:
        colors = ["#a8562d", "#2d6aa8", "#5a962d", "#962d8b"]
        for i, comp in enumerate(g.get("components", [])):
            bbox = component_bbox(comp)
            if not bbox:
                continue
            x0, y0, x1, y1 = bbox
            p0 = to_px((x0, y0)); p1 = to_px((x1, y1))
            color = colors[i % len(colors)]
            draw.rectangle([min(p0[0],p1[0]), min(p0[1],p1[1]), max(p0[0],p1[0]), max(p0[1],p1[1])], outline=color, width=2)
            draw.text((min(p0[0],p1[0]), max(p0[1],p1[1])+2), comp["baseGlyph"], fill=color)

    if show_anchors:
        for a in g["anchors"]:
            is_mark = a["name"].startswith("_")
            color = "#b9563f" if is_mark else "#4f8f7d"
            px, py = to_px((a["x"], a["y"]))
            r = vbW * 0.012 * scale
            draw.ellipse([px-r, py-r, px+r, py+r], fill=color, outline="white")

    return img


# side-by-side comparison strip: full consonant, its below-base miniature, and a conjunct,
# all under the SAME shared frame (this is the actual bug-report scenario).
names = ["ka-tutg", "ka-tutg.below", "ka_ka-tutg"]
imgs = [render(n, size=300, show_anchors=(n == "ka-tutg")) for n in names]
w = sum(im.width for im in imgs) + 20 * (len(imgs) - 1)
h = max(im.height for im in imgs)
strip = Image.new("RGB", (w, h), "#1a1820")
x = 0
for im in imgs:
    strip.paste(im, (x, 0))
    x += im.width + 20
strip.save("_selfcheck_shared_frame.png")

# detail/autofit view of one glyph with anchors, for comparison
detail = render("ba-tutg", size=500, autofit=True, show_anchors=True)
detail.save("_selfcheck_autofit_detail.png")

# composite glyph with component boxes overlaid - the actual feature just added
print("ba_ra-tutg components:", DATA["ba_ra-tutg"]["components"])
composite = render("ba_ra-tutg", size=500, autofit=True, show_components=True)
composite.save("_selfcheck_components.png")

print("saved _selfcheck_shared_frame.png, _selfcheck_autofit_detail.png, _selfcheck_components.png")
