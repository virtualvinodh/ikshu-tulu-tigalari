"""
Merges the generated Tulu-Tigalari `rkrf` feature (tutg_rkrf.fea) into the UFO's
real features.fea, right after the `pstf` block - same pattern as
merge_akhn_feature.py/merge_blwf_feature.py/merge_blws_feature.py/
merge_pstf_feature.py, kept as its own script/step because it depends on a
different generated file (tutg_rkrf.fea, written by generate_blwf_feature.py
alongside tutg_blwf.fea/tutg_pstf.fea - see that script's RAKAR_EXCLUDE comment
for why RA's own post-base "Rakar" combining form lives in the real, registered
`rkrf` (Rakar Forms) OpenType feature instead of `pstf`, which YA uses).

Must run after merge_pstf_feature.py in the pipeline: this script inserts right
after "} pstf;", so it has nothing to anchor after if pstf hasn't been merged yet.

Idempotency model: same as the other merge_X_feature.py scripts - detects an
existing real rkrf block and replaces it in place rather than skipping whenever
one is already present.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")
FEATURES_PATH = os.path.join(UFO_PATH, "features.fea")
RKRF_PATH = os.path.join(HERE, "tutg_rkrf.fea")

with open(FEATURES_PATH, encoding="utf-8") as f:
    features = f.read()

if "} pstf;" not in features:
    raise SystemExit("No '} pstf;' block found in features.fea - run merge_pstf_feature.py first.")

with open(RKRF_PATH, encoding="utf-8") as f:
    rkrf_content = f.read()

m = re.search(r"feature rkrf \{.*?\} rkrf;", rkrf_content, re.S)
if not m:
    raise SystemExit("Could not find 'feature rkrf { ... } rkrf;' block in tutg_rkrf.fea")
new_rkrf_block = m.group(0)

existing = re.search(r"feature rkrf \{.*?\} rkrf;", features, re.S)
if existing:
    if existing.group(0) == new_rkrf_block:
        print("features.fea's rkrf block already matches tutg_rkrf.fea - nothing to do.")
    else:
        features = features[: existing.start()] + new_rkrf_block + features[existing.end() :]
        print("Replaced existing rkrf block with regenerated content.")
else:
    pstf_block = re.search(r"feature pstf \{.*?\} pstf;", features, re.S)
    insert_at = pstf_block.end()
    features = features[:insert_at] + "\n\n" + new_rkrf_block + features[insert_at:]
    print("Inserted rkrf block (first merge).")

with open(FEATURES_PATH, "w", encoding="utf-8") as f:
    f.write(features)

print()
print("Written:", FEATURES_PATH)
print("New file size:", len(features), "bytes")
