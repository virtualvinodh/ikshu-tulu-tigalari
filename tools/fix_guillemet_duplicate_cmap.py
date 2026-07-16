"""
fontmake refused to compile with: "cannot map 'guillemotleft' to U+00AB; already
mapped to 'guillemetleft'" - two glyphs (guillemotleft/guillemetleft and their
-right counterparts) both claim the same codepoint. Pre-existing issue in the
Latin portion of the font, unrelated to the Tigalari work.

"guillemotleft"/"guillemotright" is the standard Adobe Glyph List name for this
character (yes, that's a known AGL misspelling of French "guillemet" that stuck) -
and it's the name features.fea's own kerning classes already reference
(@MMK_L_guillemotleft, @MMK_R_guillemotright, etc.), never the "guillemet*" spelling.
So the "guillemet*" glyphs are the orphaned duplicates - remove their unicode
mapping (not the glyph itself) so cmap has one unambiguous owner per codepoint.
"""
import ufoLib2
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")

font = ufoLib2.Font.open(UFO_PATH)

for name in ("guillemetleft", "guillemetright"):
    g = font.get(name)
    if g is None:
        print(name, "-> not in font, skipping")
        continue
    print(name, "-> clearing unicodes", [hex(u) for u in g.unicodes])
    g.unicodes = []

font.save(UFO_PATH, overwrite=True)
print("Saved.")
