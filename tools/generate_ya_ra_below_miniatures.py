"""
Creates real scaled-down "miniature" below-base forms for YA, RA, and RA.alt1 -
per BELOW_BASE_MINIATURE_GLYPHS.md, these are the 2 of 36 consonants whose
existing below-base representation is a genuinely different allograph, not a
miniature of the base letterform at all:

  - ya-tutg.below: independently drawn, "taller/narrower than its base, not a
    miniature of it" - kept as-is (not touched by this script) since it's a real
    hand-drawn shape with its own purpose, just no longer used as YA's below-form
    (see names_override.json's "below_form_overrides" - generate_blwf_feature.py
    now resolves YA to the new "ya-tutg.below.mini" glyph created here instead).
  - RA has no ".below" glyph at all - generate_blwf_feature.py's
    BELOW_FORM_OVERRIDES used raMatra-tutg instead, "wider/shorter than RA's
    independent letterform - again a different allograph, not a miniature".
    raMatra-tutg is untouched by this script (still exists, still used
    wherever else it's referenced, e.g. as a component in ba_ra-tutg) - RA's
    blwf below-form now resolves to the new "ra-tutg.below" created here
    instead, once BELOW_FORM_OVERRIDES's "ra-tutg" entry is dropped.
  - ra-tutg.alt1 has no dedicated below-form at all today (falls back to
    RA's own, i.e. raMatra-tutg, via resolve_alt_below()) - "ra-tutg.below.alt1"
    created here gives it one, matching the "{base}.below.alt{N}" naming
    convention every other registered consonant variant already uses.

Geometry: same convention as the 26 "modal" single-consonant .below glyphs
(BELOW_BASE_MINIATURE_GLYPHS.md) - scale 0.863, yOffset -677, xOffset chosen so
the scaled copy is horizontally centered at x=0 (matching ka-tutg.below/
ta-tutg.below/ha-tutg.below's own component transforms, reverse-engineered
2026-07-21: xOffset = round(-SCALE * base_glyph's own bbox center)).
"""
import ufoLib2
from ufoLib2.objects import Component
import shutil
import time
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")

SCALE = 0.863
Y_OFFSET = -677

NEW_GLYPHS = [
    # (new_name, base_glyph)
    ("ya-tutg.below.mini", "ya-tutg"),
    ("ra-tutg.below", "ra-tutg"),
    ("ra-tutg.below.alt1", "ra-tutg.alt1"),
]


def backup_ufo():
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = UFO_PATH + f".backup-{stamp}"
    shutil.copytree(UFO_PATH, backup_path)
    print("Backed up UFO to:", backup_path)


backup_ufo()
font = ufoLib2.Font.open(UFO_PATH)

created = []
skipped_exists = []
skipped_missing_base = []

for new_name, base_name in NEW_GLYPHS:
    if new_name in font:
        skipped_exists.append(new_name)
        continue
    if base_name not in font:
        skipped_missing_base.append((new_name, base_name))
        continue
    base_glyph = font[base_name]
    bounds = base_glyph.getBounds(font)
    center_x = (bounds.xMin + bounds.xMax) / 2
    x_offset = round(-SCALE * center_x)

    new_glyph = font.newGlyph(new_name)
    new_glyph.width = 0
    new_glyph.components.append(Component(
        baseGlyph=base_name,
        transformation=(SCALE, 0, 0, SCALE, x_offset, Y_OFFSET),
    ))
    created.append(new_name)
    print(f"Created {new_name} <- {base_name} (center_x={center_x}, xOffset={x_offset})")

font.glyphOrder = list(font.glyphOrder) + created
font.save(UFO_PATH, overwrite=True)

print("Created:", created)
print("Skipped (already exists):", skipped_exists)
print("Skipped (missing base glyph):", skipped_missing_base)
