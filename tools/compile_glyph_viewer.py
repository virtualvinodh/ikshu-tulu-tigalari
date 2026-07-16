"""
Compiles glyph_viewer_template.html + glyph_svg_data.json into the final
self-contained glyph_viewer.html (all glyph data embedded inline, so the page
works offline with no external files).

    wsl python3 compile_glyph_viewer.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "glyph_viewer_template.html")
DATA = os.path.join(HERE, "glyph_svg_data.json")
OUT = os.path.join(os.path.dirname(HERE), "glyph_viewer.html")

with open(TEMPLATE, encoding="utf-8") as f:
    html = f.read()
with open(DATA, encoding="utf-8") as f:
    data_json = f.read()

html = html.replace("__GLYPH_DATA_JSON__", data_json)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("Written to:", OUT)
print("Size:", os.path.getsize(OUT) / 1024, "KB")
