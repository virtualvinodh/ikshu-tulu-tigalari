"""
Compiles glyph_test_page_template.html + test_page_data.json + the built ttf into
the final self-contained glyph_test_page.html (font and data embedded inline as a
base64 data URI / inline JSON, so the page works offline with no external files).

Also embeds a vendored copy of harfbuzzjs (tools/harfbuzzjs_vendor/ - harfbuzz.wasm
+ harfbuzz.js + index.mjs, downloaded once from npm, unmodified) so the page can
shape candidate syllable-popup options with the REAL compiled font client-side and
collapse any that render identically - see initHarfBuzz()/shapeCps() in the
template. Embedded as <script type="text/plain"> blocks (raw ES module source,
read via textContent + Blob URLs at runtime, not executed directly - see comment
there for why) rather than as JS string literals, to avoid any quote/escaping
concerns from arbitrary third-party source text.
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "glyph_test_page_template.html")
DATA = os.path.join(HERE, "test_page_data.json")
SAMPLE_TEXTS = os.path.join(HERE, "sample_texts.json")
BRAHMIC_TABLES = os.path.join(HERE, "brahmic_tables.json")
CONJUNCT_LISTS = os.path.join(HERE, "conjunct_lists.json")
FONT = os.path.join(HERE, "Ikshu-Regular.ttf")
HB_VENDOR = os.path.join(HERE, "harfbuzzjs_vendor")
OUT = os.path.join(os.path.dirname(HERE), "glyph_test_page.html")

with open(TEMPLATE, encoding="utf-8") as f:
    html = f.read()
with open(DATA, encoding="utf-8") as f:
    data_json = f.read()
with open(SAMPLE_TEXTS, encoding="utf-8") as f:
    sample_texts_json = f.read()
with open(BRAHMIC_TABLES, encoding="utf-8") as f:
    brahmic_tables_json = f.read()
with open(CONJUNCT_LISTS, encoding="utf-8") as f:
    conjunct_lists_json = f.read()
with open(FONT, "rb") as f:
    font_b64 = base64.b64encode(f.read()).decode("ascii")
with open(os.path.join(HB_VENDOR, "harfbuzz.wasm"), "rb") as f:
    hb_wasm_b64 = base64.b64encode(f.read()).decode("ascii")
with open(os.path.join(HB_VENDOR, "harfbuzz.js"), encoding="utf-8") as f:
    hb_harfbuzz_js = f.read()
with open(os.path.join(HB_VENDOR, "index.mjs"), encoding="utf-8") as f:
    hb_index_mjs = f.read()

html = html.replace("__TEST_DATA_JSON__", data_json)
html = html.replace("__SAMPLE_TEXTS_JSON__", sample_texts_json)
html = html.replace("__BRAHMIC_TABLES_JSON__", brahmic_tables_json)
html = html.replace("__CONJUNCT_LISTS_JSON__", conjunct_lists_json)
html = html.replace("__FONT_BASE64__", font_b64)
html = html.replace("__HB_WASM_BASE64__", hb_wasm_b64)
html = html.replace("__HB_HARFBUZZ_JS__", hb_harfbuzz_js)
html = html.replace("__HB_INDEX_MJS__", hb_index_mjs)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("Written to:", OUT)
print("Size:", os.path.getsize(OUT) / 1024, "KB")
