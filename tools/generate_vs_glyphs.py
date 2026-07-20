"""
Adds vs1-tutg through vs6-tutg plus vs11-tutg/vs12-tutg (real, encoded,
empty/zero-width glyphs for Unicode Variation Selectors 1-6, 11, 12 -
U+FE00-U+FE05, U+FE0A, U+FE0B) and subjoiner-tutg (an UNENCODED intermediate
glyph - no codepoint of its own, purely a GSUB-internal token) to the UFO.

Why these need to exist as ordinary glyphs at all: GSUB lookups only ever
match glyph IDs, never Unicode codepoints, so a variation selector can only
appear as an operand in a `sub ... by ...;` rule if the font gives it some
glyph identity first. The earlier prototype (generate_variant_registry_cmap.py)
got that glyph identity indirectly via a 'cmap' format 14 (Unicode Variation
Sequence) subtable, resolved only in the specific context of a registered
base+selector pair. That works, but it's binary-only (no FEA source exists for
it - written straight into a compiled TTF by a one-off Python script) and
doesn't fit this project's normal editable pipeline (UFO + features.fea,
everything else reviewable as text and rebuilt by fontmake).

This script does the simpler thing instead: give VS1-VS6 completely ordinary
cmap entries, just like any other encoded glyph in this font (e.g.
conjoiner-tutg, itself a control-ish joining character with a real glyph).
Once they're real glyphs, plain akhn/blwf GSUB rules can reference them
directly - "sub bha-tutg vs1-tutg by bha-tutg.alt1;" - no cmap trickery, no
marker-glyph indirection, fully hand-editable in the .fea source. See the
conversation this was scoped in for the fuller reasoning (variant_registry.json
prototype -> conjoiner+VS marker-glyph prototype -> this).

Zero width + empty outline so that if one of these ever ends up somewhere no
GSUB rule consumes it (unregistered base, or typed on its own), it renders as
nothing - same silent no-op fallback the cmap14 prototype had via HarfBuzz's
Default_Ignorable handling, just achieved directly instead of relying on that
fallback.

subjoiner-tutg is what "conjoiner-tutg + vs1-tutg" collapses into (an akhn
lookup does that collapse - see generate_akhn_feature.py's TutgSubjoinerForm).
Its whole purpose is to be the trigger glyph for blwf's new "force below-base
stacking" lookup (TutgBlwfSubjoiner) - so it needs the exact same fallback
appearance conjoiner-tutg has if IT ever ends up unconsumed (component copy of
conjoiner-tutg's own outline, not empty), for the same reason conjoiner-tutg
itself isn't empty: a leftover, un-shrunk marker should visibly read as
"incomplete stacking request" rather than silently vanish.

Not yet added to glyph_classification.json - same as generate_below_auto_glyphs.py's
".below.auto" glyphs, these postdate that file and classify_glyphs.py has no
naming rule for them; classify separately if/when needed.

Re-runnable: skips any glyph that already exists.
"""
import shutil
import time
import os

import ufoLib2
from ufoLib2.objects import Component

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")

VS_GLYPHS = [
    ("vs1-tutg", 0xFE00),
    ("vs2-tutg", 0xFE01),
    ("vs3-tutg", 0xFE02),
    ("vs4-tutg", 0xFE03),
    ("vs5-tutg", 0xFE04),
    ("vs6-tutg", 0xFE05),
    # VS11/VS12 (added 2026-07-20): conjunct-ligature-alternate selection
    # (generate_akhn_feature.py's TutgConjunctVariantSelect) - see
    # variant_registry.json's "_conjunct_variants_readme" for why this layer
    # uses an index range offset by +10 rather than starting at VS1 again.
    ("vs11-tutg", 0xFE0A),
    ("vs12-tutg", 0xFE0B),
]

SUBJOINER_NAME = "subjoiner-tutg"
CONJOINER_NAME = "conjoiner-tutg"


def backup_ufo():
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = UFO_PATH + f".backup-{stamp}"
    shutil.copytree(UFO_PATH, backup_path)
    print("Backed up UFO to:", backup_path)


backup_ufo()
font = ufoLib2.Font.open(UFO_PATH)

created = []
skipped = []

for name, codepoint in VS_GLYPHS:
    if name in font:
        skipped.append(name)
        continue
    glyph = font.newGlyph(name)
    glyph.width = 0
    glyph.unicodes = [codepoint]
    created.append(name)

if SUBJOINER_NAME in font:
    skipped.append(SUBJOINER_NAME)
elif CONJOINER_NAME not in font:
    raise SystemExit(f"{CONJOINER_NAME} not found in UFO - can't build {SUBJOINER_NAME} as a copy of it.")
else:
    conjoiner = font[CONJOINER_NAME]
    glyph = font.newGlyph(SUBJOINER_NAME)
    glyph.width = conjoiner.width
    glyph.components.append(Component(baseGlyph=CONJOINER_NAME, transformation=(1, 0, 0, 1, 0, 0)))
    created.append(SUBJOINER_NAME)

if created:
    font.glyphOrder = list(font.glyphOrder) + created
    font.save(UFO_PATH, overwrite=True)

print(f"Created: {len(created)} {created}")
print(f"Skipped (already existed): {len(skipped)} {skipped}")
