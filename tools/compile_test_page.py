"""
Compiles glyph_test_page_template.html + test_page_data.json + the built ttf into
the final self-contained glyph_test_page.html (font and data embedded inline as a
base64 data URI / inline JSON, so the page works offline with no external files).
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

html = html.replace("__TEST_DATA_JSON__", data_json)
html = html.replace("__SAMPLE_TEXTS_JSON__", sample_texts_json)
html = html.replace("__BRAHMIC_TABLES_JSON__", brahmic_tables_json)
html = html.replace("__CONJUNCT_LISTS_JSON__", conjunct_lists_json)
html = html.replace("__FONT_BASE64__", font_b64)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("Written to:", OUT)
print("Size:", os.path.getsize(OUT) / 1024, "KB")
