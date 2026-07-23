"""
Duplicates one glyph as a new glyph under a different name - a true copy
(contours, components, anchors, width), not a scaled/referencing component
like generate_below_auto_glyphs.py's miniatures. Meant for cases where a new
.altN slot needs to exist (so it's pickable via TutgVariantSelect once
generate_variant_registry.py/generate_akhn_feature.py are rerun) starting
from an exact copy of an existing form, ready for its own artwork later.

    wsl python3 duplicate_glyph.py

Currently hardcoded to one pair (see SOURCE_NAME/TARGET_NAME below) - repoint
those and rerun for a different pair rather than adding CLI args, matching
this project's one-off-script convention.

unicodes are explicitly NOT copied (cleared on the duplicate) - a second
glyph mapped to the same codepoint as another would be a cmap collision;
.altN forms are only ever reached via GSUB substitution, never their own
cmap entry, so an empty unicodes list is correct here regardless of what the
source glyph happens to have.

Idempotent: skips (does not overwrite) if TARGET_NAME already exists.
"""
import os
import shutil
import time

import ufoLib2

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")

SOURCE_NAME = "repha-tutg.alt1"
TARGET_NAME = "repha-tutg.alt2"


def backup_ufo():
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = UFO_PATH + f".backup-{stamp}"
    shutil.copytree(UFO_PATH, backup_path)
    print("Backed up UFO to:", backup_path)


font = ufoLib2.Font.open(UFO_PATH)

if TARGET_NAME in font:
    raise SystemExit(f"{TARGET_NAME} already exists - not overwriting. Nothing to do.")
if SOURCE_NAME not in font:
    raise SystemExit(f"{SOURCE_NAME} not found in the font.")

backup_ufo()

new_glyph = font[SOURCE_NAME].copy(name=TARGET_NAME)
new_glyph.unicodes = []

font.addGlyph(new_glyph)
font.glyphOrder = list(font.glyphOrder) + [TARGET_NAME]
font.save(UFO_PATH, overwrite=True)

print(f"Duplicated {SOURCE_NAME} -> {TARGET_NAME}")
print(f"  width: {new_glyph.width}")
print(f"  contours: {len(new_glyph.contours)}, components: {len(new_glyph.components)}")
print(f"  anchors: {[(a.name, a.x, a.y) for a in new_glyph.anchors]}")
print()
print("Next: rerun generate_variant_registry.py (and the rest of build_ufo.py's")
print("pipeline) to wire this new .altN slot into TutgVariantSelect.")
