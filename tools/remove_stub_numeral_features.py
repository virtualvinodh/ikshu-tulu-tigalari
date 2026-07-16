"""
fontmake refused to compile with: glyphs referenced by numr/dnom/frac (zero.numr,
oneeighth, etc.) are "missing from the glyph set". Confirmed 2026-07-16: all 10
numr glyphs, all 10 dnom glyphs, and all 7 frac glyphs are entirely absent from this
UFO - these are incomplete stub features left over from whatever template this font
was bootstrapped from (same category of issue as the dead Malayalam akhn/blwf/abvs
scaffold). By contrast lnum, onum, and the zero feature are fully complete (checked
against the actual glyph set) and are left untouched.

This is a pre-existing gap in the Latin/numeral portion of the font, unrelated to
the Tigalari work - removing these three features here is what's needed to get a
compilable test build; drawing the missing numeral-variant glyphs is a separate,
later design task if these OpenType numeral features are wanted.
"""
import re
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")
FEATURES_PATH = os.path.join(UFO_PATH, "features.fea")

with open(FEATURES_PATH, encoding="utf-8") as f:
    features = f.read()

for feat_name in ("numr", "dnom", "frac"):
    pattern = re.compile(
        r"### feature:\d+:" + feat_name + r" ###\n"
        r"feature " + feat_name + r" \{.*?\} " + feat_name + r";\n\n?",
        re.S,
    )
    features, n = pattern.subn("", features)
    print(f"Removed {n} '{feat_name}' block(s)")
    features = features.replace(f"feature {feat_name};\n", "")

with open(FEATURES_PATH, "w", encoding="utf-8") as f:
    f.write(features)

print("Written:", FEATURES_PATH)
