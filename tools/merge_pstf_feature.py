"""
Merges the generated Tulu-Tigalari `pstf` feature (tutg_pstf.fea) into the UFO's
real features.fea, right after the `blwf` block - same pattern as
merge_akhn_feature.py/merge_blwf_feature.py/merge_blws_feature.py, kept as its
own script/step because it depends on a different generated file (tutg_pstf.fea,
written by generate_blwf_feature.py alongside tutg_blwf.fea - see that script's
GENERIC_FALLBACK_EXCLUDE comment for why YA/RA's own post-base combining forms
live in `pstf` instead of blwf's generic fallback).

Must run after merge_blwf_feature.py in the pipeline: this script inserts right
after "} blwf;", so it has nothing to anchor after if blwf hasn't been merged yet.

Idempotency model: same as the other merge_X_feature.py scripts - detects an
existing real pstf block and replaces it in place rather than skipping whenever
one is already present.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")
FEATURES_PATH = os.path.join(UFO_PATH, "features.fea")
PSTF_PATH = os.path.join(HERE, "tutg_pstf.fea")

with open(FEATURES_PATH, encoding="utf-8") as f:
    features = f.read()

if "} blwf;" not in features:
    raise SystemExit("No '} blwf;' block found in features.fea - run merge_blwf_feature.py first.")

with open(PSTF_PATH, encoding="utf-8") as f:
    pstf_content = f.read()

m = re.search(r"feature pstf \{.*?\} pstf;", pstf_content, re.S)
if not m:
    raise SystemExit("Could not find 'feature pstf { ... } pstf;' block in tutg_pstf.fea")
new_pstf_block = m.group(0)

existing = re.search(r"feature pstf \{.*?\} pstf;", features, re.S)
if existing:
    if existing.group(0) == new_pstf_block:
        print("features.fea's pstf block already matches tutg_pstf.fea - nothing to do.")
    else:
        features = features[: existing.start()] + new_pstf_block + features[existing.end() :]
        print("Replaced existing pstf block with regenerated content.")
else:
    blwf_block = re.search(r"feature blwf \{.*?\} blwf;", features, re.S)
    insert_at = blwf_block.end()
    features = features[:insert_at] + "\n\n" + new_pstf_block + features[insert_at:]
    print("Inserted pstf block (first merge).")

with open(FEATURES_PATH, "w", encoding="utf-8") as f:
    f.write(features)

print()
print("Written:", FEATURES_PATH)
print("New file size:", len(features), "bytes")
