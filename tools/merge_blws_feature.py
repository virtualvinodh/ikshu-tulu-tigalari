"""
Merges the generated Tulu-Tigalari `blws` feature (tutg_blws.fea) into the UFO's
real features.fea, right after the `akhn` block - same pattern as
merge_akhn_feature.py/merge_blwf_feature.py, kept as its own script/step because
it depends on a different generated file (tutg_blws.fea, written by
generate_akhn_feature.py alongside tutg_akhn.fea - see that script's split
comment for why vowel-sign ligature formation lives in `blws` instead of `akhn`).

Must run after merge_akhn_feature.py in the pipeline: this script inserts right
after "} akhn;", so it has nothing to anchor after if akhn hasn't been merged yet.

Idempotency model: same as merge_akhn_feature.py - detects an existing real blws
block and replaces it in place rather than skipping whenever one is already
present, so re-running this after regenerating tutg_blws.fea with different
rules actually takes effect.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")
FEATURES_PATH = os.path.join(UFO_PATH, "features.fea")
BLWS_PATH = os.path.join(HERE, "tutg_blws.fea")

with open(FEATURES_PATH, encoding="utf-8") as f:
    features = f.read()

if "} akhn;" not in features:
    raise SystemExit("No '} akhn;' block found in features.fea - run merge_akhn_feature.py first.")

with open(BLWS_PATH, encoding="utf-8") as f:
    blws_content = f.read()

m = re.search(r"feature blws \{.*?\} blws;", blws_content, re.S)
if not m:
    raise SystemExit("Could not find 'feature blws { ... } blws;' block in tutg_blws.fea")
new_blws_block = m.group(0)

existing = re.search(r"feature blws \{.*?\} blws;", features, re.S)
if existing:
    if existing.group(0) == new_blws_block:
        print("features.fea's blws block already matches tutg_blws.fea - nothing to do.")
    else:
        features = features[: existing.start()] + new_blws_block + features[existing.end() :]
        print("Replaced existing blws block with regenerated content.")
else:
    akhn_block = re.search(r"feature akhn \{.*?\} akhn;", features, re.S)
    insert_at = akhn_block.end()
    features = features[:insert_at] + "\n\n" + new_blws_block + features[insert_at:]
    print("Inserted blws block (first merge).")

with open(FEATURES_PATH, "w", encoding="utf-8") as f:
    f.write(features)

print()
print("Written:", FEATURES_PATH)
print("New file size:", len(features), "bytes")
