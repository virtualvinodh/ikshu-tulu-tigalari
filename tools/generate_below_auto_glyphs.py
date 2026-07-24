"""
Automatically creates a scaled-down ("miniature") below-base form for every
existing ligature glyph of these 3 shapes (the ones we already have real drawn
glyphs for):

  (i)   cons + conjoiner + cons [+ conjoiner + cons ...]        (conjunct_ligature)
  (ii)  cons + conjoiner + cons [+ ...] + vowel sign             (vowel_sign_ligature)
  (iii) cons + vowel sign, no conjunct at all                    (vowel_sign_ligature)

New glyph name: "<existing-name>.below.auto" - ".below" to match the font's
existing below-base naming convention, ".auto" appended to flag it as a
generated placeholder, not hand-drawn, and to guarantee it can never collide
with or overwrite a real ".below" glyph.

Skip conditions (both checked, either one skips):
  - "<existing-name>.below" already exists - there's real hand-drawn artwork for
    this specific combination already; don't create a competing auto one.
  - "<existing-name>.below.auto" already exists - re-running this script is a
    no-op for glyphs it already created.

Geometry: single component referencing the existing ligature glyph, scaled to
0.863 (the modal shrink factor across the 31 single-consonant .below glyphs that
ARE simple scaled copies - see BELOW_BASE_MINIATURE_GLYPHS.md), with:
  - yOffset fixed at -677 (the value ~90% of existing .below glyphs use,
    independent of the specific glyph's own bounds).
  - xOffset computed by horizontally centering the scaled copy over the
    original glyph's own bounding-box center - NOT a reverse-engineered match
    for the hand-tuned single-consonant offsets (there isn't one; verified the
    31 "simple scaled copy" .below glyphs' xOffsets don't reduce to any clean
    formula from bbox alone - even the few ALREADY-existing ligature .below
    glyphs, e.g. ha_ya-tutg.below/sha_ya-tutg.below/ssa_va-tutg.below, use
    different scale/yOffset values from each other and from the single-
    consonant norm, confirming these are hand-tuned by eye, not derived).
    This is a simple, consistent placeholder rule - exactly what ".auto" is
    meant to signal: needs visual review, not a final form.

Explicitly NOT done here (out of scope for this pass, matches nothing else in
the pipeline touching ".below.auto" yet):
  - No GDEF Mark classification (public.openTypeCategory) or _bottom anchor -
    classify_blwf_marks.py only targets glyph_classification.json's
    "consonant_below_base" category (single-consonant below-forms), which
    these new compound-ligature glyphs aren't part of. They won't be usable as
    a real below-base GSUB/GPOS attachment target until that's addressed
    separately.
  - No GSUB feature wiring (e.g. a blwf-style fallback rule referencing these).

Re-runnable: the two skip conditions make this idempotent - running it again
after new ligatures are added to the font only creates glyphs for the new ones.
"""
import ufoLib2
from ufoLib2.objects import Component
import json
import os
import shutil
import time

HERE = os.path.dirname(os.path.abspath(__file__))
UFO_PATH = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")

SCALE = 0.863
Y_OFFSET = -677


def is_default_form(name):
    # no ".below"/".altN"/other suffix after "-tutg"
    return "-tutg" in name and "." not in name.partition("-tutg")[2]


def backup_ufo():
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = UFO_PATH + f".backup-{stamp}"
    shutil.copytree(UFO_PATH, backup_path)
    print("Backed up UFO to:", backup_path)


backup_ufo()
font = ufoLib2.Font.open(UFO_PATH)
with open(os.path.join(HERE, "glyph_classification.json"), encoding="utf-8") as f:
    classification = json.load(f)
with open(os.path.join(HERE, "variant_registry.json"), encoding="utf-8") as f:
    variant_registry = json.load(f)

candidates = sorted(set(
    n for n in classification.get("conjunct_ligature", []) + classification.get("vowel_sign_ligature", [])
    if is_default_form(n)
))

# Registered .altN forms of a vowel-sign-ligature compound (e.g.
# ka_uMatra-tutg.alt1) need their own miniature too - added 2026-07-24
# (project owner: confirmed these were silently skipped by the
# is_default_form() filter above, and forcing the below-base subjoin path
# on one fell back to the DEFAULT compound's miniature instead, silently
# discarding the alt selection entirely - see generate_blwf_feature.py's
# matching subjoiner_compound_alt_rules fix). Read directly from
# variant_registry.json's _ligature_variants (not reconstructed by
# assuming a ".altN" naming pattern) and filtered to bases actually
# classified as vowel_sign_ligature - a plain conjunct_ligature's own
# .altN (no vowel sign involved) doesn't have this gap, since the
# subjoiner mechanism for those never depended on a per-root compound name
# the way vowel-sign ligatures do.
vowel_sign_ligature_names = set(classification.get("vowel_sign_ligature", []))
alt_candidates = sorted(set(
    alt_name
    for base_name, variants in variant_registry.get("_ligature_variants", {}).items()
    if base_name in vowel_sign_ligature_names
    for alt_name in variants.values()
))
candidates = sorted(set(candidates) | set(alt_candidates))

created = []
skipped_has_below = []
skipped_already_auto = []
skipped_no_bounds = []
skipped_missing = []

for name in candidates:
    below_name = f"{name}.below"
    auto_name = f"{name}.below.auto"
    if below_name in font:
        skipped_has_below.append(name)
        continue
    if auto_name in font:
        skipped_already_auto.append(name)
        continue
    if name not in font:
        skipped_missing.append(name)
        continue

    base_glyph = font[name]
    bounds = base_glyph.getBounds(font)
    if bounds is None:
        skipped_no_bounds.append(name)
        continue

    center_x = (bounds.xMin + bounds.xMax) / 2
    x_offset = round(center_x * (1 - SCALE), 1)

    new_glyph = font.newGlyph(auto_name)
    new_glyph.width = 0
    new_glyph.components.append(Component(
        baseGlyph=name,
        transformation=(SCALE, 0, 0, SCALE, x_offset, Y_OFFSET),
    ))
    created.append(auto_name)

font.glyphOrder = list(font.glyphOrder) + created
font.save(UFO_PATH, overwrite=True)

print(f"Candidates (conjunct_ligature + vowel_sign_ligature, default forms + registered .altN of vowel_sign_ligature bases): {len(candidates)}")
print(f"  - of which registered .altN alt forms: {len(alt_candidates)}")
print(f"Created: {len(created)}")
print(f"Skipped - real .below already exists: {len(skipped_has_below)}")
print(f"Skipped - .below.auto already exists (already ran): {len(skipped_already_auto)}")
print(f"Skipped - base glyph missing: {len(skipped_missing)} {skipped_missing}")
print(f"Skipped - no bounds/empty glyph: {len(skipped_no_bounds)} {skipped_no_bounds}")
