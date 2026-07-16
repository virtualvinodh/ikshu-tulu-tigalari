"""
Merges the generated Tulu-Tigalari `akhn` feature (tutg_akhn.fea) into the UFO's
real features.fea, replacing the dead Malayalam scaffold (script mlm2, -malayalam
glyph names that don't exist in this font) while leaving the unrelated Latin
kerning classes and numeral features (numr/dnom/frac/ordn/lnum/onum/case/zero/cpsp)
untouched.

Does NOT write any GPOS mark/mkmk feature code - ufo2ft (used by fontmake)
auto-generates those from the UFO's own anchors (top/_top, bottom/_bottom,
topright/_topright, bottomright/_bottomright) at compile time, as long as no
explicit `mark`/`mkmk` feature is already defined here.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")
FEATURES_PATH = os.path.join(UFO_PATH, "features.fea")
AKHN_PATH = os.path.join(HERE, "tutg_akhn.fea")

with open(FEATURES_PATH, encoding="utf-8") as f:
    features = f.read()

# Idempotency guard: this does one-shot string surgery on the *original*
# dead-Malayalam-scaffold features.fea (finds "languagesystem mlm2 dflt", inserts
# the akhn block after "} cpsp;"). Rerunning it against its own output would find
# neither anchor in its expected pristine form for step 1, and would insert a
# *second* copy of the akhn block in step 4 - fontmake then refuses to compile on
# the duplicate feature definition. So: if tutg is already the active language
# system, the merge has already happened - skip instead of corrupting the file.
if "languagesystem tutg dflt" in features:
    print("features.fea already has 'languagesystem tutg dflt' - akhn already merged, skipping.")
    raise SystemExit(0)

with open(AKHN_PATH, encoding="utf-8") as f:
    akhn_content = f.read()

# Extract just the "feature akhn { ... } akhn;" block from tutg_akhn.fea (skip its
# own header comment and languagesystem lines - those get handled separately below).
m = re.search(r"feature akhn \{.*?\} akhn;", akhn_content, re.S)
if not m:
    raise SystemExit("Could not find 'feature akhn { ... } akhn;' block in tutg_akhn.fea")
new_akhn_block = m.group(0)

# 1. Replace the languagesystem prefix block: drop the dead `mlm2`, add `tutg`.
features = features.replace(
    "languagesystem DFLT dflt;\n\nlanguagesystem mlm2 dflt;",
    "languagesystem DFLT dflt;\n\nlanguagesystem tutg dflt;",
)

# 2. Remove the dead Malayalam akhn/blwf/abvs feature blocks entirely.
for feat_name in ("akhn", "blwf", "abvs"):
    pattern = re.compile(
        r"### feature:\d+:" + feat_name + r" ###\n"
        r"feature " + feat_name + r" \{.*?\} " + feat_name + r";\n\n?",
        re.S,
    )
    features, n = pattern.subn("", features)
    print(f"Removed {n} dead '{feat_name}' block(s)")

# 3. In the aalt feature, drop references to blwf/abvs (no longer defined) - keep
# the reference to akhn (now pointing at our real Tigalari feature instead).
features = features.replace("feature blwf;\n", "").replace("feature abvs;\n", "")

# 4. Insert the real akhn feature where the dead one used to be (right before cpsp,
# which was immediately followed by the old akhn block in the original file).
features = features.replace(
    "} cpsp;\n",
    "} cpsp;\n\n" + new_akhn_block + "\n",
    1,
)

with open(FEATURES_PATH, "w", encoding="utf-8") as f:
    f.write(features)

print()
print("Written:", FEATURES_PATH)
print("New file size:", len(features), "bytes")
