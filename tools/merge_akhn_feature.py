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

Renamed from merge_features.py (2026-07-17) once merge_blwf_feature.py made clear
this is one of a pair of per-feature merge scripts, not "the" merge step - keeping
both explicitly named by feature, not one generic and one specific. As of
2026-07-21 there are four such pairs (akhn, blwf, blws, pstf) - see
merge_blws_feature.py/merge_pstf_feature.py for the other two, split out of
generate_akhn_feature.py/generate_blwf_feature.py's own docstrings.

Idempotency model (rewritten 2026-07-17): steps 1-3 are naturally idempotent
find-and-replace on text that's only ever present in the original dead-scaffold
file, so they silently no-op once already applied. Step 4 (the actual akhn block)
used to be guarded by skipping the ENTIRE script if "languagesystem tutg dflt" was
already present - which meant re-running this after regenerating tutg_akhn.fea
with different rules (not just the first time) silently left the UFO's
features.fea stale, since the guard has no way to tell "already merged, nothing
changed" apart from "already merged, rules changed underneath it". Confirmed this
the hard way: removing two bad rules from generate_akhn_feature.py and rerunning
the pipeline did NOT remove them from the compiled font - they were still sitting
in the already-merged features.fea until edited out by hand. Fixed by detecting
the EXISTING akhn block (if any) and replacing it in place with the freshly
generated one, rather than skip-if-present - safe to run any number of times,
and always reflects whatever tutg_akhn.fea currently says.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")
FEATURES_PATH = os.path.join(UFO_PATH, "features.fea")
AKHN_PATH = os.path.join(HERE, "tutg_akhn.fea")

with open(FEATURES_PATH, encoding="utf-8") as f:
    features = f.read()

with open(AKHN_PATH, encoding="utf-8") as f:
    akhn_content = f.read()

# Extract just the "feature akhn { ... } akhn;" block from tutg_akhn.fea (skip its
# own header comment and languagesystem lines - those get handled separately below).
m = re.search(r"feature akhn \{.*?\} akhn;", akhn_content, re.S)
if not m:
    raise SystemExit("Could not find 'feature akhn { ... } akhn;' block in tutg_akhn.fea")
new_akhn_block = m.group(0)

# 1. Replace the languagesystem prefix block: drop the dead `mlm2`, add `tutg`.
# No-op once already done - the "mlm2" text won't be found a second time.
features = features.replace(
    "languagesystem DFLT dflt;\n\nlanguagesystem mlm2 dflt;",
    "languagesystem DFLT dflt;\n\nlanguagesystem tutg dflt;",
)

# 2. Remove the dead Malayalam akhn/blwf/abvs feature blocks entirely. No-op once
# already removed - their "### feature:N:<name> ###" comment markers (only present
# in the original glyphsApp-style scaffold, never in our own generated blocks)
# won't be found again.
for feat_name in ("akhn", "blwf", "abvs"):
    pattern = re.compile(
        r"### feature:\d+:" + feat_name + r" ###\n"
        r"feature " + feat_name + r" \{.*?\} " + feat_name + r";\n\n?",
        re.S,
    )
    features, n = pattern.subn("", features)
    if n:
        print(f"Removed {n} dead '{feat_name}' block(s)")

# 3. In the aalt feature, drop references to blwf/abvs (no longer defined) - keep
# the reference to akhn (now pointing at our real Tigalari feature instead).
# No-op once already done.
features = features.replace("feature blwf;\n", "").replace("feature abvs;\n", "")

# 4. Insert the real akhn block, or replace it in place if a previous run already
# inserted one (see docstring - this is what makes re-running after a rule change
# actually take effect, instead of silently keeping stale rules).
existing = re.search(r"feature akhn \{.*?\} akhn;", features, re.S)
if existing:
    if existing.group(0) == new_akhn_block:
        print("features.fea's akhn block already matches tutg_akhn.fea - nothing to do.")
    else:
        features = features[: existing.start()] + new_akhn_block + features[existing.end() :]
        print("Replaced existing akhn block with regenerated content.")
else:
    features = features.replace("} cpsp;\n", "} cpsp;\n\n" + new_akhn_block + "\n", 1)
    print("Inserted akhn block (first merge).")

with open(FEATURES_PATH, "w", encoding="utf-8") as f:
    f.write(features)

print()
print("Written:", FEATURES_PATH)
print("New file size:", len(features), "bytes")
