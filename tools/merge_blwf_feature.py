"""
Merges the generated Tulu-Tigalari `blwf` feature (tutg_blwf.fea) into the UFO's
real features.fea, right after the `akhn` block - same idea as
merge_akhn_feature.py for akhn, kept as a separate script/step because it runs
after merge_akhn_feature.py (blwf depends on akhn already being in place to
insert after) and depends on a different generated file (tutg_blwf.fea instead
of tutg_akhn.fea).

Must run after merge_akhn_feature.py in the pipeline: merge_akhn_feature.py strips
the *dead Malayalam* "feature blwf { ... } blwf;" scaffold block from a fresh/raw
UFO (see its step 2) - this script only ever inserts the real Tigalari one, and
would have nothing to anchor after ("} akhn;") if akhn hadn't been merged yet.

Idempotency model (rewritten 2026-07-17, same reasoning as merge_akhn_feature.py):
detects an existing real blwf block and replaces it in place rather than
skipping the whole script whenever one is already present - so re-running this
after regenerating tutg_blwf.fea with different rules actually takes effect,
instead of leaving stale rules sitting in features.fea. The old skip-if-present
guard was how ha_ra-tutg.below/pa_ra-tutg.below stayed merged into the real font
after being removed from generate_akhn_feature.py - regenerating the .fea file
alone did nothing until the merged block was fixed by hand.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")
FEATURES_PATH = os.path.join(UFO_PATH, "features.fea")
BLWF_PATH = os.path.join(HERE, "tutg_blwf.fea")

with open(FEATURES_PATH, encoding="utf-8") as f:
    features = f.read()

if "} akhn;" not in features:
    raise SystemExit("No '} akhn;' block found in features.fea - run merge_akhn_feature.py first.")

with open(BLWF_PATH, encoding="utf-8") as f:
    blwf_content = f.read()

# Extract just the "feature blwf { ... } blwf;" block from tutg_blwf.fea (skip its
# own header comment and languagesystem lines, already present in features.fea).
m = re.search(r"feature blwf \{.*?\} blwf;", blwf_content, re.S)
if not m:
    raise SystemExit("Could not find 'feature blwf { ... } blwf;' block in tutg_blwf.fea")
new_blwf_block = m.group(0)

# Insert the real blwf block, or replace it in place if a previous run already
# inserted one (see docstring).
existing = re.search(r"feature blwf \{.*?\} blwf;", features, re.S)
if existing:
    if existing.group(0) == new_blwf_block:
        print("features.fea's blwf block already matches tutg_blwf.fea - nothing to do.")
    else:
        features = features[: existing.start()] + new_blwf_block + features[existing.end() :]
        print("Replaced existing blwf block with regenerated content.")
else:
    features = features.replace("} akhn;\n", "} akhn;\n\n" + new_blwf_block + "\n", 1)
    print("Inserted blwf block (first merge).")

with open(FEATURES_PATH, "w", encoding="utf-8") as f:
    f.write(features)

print()
print("Written:", FEATURES_PATH)
print("New file size:", len(features), "bytes")
