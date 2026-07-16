"""
Adds missing Unicode codepoint mappings for drawn-but-uncmapped Tulu-Tigalari
characters, found by cross-referencing every default-form glyph in the
"vowel_independent"/"consonant"/"vowel_sign"/"special_mark" categories (see
glyph_classification.json) against the UFO's actual cmap on 2026-07-16.

Deliberately NOT included here (see GSUB_TODO.md / conversation notes for why):
  - nnna-tutg        -> 113B6 is a reserved-but-unassigned slot, no real codepoint yet.
  - candrabindu-tutg, pluta_pluta-tutg, rVocalic_repha-tutg, virama_dotrepha-tutg,
    virama_virama-tutg, rephajoiner-tutg -> compound/reference glyphs, not single
    encoded characters; shouldn't carry their own cmap entry.
  - ooMatra-tutg     -> would map U+113C7 to a genuinely empty/unbuilt glyph, which
    would make that character render as invisible rather than simply absent. Add its
    mapping only once it's actually drawn.
  - rVocalicMatra-tutg-alt1 -> an alternate form, not the default; alternates are
    reached via GSUB (salt/ss0N), not cmap, same as every other .altN glyph in the
    font.

Idempotent: skips any glyph that already has a unicode value assigned.
"""
import ufoLib2
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")

MISSING_MAPPINGS = {
    "rVocalicMatra-tutg": 0x113BD,    # TULU-TIGALARI VOWEL SIGN VOCALIC R
    "svarita-tutg": 0x113E1,          # TULU-TIGALARI VEDIC TONE SVARITA
    "anudatta-tutg": 0x113E2,         # TULU-TIGALARI VEDIC TONE ANUDATTA
    "loopedvirama-tutg": 0x113CF,     # TULU-TIGALARI SIGN LOOPED VIRAMA
    "candraanunasika-tutg": 0x113CA,  # TULU-TIGALARI SIGN CANDRA ANUNASIKA
}

font = ufoLib2.Font.open(UFO_PATH)

added, skipped, missing_glyph = [], [], []
for name, codepoint in MISSING_MAPPINGS.items():
    g = font.get(name)
    if g is None:
        missing_glyph.append(name)
        continue
    if g.unicodes:
        skipped.append((name, [hex(u) for u in g.unicodes]))
        continue
    g.unicodes = [codepoint]
    added.append((name, hex(codepoint)))

font.save(UFO_PATH, overwrite=True)

print("Added:", len(added))
for n, u in added:
    print("  ", n, "->", u)
print("Skipped (already had a unicode value):", len(skipped))
for n, u in skipped:
    print("  ", n, "already", u)
print("Not found in font at all:", len(missing_glyph))
for n in missing_glyph:
    print("  ", n)
