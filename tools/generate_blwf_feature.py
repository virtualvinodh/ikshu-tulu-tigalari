"""
Builds a ready-to-merge .fea file for the `blwf` (Below-base Forms) feature.

TutgBlwfSubjoiner (added 2026-07-20, runs first): "subjoiner-tutg + consonant
(or any registered char-variant of it) -> consonant's below-form". Forces
below-base stacking on demand - the other half of akhn's TutgSubjoinerForm
lookup, which collapses a typed "conjoiner + VS1" into the subjoiner-tutg
glyph this lookup matches on. See its own comment further down for the full
reasoning.

Alt-consonant fallback (added 2026-07-20, folded directly into TutgBlwf's own
rule list): every registered variant_registry.json .altN consonant form also
gets a "conjoiner-tutg + CONS.altN -> CONS.altN's OWN below-form" rule, not
just the plain consonant. Without this, a variant-selected consonant used as
the second half of a plain (non-VS) conjunct left the conjoiner completely
unconsumed - confirmed via the Variant Registry tab's Consonant Variant
Matrix, which showed the conjoiner's own real fallback artwork in every cell
before this fix. Every one of the 24 registered consonant-variant entries
turns out to have its own dedicated, hand-drawn "{base}.below.altN" glyph
(e.g. bha-tutg.alt1 -> bha-tutg.below.alt1) - resolve_alt_below() prefers that
over the plain consonant's own below-form, which is only a fallback for the
one case with no dedicated alt-below drawn (ra-tutg.alt1).

Three more kinds of rule, in two more lookups:

**Lookup `TutgBlwfDecompose`** (added 2026-07-18, runs first): a targeted fix
for conjunct ligatures (akhn's own dedicated multi-consonant glyphs, e.g.
ka_ka-tutg) followed by U/UU/Vocalic R/Vocalic RR where THAT SPECIFIC
combination has no dedicated compound ligature of its own - see
VOWEL_SIGN_LIGATURE_GAP.md for the full writeup. Without this, e.g.
"KA+conjoiner+KA+U" shapes to `['ka_katutg', 'u113BB']` - the vowel sign left
bare and unattached, because akhn already collapsed KA+conjoiner+KA into
ka_ka-tutg before there's any chance to notice U needs the SECOND ka's own
u-ligating shape. The fix: decompose the ligature back into its raw consonant
sequence, but ONLY when immediately followed by one of the 4 vowel signs it
doesn't have a compound for (checked per-ligature AND per-vowel-sign, not "has
ANY compound" - 15 ligatures like ka_ta-tutg have a compound for SOME of the 4
signs already, e.g. ka_ta_uMatra-tutg, and must only decompose before the ones
they're actually missing, or a working akhn-formed compound would get
needlessly undone). Grouped by identical missing-vowel-sign set so the
contextual trigger is written as one glyph-class line per group, not one line
per ligature.

**Lookup `TutgBlwf`** (existing, extended): after the decompose exposes the raw
consonant sequence again, this is what actually re-ligates the newly-exposed
last consonant with the vowel sign AND shrinks it into a below-base form, in
one step - no separate re-ligation pass needed, since the final compound's
below-form glyph is already known. Three rule shapes, LONGEST FIRST (critical -
see below):

1. NEW (2026-07-18) 3-glyph compound rule: "conjoiner + <consonant> + <vowel
   sign>" -> "<consonant>_<root>-tutg's below-form" - one per distinct
   (last-consonant, missing-root) pair actually needed by the decompose set
   above (not all 36*4 - only the combinations that can occur).
2. Per-ligature (added 2026-07-17): "conjoiner + <ligature>" -> "<ligature>'s
   below-form" - covers a conjunct that itself has a dedicated akhn ligature
   (e.g. ka_ma-tutg) still getting a correctly-shaped below-base stack when
   something else conjoins onto the END of it.
3. Per-consonant fallback (original): "conjoiner + consonant" -> "consonant's
   below-form" - the generic fallback for any conjunct akhn didn't already
   claim.

CRITICAL: rule 1 (3 glyphs) MUST be listed before rules 2/3 (2 glyphs each) in
the SAME lookup - all of them start with "conjoiner-tutg", so within HarfBuzz's
ligature-substitution subtable they're all candidates for the same starting
position, tried in file order. If the 2-glyph "conjoiner + ga-tutg -> ga-tutg.below"
rule came first, it would steal the match and shrink the consonant alone before
the vowel sign ever got a chance to combine with it, leaving the vowel sign
stranded exactly as before this fix. Rules 2 and 3 don't compete with each
other or with rule 1's OUTPUT the same way (each rule's second glyph is a
distinct glyph identity, not a prefix of another match), so their relative
order doesn't matter - only "3-glyph before 2-glyph" does.

IMPORTANT, found the hard way (2026-07-17): rule 2/3's shape is "conjoiner +
<the ligature's own OUTPUT glyph name>", NOT "conjoiner + <the ligature's raw
akhn input sequence>". `akhn` runs before `blwf` in the standard feature-
application order, so by the time `blwf`'s lookup sees the glyph stream,
"ka-tutg conjoiner-tutg ma-tutg" has ALREADY been collapsed into the single
glyph "ka_ma-tutg" by `akhn` - that raw 3-glyph sequence never reaches `blwf`
intact. An earlier version of this script generated "conjoiner + ka-tutg +
conjoiner + ma-tutg -> ka_ma-tutg.below.auto" (matching the pre-akhn sequence)
and confirmed via uharfbuzz that it never fires: shaping "GA+conj+KA+conj+MA"
produced `['u11394', 'u113D0', 'ka_matutg']` - the leading conjoiner left
dangling and unconsumed. The fix is exactly as simple as the per-consonant
case: match the ligature's own OUTPUT glyph name directly, since that's what's
actually in the stream by then. (Rule 1 above is different again - it matches
RAW consonant + vowel-sign glyphs, because those are only ever exposed AFTER
the new decompose lookup runs, specifically so they're raw at this point.)

This MUST be a ligature-style substitution (both input glyphs consumed, one output
glyph: `sub conjoiner-tutg ka-tutg by ka-tutg.below;`), not a chaining-contextual
single substitution (`sub conjoiner-tutg ka-tutg' by ka-tutg.below;`). The latter
only replaces the marked glyph and leaves `conjoiner-tutg` itself sitting in the
glyph stream afterward - and conjoiner-tutg has real, visible dotted-circle-style
artwork drawn (the intended USE fallback appearance for an Invisible_Stacker that
never got consumed), so that bug renders as a dotted circle glaring out of every
below-base conjunct instead of a clean stack. Confirmed via uharfbuzz before/after:
the contextual form left `u113D0` (conjoiner) in the shaped glyph list; the
ligature form consumes it entirely.

Why this feature exists alongside `akhn` (generate_akhn_feature.py): `akhn` only
covers the 452 combinations that have a dedicated, hand-drawn ligature glyph
(e.g. ka_ka-tutg). Most of the 36*36 possible consonant pairs have no such glyph.
Per the standard Indic/USE feature-application order, `akhn` runs first and claims
whatever specific conjuncts it recognizes; any "conjoiner + consonant" sequence
`akhn` didn't touch reaches `blwf` unchanged, which then applies this generic
fallback - so every possible conjunct renders as *something* correctly shaped
(a below-base stack), not a default/unjoined pair, even without a bespoke ligature.

Below-base glyph naming is almost universally "{consonant}.below" (e.g.
ka-tutg -> ka-tutg.below). Two documented exceptions, RA and YA (see
BELOW_BASE_MINIATURE_GLYPHS.md), each have a real, scaled-down miniature too
(ra-tutg.below, ya-tutg.below.mini, ra-tutg.below.alt1 - all from
generate_ya_ra_below_miniatures.py, 2026-07-21) - but project owner confirmed
2026-07-21 these two paths must stay DELIBERATELY SEPARATE, not merged:

  - The GENERIC path (plain "conjoiner + consonant", names_override.json's
    "below_form_overrides") keeps using each consonant's traditional combining
    form: RA -> raMatra-tutg ("Rakar", also used as a component in ligatures
    like ba_ra-tutg - the same fact generate_akhn_feature.py's TOKEN_ALIASES
    relies on), YA -> the plain "ya-tutg.below" (naive default, no override
    needed). Neither is a true miniature of its own letterform, but that's
    intentional here.
  - The SUBJOINER path (explicit "conjoiner + VS1" forced-stacking, see
    TutgSubjoinerForm in generate_akhn_feature.py and TutgBlwfSubjoiner below -
    names_override.json's "subjoiner_below_form_overrides") uses the new real
    miniatures instead: RA -> ra-tutg.below, YA -> ya-tutg.below.mini. RA's
    alt1 form is a related special case: "subjoiner_alt_below_no_dedicated_in_
    generic" keeps the GENERIC path's resolve_alt_below() falling back to
    raMatra-tutg for ra-tutg.alt1 (as it always did, since raMatra-tutg has no
    alt1 of its own) even though ra-tutg.below.alt1 now exists - that dedicated
    glyph is subjoiner-path-only, matching the plain-RA split above.

BELOW_FORM_OVERRIDES (read from names_override.json) documents any future
generic-path exception like this explicitly rather than assuming the ".below"
suffix pattern always holds.

Any consonant that turns out to have NO below-base glyph at all (neither the
".below" suffix nor a listed override) is reported in BLWF_TODO.md instead of
silently skipped or guessed at - same principle as every other gap in this
project's GSUB tooling.

blwf_decompose_ignore_list.json (added 2026-07-18): hand-maintained, like
gsub_ignore_list.json - ligature names that should NEVER get the vowel-sign
decompose fix (see below), regardless of what the automated missing-compound
check would otherwise say. E.g. ka_ssa-tutg (KSHA) - project owner confirmed it
should stay as one recognizable conjunct rather than being decomposed back to
KA+conjoiner+SSA before a vowel sign it happens to have no compound for.
"""
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "glyph_svg_data.json"), encoding="utf-8") as f:
    glyphs = json.load(f)
with open(os.path.join(HERE, "glyph_classification.json"), encoding="utf-8") as f:
    classification = json.load(f)
with open(os.path.join(HERE, "tutg_akhn_rules.json"), encoding="utf-8") as f:
    akhn_rules = json.load(f)
with open(os.path.join(HERE, "names_override.json"), encoding="utf-8") as f:
    names_override = json.load(f)
with open(os.path.join(HERE, "blwf_decompose_ignore_list.json"), encoding="utf-8") as f:
    DECOMPOSE_IGNORE = json.load(f)
with open(os.path.join(HERE, "variant_registry.json"), encoding="utf-8") as f:
    VARIANT_REGISTRY = json.load(f)


def cp_of(name):
    u = glyphs.get(name, {}).get("unicodes", [])
    return u[0] if u else None


def is_default_form(name):
    # no ".below"/".altN"/other suffix after "-tutg" - same filter
    # build_test_page_data.py uses to get the canonical 36-consonant list.
    return "-tutg" in name and "." not in name.partition("-tutg")[2]


def resolve_below_form(base_name):
    """Real hand-drawn '.below' preferred over auto-generated '.below.auto'."""
    real_below = f"{base_name}.below"
    auto_below = f"{base_name}.below.auto"
    if real_below in glyphs:
        return real_below, False
    if auto_below in glyphs:
        return auto_below, True
    return None, None


consonants = [n for n in classification.get("consonant", []) if is_default_form(n) and cp_of(n) is not None]
consonants.sort(key=cp_of)

# See module docstring - data-driven replacement for what used to be a
# hardcoded dict here.
BELOW_FORM_OVERRIDES = {
    k: v["resolves_to"] for k, v in names_override.get("below_form_overrides", {}).items()
    if not k.startswith("_")
}

# See module docstring - the SEPARATE, VS1-forced-stacking (TutgBlwfSubjoiner)
# resolution, deliberately distinct from BELOW_FORM_OVERRIDES above.
SUBJOINER_BELOW_OVERRIDES = {
    k: v["resolves_to"] for k, v in names_override.get("subjoiner_below_form_overrides", {}).items()
    if not k.startswith("_")
}
# Consonants whose GENERIC-path resolve_alt_below() should NOT prefer a newly
# added dedicated "{base}.below.altN" glyph - see module docstring (RA's alt1).
SUBJOINER_ONLY_DEDICATED_ALT = {
    k for k, v in names_override.get("subjoiner_alt_below_no_dedicated_in_generic", {}).items()
    if not k.startswith("_") and v
}

rules = []    # (input_seq, output_name) - input_seq always ["conjoiner-tutg", X]
pstf_rules = []   # (input_seq, output_name) - YA's own post-base form (see below)
rakar_rules = []  # (input_seq, output_name) - RA's own post-base form ("the Rakar form")
missing = []  # consonant_name
consonant_below = {}  # consonant name -> resolved below-form name, reused below

# YA's combining form (ya-tutg.below) and RA's (raMatra-tutg, "the Rakar form")
# are genuinely post-base forms per BELOW_BASE_MINIATURE_GLYPHS.md (different
# allographs, not below-base miniatures), not a below-base stack at all -
# confirmed 2026-07-21 by project owner. Moved from blwf's generic "conjoiner +
# consonant" fallback into their own real features instead of just being
# excluded (an earlier version of this fix tried plain exclusion - left the
# conjoiner completely unconsumed, a visible dotted-circle-style fallback
# glyph, confirmed via uharfbuzz): YA -> `pstf` (Post-base Forms), RA -> `rkrf`
# (Rakar Forms - a real, registered OpenType feature specifically for this
# exact RA-combining-form case, confirmed 2026-07-21 to apply by default and
# run before blwf, same as pstf/blws, via the same throwaway-test-font
# methodology). consonant_below is still populated for both (resolve_alt_
# below's fallback, etc. still relies on it) - only the GENERIC
# "conjoiner-tutg + X" rule itself moves feature, from `rules` to
# `pstf_rules`/`rakar_rules`.
GENERIC_FALLBACK_EXCLUDE = {"ya-tutg", "ra-tutg"}
RAKAR_EXCLUDE = {"ra-tutg"}
for name in consonants:
    below = BELOW_FORM_OVERRIDES.get(name, name + ".below")
    if below in glyphs:
        if name in RAKAR_EXCLUDE:
            target_list = rakar_rules
        elif name in GENERIC_FALLBACK_EXCLUDE:
            target_list = pstf_rules
        else:
            target_list = rules
        target_list.append((["conjoiner-tutg", name], below))
        consonant_below[name] = below
    else:
        missing.append(name)

# --- Alt-consonant fallback (added 2026-07-20, corrected 2026-07-20) ---
#
# The loop above only ever matched the PLAIN consonant name as the second
# glyph of "conjoiner-tutg + X" - a consonant already switched to one of its
# variant_registry.json .altN forms (via akhn's TutgVariantSelect) didn't
# match ANYTHING here, so a plain (non-VS) "conjoiner-tutg" preceding it was
# left completely unconsumed, rendering as the font's real dotted-circle-style
# conjoiner-tutg fallback artwork - confirmed via the Variant Registry tab's
# Consonant Variant Matrix (24x24 grid of every registered variant conjoined
# with every other): the conjoiner never disappeared in any cell.
#
# CORRECTED: the first version of this fix assumed every .altN variant reused
# the SAME below-form as its plain consonant - wrong, caught by the project
# owner. Every one of the 24 registered consonant-variant entries actually has
# its OWN dedicated, hand-drawn "{base}.below.altN" glyph (e.g.
# bha-tutg.alt1 -> bha-tutg.below.alt1, not bha-tutg.below) - confirmed by
# checking glyph_svg_data.json directly rather than assuming. resolve_alt_below()
# prefers that dedicated glyph and only falls back to the plain consonant's own
# below-form (still via consonant_below, which already applies
# BELOW_FORM_OVERRIDES - e.g. RA's raMatra-tutg) for the one case with no
# dedicated alt-below drawn at all: ra-tutg.alt1 (no raMatra-tutg.alt1 exists).
def resolve_alt_below(name, index_str, allow_dedicated=True):
    # allow_dedicated=False skips a dedicated "{base}.below.altN" for names in
    # SUBJOINER_ONLY_DEDICATED_ALT (RA's alt1) - used by the GENERIC-path call
    # site below, so that dedicated glyph stays subjoiner-path-only (see module
    # docstring).
    if allow_dedicated or name not in SUBJOINER_ONLY_DEDICATED_ALT:
        alt_below = f"{name}.below.alt{index_str}"
        if alt_below in glyphs:
            return alt_below, True
    return consonant_below.get(name), False


alt_consonant_missing = []  # (base_name, variant_name) - registered but not a real glyph
alt_consonant_no_dedicated_below = []  # (base_name, variant_name) - falls back to the plain below-form
alt_consonant_rule_count = 0
for name in consonants:
    for index_str, variant_name in sorted(VARIANT_REGISTRY.get(name, {}).items(), key=lambda kv: int(kv[0])):
        if variant_name not in glyphs:
            alt_consonant_missing.append((name, variant_name))
            continue
        below, is_dedicated = resolve_alt_below(name, index_str, allow_dedicated=False)
        if below is None:
            alt_consonant_missing.append((name, variant_name))
            continue
        if not is_dedicated:
            alt_consonant_no_dedicated_below.append((name, variant_name))
        if name in RAKAR_EXCLUDE:
            target_list = rakar_rules
        elif name in GENERIC_FALLBACK_EXCLUDE:
            target_list = pstf_rules
        else:
            target_list = rules
        target_list.append((["conjoiner-tutg", variant_name], below))
        alt_consonant_rule_count += 1

# --- TutgBlwfSubjoiner (added 2026-07-20) ---
#
# "subjoiner-tutg + CONSONANT -> CONSONANT.below" - the other half of the
# akhn-side TutgSubjoinerForm lookup (generate_akhn_feature.py), which
# collapses "conjoiner-tutg + vs3-tutg" into subjoiner-tutg. By the time this
# lookup runs, subjoiner-tutg is just an ordinary glyph, so this is a plain
# 2-glyph ligature substitution - same shape as the existing per-consonant
# fallback rule above, just keyed on subjoiner-tutg instead of conjoiner-tutg.
# Also covers every registered char-variant form of each consonant
# (variant_registry.json's "ka-tutg" -> {"1": "ka-tutg.alt1", ...}), preferring
# each one's own dedicated "{base}.below.altN" glyph via resolve_alt_below()
# (see the Alt-consonant fallback section above for why - every registered
# variant actually has its own hand-drawn below-form, not a shared one) - a
# variant selected via TutgVariantSelect just before the subjoiner must still
# shrink into ITS OWN below shape, not its plain consonant's.
#
# Declared as its own explicit lookup, but - unlike TutgBlwfDecompose - INSIDE
# feature blwf on purpose: it's meant to apply unconditionally whenever this
# exact 2-glyph sequence occurs (same as TutgBlwf's own default rules), not
# only when some other contextual rule references it, so the "declared inside
# a feature block joins its default lookup set" FEA behavior is exactly what's
# wanted here, not the bug it was for TutgBlwfDecompose. No ordering conflict
# with TutgBlwfDecompose/TutgBlwf either - those rules all start with
# "conjoiner-tutg" or a ligature glyph name, never "subjoiner-tutg", so there's
# no shared starting glyph for HarfBuzz's first-match rule order to matter.
subjoiner_rules = []          # (variant_or_plain_consonant_name, below_name)
subjoiner_missing_variant = []  # (base_name, variant_name) registered but not a real glyph
for name in consonants:
    below = SUBJOINER_BELOW_OVERRIDES.get(name, consonant_below.get(name))
    if below is None:
        continue
    subjoiner_rules.append((name, below))
    for index_str, variant_name in sorted(VARIANT_REGISTRY.get(name, {}).items(), key=lambda kv: int(kv[0])):
        if variant_name not in glyphs:
            subjoiner_missing_variant.append((name, variant_name))
            continue
        variant_below, _is_dedicated = resolve_alt_below(name, index_str, allow_dedicated=True)
        subjoiner_rules.append((variant_name, variant_below))

# Per-ligature rules: the ligature's own output glyph name, not its raw akhn
# input sequence - see module docstring for why.
#
# Covers EVERY ligature candidate (conjunct_ligature + vowel_sign_ligature,
# default forms), not just the ones generate_below_auto_glyphs.py created a
# ".below.auto" for - 9 of them (ga_uMatra-tutg, ha_ya-tutg, ja_uuMatra-tutg,
# na_uMatra-tutg, na_ya-tutg, pa_ya-tutg, sha_ya-tutg, ssa_va-tutg,
# ta_uMatra-tutg) already had real hand-drawn ".below" glyphs and were
# correctly skipped by that script - but that meant they'd been left with NO
# blwf rule at all until now. Prefer the real ".below" when one exists,
# matching BELOW_FORM_OVERRIDES's "prefer real artwork" principle for
# consonants; fall back to ".below.auto" otherwise.
akhn_outputs = {r["output"] for r in akhn_rules}
akhn_input_by_output = {r["output"]: r["input"] for r in akhn_rules}

ligature_candidates = sorted(set(
    n for n in classification.get("conjunct_ligature", []) + classification.get("vowel_sign_ligature", [])
    if is_default_form(n)
))
# YA/RA + their OWN vowel sign (e.g. ya_uMatra-tutg = "YA taking the U matra")
# - same GENERIC_FALLBACK_EXCLUDE principle as plain ya-tutg/ra-tutg above:
# this is still fundamentally "YA/RA's own shape", so it must not auto-shrink
# via the plain conjoiner path either. Only the 4 roots each (U/UU/Vocalic-R/
# Vocalic-RR), not e.g. ka_ya-tutg (a DIFFERENT consonant conjoined with YA -
# already excluded from decompose above, but its own per-ligature rule here is
# a separate "the whole ka_ya conjunct itself gets subjoined" concern, not
# "YA's own shape", so left untouched).
GENERIC_LIGATURE_FALLBACK_EXCLUDE = {
    f"{cons}_{root}-tutg" for cons in ("ya", "ra")
    for root in ("uMatra", "uuMatra", "rVocalicMatra", "rrVocalicMatra")
}
unreachable = []       # base ligature name isn't actually producible by any akhn rule
no_below_form = []     # neither a real .below nor a .below.auto exists (shouldn't happen)
below_auto_names = []  # kept for the report line below
ligature_below = {}    # ligature name -> resolved below-form name, reused by the compound rules below
for base_name in ligature_candidates:
    below_name, is_auto = resolve_below_form(base_name)
    if below_name is None:
        no_below_form.append(base_name)
        continue
    ligature_below[base_name] = below_name
    if is_auto:
        below_auto_names.append(below_name)
    if base_name not in GENERIC_LIGATURE_FALLBACK_EXCLUDE:
        rules.append((["conjoiner-tutg", base_name], below_name))
    if base_name not in akhn_outputs:
        unreachable.append(base_name)

# Subjoiner counterpart of the per-ligature rules above (added 2026-07-21,
# confirmed missing by the project owner): TutgBlwfSubjoiner previously only
# ever matched a plain consonant or one of its registered .altN variants -
# never a ligature name like ya_uMatra-tutg. Since akhn always collapses
# "ya-tutg uMatra-tutg" into ya_uMatra-tutg BEFORE blwf runs, "subjoiner-tutg +
# ya-tutg" (2 glyphs) never actually occurs in the buffer when U follows YA -
# it's really "subjoiner-tutg + ya_uMatra-tutg" (2 glyphs, the ligature as a
# single unit) by the time TutgBlwfSubjoiner's lookup sees it. Without this,
# that 2-glyph sequence matched NOTHING: subjoiner-tutg rendered unconsumed
# (its own visible fallback glyph) and ya_uMatra-tutg stayed full-size,
# unshrunk - confirmed via uharfbuzz on "conjoiner+VS1+YA+U". Reuses the same
# ligature_below resolution as the generic per-ligature rules above, so this
# fixes every consonant's _uMatra/_uuMatra/_rVocalicMatra/_rrVocalicMatra
# compound and every conjunct_ligature, not just YA/RA specifically.
subjoiner_ligature_rule_count = 0
for base_name, below_name in ligature_below.items():
    subjoiner_rules.append((base_name, below_name))
    subjoiner_ligature_rule_count += 1

# ---------------------------------------------------------------------------
# Decompose fix (added 2026-07-18) - see module docstring and
# VOWEL_SIGN_LIGATURE_GAP.md for the full reasoning.
# ---------------------------------------------------------------------------
VS_ROOTS = ["uMatra", "uuMatra", "rVocalicMatra", "rrVocalicMatra"]
VS_INPUT_GLYPH = {root: f"{root}-tutg" for root in VS_ROOTS}

# Some compounds only exist under a typo'd/aliased spelling (e.g. the real glyph
# is nya_UuMatra-tutg, not nya_uuMatra-tutg) - names_override.json already
# documents these for generate_akhn_feature.py; reuse it here so the same
# alias is recognized instead of wrongly reporting a gap that isn't real.
alt_tokens = {root: [] for root in VS_ROOTS}
for token, info in names_override["token_aliases"].items():
    resolved = info["resolves_to"]
    for root in VS_ROOTS:
        if resolved == f"{root}-tutg":
            alt_tokens[root].append(token)


def compound_glyph_name(base, root):
    """Real compound glyph name for base+root, checking known alias spellings too."""
    standard = f"{base}_{root}-tutg"
    if standard in glyphs:
        return standard
    for alt in alt_tokens[root]:
        alt_name = f"{base}_{alt}-tutg"
        if alt_name in glyphs:
            return alt_name
    return None


conjunct_ligs_default = sorted(n for n in classification.get("conjunct_ligature", []) if is_default_form(n))
consonant_bases = {n[: -len("-tutg")] for n in consonants}

decompose_rules = []         # (ligature_name, raw_input_seq, [missing_roots])
decompose_no_input_seq = []  # has missing roots but no known akhn input sequence - can't decompose
decompose_not_plain_last = []  # last "_"-token isn't a plain consonant name - see below
decompose_ignored = []       # hand-excluded via blwf_decompose_ignore_list.json
decompose_excluded_ya_ra = []  # last consonant is YA/RA - see DECOMPOSE_EXCLUDE_LAST below
# YA and RA never get decomposed this way, regardless of missing compound -
# confirmed 2026-07-21 by project owner: decomposing e.g. ka_ya-tutg (a real,
# dedicated hand-drawn ligature) back into raw ka+ya just to re-ligate ya+U
# and SHRINK it below ka throws away that dedicated artwork for no reason -
# ka_ya-tutg should stay intact, with U/UU/rVocalicMatra/rrVocalicMatra
# attaching to it directly via its own "bottomright" GPOS mark-anchor instead
# (see generate_anchors.py's BARE_YA_LIGATURES/BARE_RA_LIGATURES - added
# specifically to support this). The explicit conjoiner+VS1 forced-subjoiner
# path is unaffected - TutgBlwfSubjoiner's own per-ligature rules still apply
# there regardless of this exclusion.
DECOMPOSE_EXCLUDE_LAST = {"ya", "ra"}
for lig in conjunct_ligs_default:
    if lig in DECOMPOSE_IGNORE:
        decompose_ignored.append(lig)
        continue
    base = lig[: -len("-tutg")]
    # The last underscore-token must be a PLAIN consonant name for the
    # last_consonant/needed_pairs logic further down to make sense. Some
    # "conjunct_ligature"-classified names don't qualify: Chillu-suffixed
    # compounds (ka_kChillu-tutg - a real conjunct, but ".split('_')[-1]"
    # gives "kChillu", not a real consonant, and decomposing a Looped-Virama-
    # terminated consonant before a further vowel sign is semantically odd
    # anyway), names that are ACTUALLY a vowel-sign compound misclassified as
    # conjunct_ligature (e.g. sa_ka_vocalicR-tutg, nya_UuMatra-tutg - the
    # classifier didn't recognize the aliased vowel-sign token, but these
    # already have their vowel sign, nothing to fix), and one known trailing-
    # underscore typo (na_ta_ra_ya_-tutg, giving an empty last token). Skipped
    # and reported rather than silently generating a wrong rule.
    last_token = base.split("_")[-1]
    if last_token not in consonant_bases:
        decompose_not_plain_last.append(lig)
        continue
    if last_token in DECOMPOSE_EXCLUDE_LAST:
        decompose_excluded_ya_ra.append(lig)
        continue
    missing_roots = [root for root in VS_ROOTS if compound_glyph_name(base, root) is None]
    if not missing_roots:
        continue
    raw_seq = akhn_input_by_output.get(lig)
    if raw_seq is None:
        decompose_no_input_seq.append(lig)
        continue
    decompose_rules.append((lig, raw_seq, missing_roots))

# Group ligatures by identical missing-root set, so the contextual trigger is
# written as one glyph-class line per group instead of one line per ligature.
trigger_groups = defaultdict(list)  # tuple(sorted(missing_roots)) -> [ligature names]
for lig, raw_seq, missing_roots in decompose_rules:
    trigger_groups[tuple(sorted(missing_roots))].append(lig)

# The new 3-glyph re-ligate-and-shrink rules: one per distinct (last consonant,
# missing root) pair actually needed by the decompose set above - not all
# 36*4, only the combinations that can actually occur once decomposed.
needed_pairs = set()
for lig, raw_seq, missing_roots in decompose_rules:
    last_consonant = lig[: -len("-tutg")].split("_")[-1] + "-tutg"
    for root in missing_roots:
        needed_pairs.add((last_consonant, root))

compound_rules = []    # (input_seq, output_name) - input_seq is 3 glyphs
compound_no_glyph = []  # (consonant, root) with no compound glyph at all - shouldn't happen
compound_no_below = []  # compound glyph exists but has no below-form at all - shouldn't happen
for consonant, root in sorted(needed_pairs):
    base = consonant[: -len("-tutg")]
    compound_name = compound_glyph_name(base, root)
    if compound_name is None:
        compound_no_glyph.append((consonant, root))
        continue
    below_name = ligature_below.get(compound_name)
    if below_name is None:
        below_name, _ = resolve_below_form(compound_name)
        if below_name is None:
            compound_no_below.append((consonant, root))
            continue
    compound_rules.append((["conjoiner-tutg", consonant, VS_INPUT_GLYPH[root]], below_name))

# Subjoiner counterpart of compound_rules above (added 2026-07-22, second
# regression found by the project owner): the per-ligature TutgBlwfSubjoiner
# rules further up ("subjoiner-tutg + ya_uMatra-tutg -> ...") assumed the
# consonant+vowel-sign compound (ya_uMatra-tutg etc.) would already exist in
# the buffer by the time this lookup runs - true back when that merge lived
# in akhn, but now that it's been moved to blws (see generate_akhn_feature.py/
# tutg_blws.fea), confirmed via uharfbuzz that blws does NOT reliably run
# before TutgBlwfSubjoiner for this sequence: "subjoiner-tutg + ka-tutg"
# (the plain 2-glyph rule) matches first, shrinking the bare consonant alone
# and leaving the vowel sign stranded as its own unattached glyph - reproduced
# with "GHA+conjoiner+VS1+KA+uMatra", not just YA/RA, so this covers every
# consonant, not only the "needed_pairs" subset compound_rules above targets.
# Unlike compound_rules (only built for the specific pairs decompose_rules
# actually needs), this is unconditional over all 36 consonants x 4 roots -
# every consonant that HAS a compound glyph for a given root gets a rule here.
subjoiner_compound_rules = []    # (input_seq, output_name) - input_seq is 3 glyphs
subjoiner_compound_no_below = []  # (consonant, root) - compound glyph exists but no below-form
for consonant in consonants:
    base = consonant[: -len("-tutg")]
    for root in VS_ROOTS:
        compound_name = compound_glyph_name(base, root)
        if compound_name is None:
            continue  # no such compound glyph at all - nothing to fix here
        below_name = ligature_below.get(compound_name)
        if below_name is None:
            below_name, _ = resolve_below_form(compound_name)
            if below_name is None:
                subjoiner_compound_no_below.append((consonant, root))
                continue
        subjoiner_compound_rules.append((["subjoiner-tutg", consonant, VS_INPUT_GLYPH[root]], below_name))

# Alt-aware counterpart of subjoiner_compound_rules above (added 2026-07-24 -
# project owner: confirmed forcing the below-base subjoin path on an
# alt-selected compound, e.g. typing "conjoiner+VS1+KA+U+VS11" to select
# ka_uMatra-tutg.alt1 while ALSO forcing it below-base, silently fell back to
# shrinking the DEFAULT compound's miniature instead - VS11 had nothing left
# to attach its substitution to by the time this lookup ran, since the
# 3-glyph rule above already matched and consumed "subjoiner-tutg + KA + U"
# on its own). Fixed with a longer, MORE SPECIFIC 4-glyph rule per registered
# alt: "subjoiner-tutg + consonant + root + vsN-tutg -> that alt's OWN
# below-form" - same "longest match must be listed first" principle as
# compound_rules/subjoiner_compound_rules themselves. vsN uses
# CONJUNCT_VS_OFFSET (10) + the registry index, matching
# generate_akhn_feature.py's TutgConjunctVariantSelect convention exactly
# (index "1" -> VS11, "2" -> VS12) - duplicated here rather than imported,
# same reasoning as VS_ROOTS/VS_INPUT_GLYPH above (this project's scripts
# don't import from each other).
CONJUNCT_VS_OFFSET = 10
subjoiner_compound_alt_rules = []  # (input_seq, output_name) - input_seq is 4 glyphs
subjoiner_compound_alt_no_below = []  # (consonant, root, alt_name) - alt exists but no below-form
for consonant in consonants:
    base = consonant[: -len("-tutg")]
    for root in VS_ROOTS:
        compound_name = compound_glyph_name(base, root)
        if compound_name is None:
            continue
        alt_variants = VARIANT_REGISTRY.get("_ligature_variants", {}).get(compound_name, {})
        for index_str, alt_name in sorted(alt_variants.items(), key=lambda kv: int(kv[0])):
            if alt_name not in glyphs:
                continue
            alt_below_name, _ = resolve_below_form(alt_name)
            if alt_below_name is None:
                subjoiner_compound_alt_no_below.append((consonant, root, alt_name))
                continue
            vs_glyph = f"vs{CONJUNCT_VS_OFFSET + int(index_str)}-tutg"
            subjoiner_compound_alt_rules.append(
                (["subjoiner-tutg", consonant, VS_INPUT_GLYPH[root], vs_glyph], alt_below_name)
            )

# Longest sequence first within TutgBlwfSubjoiner's own rule set (4-glyph alt
# rules, then 3-glyph compound rules, then whatever's left) - alphabetical by
# output name as a stable tiebreaker within each length, so re-runs produce
# byte-identical output. compound_rules (blwf's own conjoiner-triggered
# rules, a different lookup) keeps its own separate sort.
compound_rules.sort(key=lambda r: r[1])
subjoiner_compound_alt_rules.sort(key=lambda r: (-len(r[0]), r[1]))
subjoiner_compound_rules.sort(key=lambda r: (-len(r[0]), r[1]))
rules.sort(key=lambda r: r[1])

out_path = os.path.join(HERE, "tutg_blwf.fea")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("# Auto-generated by generate_blwf_feature.py - below-base form fallback for\n")
    f.write("# the Tulu-Tigalari (tutg) script. See the module docstring for the full\n")
    f.write("# picture: TutgBlwfDecompose fixes up conjunct ligatures followed by a\n")
    f.write("# vowel sign they have no dedicated compound for; TutgBlwf covers\n")
    f.write("# \"conjoiner + consonant + vowel sign\" (new), \"conjoiner + <akhn ligature\n")
    f.write("# glyph>\", and \"conjoiner + consonant\" (original) falling through from akhn.\n")
    f.write("# Review before merging into the real features.fea (which still has\n")
    f.write("# unrelated Latin kerning/numeral features and a dead Malayalam scaffold\n")
    f.write("# that should be removed separately).\n\n")

    f.write("languagesystem DFLT dflt;\n")
    f.write("languagesystem tutg dflt;\n\n")

    # CRITICAL, found the hard way (2026-07-18): TutgBlwfDecompose must be
    # declared OUTSIDE the "feature blwf { ... }" block, not inside it. A
    # lookup block declared directly inside a feature is automatically added
    # to that feature's own default lookup list in FEA semantics, REGARDLESS
    # of whether any contextual "sub X' lookup NAME Y;" rule references it
    # elsewhere - so with it declared inside, blwf was applying the decompose
    # substitution unconditionally on every matching conjunct ligature, not
    # just when followed by a vowel sign. Confirmed via uharfbuzz: even
    # "DA+conjoiner+DA" (no vowel sign at all) broke - akhn correctly formed
    # da_da-tutg, but blwf's own (unconditionally-applied) decompose lookup
    # immediately undid it back to raw DA+conjoiner+DA, which its per-consonant
    # fallback then shrank into two separate below-forms. Declaring the lookup
    # here, before any "feature" block, means it's ONLY ever invoked by the
    # explicit chain-context trigger lines inside the feature body below.
    if decompose_rules:
        f.write("lookup TutgBlwfDecompose {\n")
        for lig, raw_seq, _missing_roots in decompose_rules:
            f.write(f"    sub {lig} by {' '.join(raw_seq)};\n")
        f.write("} TutgBlwfDecompose;\n\n")

    f.write("feature blwf {\n")
    f.write("    script tutg;\n")

    f.write("    lookup TutgBlwfSubjoiner {\n")
    f.write("        # subjoiner-tutg + consonant + vowel-sign root + vsN-tutg -> that\n")
    f.write("        # registered ALT's own below-form (4-glyph, must come first - see\n")
    f.write("        # subjoiner_compound_alt_rules comment above for why this exists at all).\n")
    for seq, out in subjoiner_compound_alt_rules:
        f.write(f"        sub {' '.join(seq)} by {out};\n")
    f.write("        # subjoiner-tutg (conjoiner + VS1, formed in akhn) + consonant + vowel-sign\n")
    f.write("        # root -> that compound's own below-form (3-glyph - see\n")
    f.write("        # subjoiner_compound_rules comment above for why this exists at all).\n")
    for seq, out in subjoiner_compound_rules:
        f.write(f"        sub {' '.join(seq)} by {out};\n")
    f.write("        # subjoiner-tutg + consonant -> consonant's below-form.\n")
    for name, below in subjoiner_rules:
        f.write(f"        sub subjoiner-tutg {name} by {below};\n")
    f.write("    } TutgBlwfSubjoiner;\n\n")

    if decompose_rules:
        for missing_key in sorted(trigger_groups):
            ligs = sorted(trigger_groups[missing_key])
            lig_class = " ".join(ligs)
            vs_class = " ".join(VS_INPUT_GLYPH[root] for root in missing_key)
            f.write(f"    sub [{lig_class}]' lookup TutgBlwfDecompose [{vs_class}];\n")
        f.write("\n")

    f.write("    lookup TutgBlwf {\n")
    for seq, out in compound_rules:
        f.write(f"        sub {' '.join(seq)} by {out};\n")
    for seq, out in rules:
        f.write(f"        sub {' '.join(seq)} by {out};\n")
    f.write("    } TutgBlwf;\n")
    f.write("} blwf;\n")

    if missing:
        f.write("\n# --- No below-base glyph found for these consonants (see BLWF_TODO.md) ---\n")
        for name in missing:
            f.write(f"# {name}\n")

    if unreachable:
        f.write("\n# --- Ligature below-base rules whose base ligature isn't producible by any akhn rule (see BLWF_TODO.md) ---\n")
        for name in unreachable:
            f.write(f"# {name}\n")

    if no_below_form:
        f.write("\n# --- Ligature candidates with no below-base glyph at all, real or auto (see BLWF_TODO.md) ---\n")
        for name in no_below_form:
            f.write(f"# {name}\n")

    if decompose_ignored:
        f.write("\n# --- Ligatures hand-excluded from the decompose fix via blwf_decompose_ignore_list.json (see BLWF_TODO.md) ---\n")
        for name in decompose_ignored:
            f.write(f"# {name}: {DECOMPOSE_IGNORE[name]}\n")

    if decompose_not_plain_last:
        f.write("\n# --- Ligatures skipped from the decompose fix: last component isn't a plain consonant (see BLWF_TODO.md) ---\n")
        for name in decompose_not_plain_last:
            f.write(f"# {name}\n")

    if decompose_excluded_ya_ra:
        f.write("\n# --- Ligatures excluded from the decompose fix: last component is YA/RA (see BLWF_TODO.md) ---\n")
        for name in decompose_excluded_ya_ra:
            f.write(f"# {name}\n")

    if decompose_no_input_seq:
        f.write("\n# --- Ligatures needing decompose but with no known akhn input sequence (see BLWF_TODO.md) ---\n")
        for name in decompose_no_input_seq:
            f.write(f"# {name}\n")

    if compound_no_glyph:
        f.write("\n# --- (consonant, vowel-sign root) pairs needed but with no compound glyph at all (see BLWF_TODO.md) ---\n")
        for consonant, root in compound_no_glyph:
            f.write(f"# {consonant} + {root}\n")

    if compound_no_below:
        f.write("\n# --- (consonant, vowel-sign root) compound glyphs with no below-form at all (see BLWF_TODO.md) ---\n")
        for consonant, root in compound_no_below:
            f.write(f"# {consonant} + {root}\n")

    if subjoiner_compound_no_below:
        f.write("\n# --- TutgBlwfSubjoiner: (consonant, vowel-sign root) compound glyphs with no below-form at all (see BLWF_TODO.md) ---\n")
        for consonant, root in subjoiner_compound_no_below:
            f.write(f"# {consonant} + {root}\n")

    if subjoiner_compound_alt_no_below:
        f.write("\n# --- TutgBlwfSubjoiner: registered alt compound with no below-form at all (see BLWF_TODO.md) ---\n")
        for consonant, root, alt_name in subjoiner_compound_alt_no_below:
            f.write(f"# {consonant} + {root} -> {alt_name}\n")

    if subjoiner_missing_variant:
        f.write("\n# --- TutgBlwfSubjoiner: variant_registry.json entry skipped, not a real glyph ---\n")
        for name, variant_name in subjoiner_missing_variant:
            f.write(f"# {name} -> {variant_name}\n")

    if alt_consonant_missing:
        f.write("\n# --- Alt-consonant fallback: variant_registry.json entry skipped, not a real glyph ---\n")
        for name, variant_name in alt_consonant_missing:
            f.write(f"# {name} -> {variant_name}\n")

    if alt_consonant_no_dedicated_below:
        f.write("\n# --- Alt-consonant fallback: no dedicated {base}.below.altN glyph, reused the plain consonant's below-form ---\n")
        for name, variant_name in alt_consonant_no_dedicated_below:
            f.write(f"# {name} -> {variant_name}\n")

# --- feature pstf (added 2026-07-21) - own file, own merge step, matching this
# project's one-script-per-feature convention, even though pstf_rules is
# computed as part of this same script's consonant-below-form resolution. YA's
# own post-base combining form (ya-tutg.below) - moved out of blwf's generic
# fallback per project owner direction 2026-07-21 (see GENERIC_FALLBACK_EXCLUDE
# above): a genuinely different allograph, not a below-base miniature
# (BELOW_BASE_MINIATURE_GLYPHS.md), so it belongs in Post-base Forms, not
# Below-base Forms. See tutg_rkrf.fea for RA's own equivalent (a real,
# registered OpenType feature specifically for this - Rakar Forms - rather
# than reusing pstf for both).
pstf_path = os.path.join(HERE, "tutg_pstf.fea")
with open(pstf_path, "w", encoding="utf-8") as f:
    f.write("# Auto-generated by generate_blwf_feature.py - YA's own post-base combining\n")
    f.write("# form for the Tulu-Tigalari (tutg) script, split out of blwf's generic\n")
    f.write("# below-base fallback 2026-07-21 (see BELOW_BASE_MINIATURE_GLYPHS.md -\n")
    f.write("# ya-tutg.below is a genuinely different allograph, not a below-base\n")
    f.write("# miniature). Review before merging into the real features.fea.\n\n")

    f.write("languagesystem DFLT dflt;\n")
    f.write("languagesystem tutg dflt;\n\n")

    f.write("feature pstf {\n")
    f.write("    script tutg;\n")
    f.write("    lookup TutgPstf {\n")
    for seq, out in pstf_rules:
        f.write(f"        sub {' '.join(seq)} by {out};\n")
    f.write("    } TutgPstf;\n")
    f.write("} pstf;\n")

# --- feature rkrf (added 2026-07-21) - RA's own post-base "Rakar" combining
# form (raMatra-tutg). Rakar Forms is a real, registered OpenType feature tag
# for exactly this - RA's special combining form - confirmed 2026-07-21 (via
# a throwaway test font, same methodology as blws/pstf) to apply by default
# and run before blwf, same early stage as pstf/blws.
rkrf_path = os.path.join(HERE, "tutg_rkrf.fea")
with open(rkrf_path, "w", encoding="utf-8") as f:
    f.write("# Auto-generated by generate_blwf_feature.py - RA's own post-base \"Rakar\"\n")
    f.write("# combining form for the Tulu-Tigalari (tutg) script, split out of blwf's\n")
    f.write("# generic below-base fallback 2026-07-21 (see BELOW_BASE_MINIATURE_GLYPHS.md -\n")
    f.write("# raMatra-tutg is a genuinely different allograph, not a below-base\n")
    f.write("# miniature). Review before merging into the real features.fea.\n\n")

    f.write("languagesystem DFLT dflt;\n")
    f.write("languagesystem tutg dflt;\n\n")

    f.write("feature rkrf {\n")
    f.write("    script tutg;\n")
    f.write("    lookup TutgRakar {\n")
    for seq, out in rakar_rules:
        f.write(f"        sub {' '.join(seq)} by {out};\n")
    f.write("    } TutgRakar;\n")
    f.write("} rkrf;\n")

# markdown report - written even when nothing is missing, so a re-run's "all clear"
# is an explicit, checkable fact rather than the mere absence of a file.
report_path = os.path.join(HERE, "BLWF_TODO.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("# blwf (Below-base Forms) coverage report\n\n")
    f.write(f"Generated by `generate_blwf_feature.py` against {len(consonants)} consonants, ")
    f.write(f"{len(ligature_candidates)} ligature candidates ({len(below_auto_names)} using an ")
    f.write(f"auto `.below.auto`), and {len(decompose_rules)} conjunct ligatures needing the ")
    f.write("vowel-sign decompose fix.\n\n")

    if missing:
        f.write(f"## {len(missing)} consonant(s) with no below-base glyph\n\n")
        f.write("Neither a `{name}.below` glyph nor an entry in `BELOW_FORM_OVERRIDES` was found, so\n")
        f.write("`blwf` has no fallback rule for these - conjuncts ending in them will render\n")
        f.write("unjoined unless an `akhn` ligature already covers that specific pair.\n\n")
        for name in missing:
            f.write(f"- `{name}`\n")
    else:
        f.write("**All clear** - every one of the 36 consonants has a below-base glyph "
                "(35 via the `{name}.below` naming convention, RA via the `raMatra-tutg` "
                "override), so `blwf` has a fallback rule for every possible conjunct.\n")
    f.write("\n")

    if unreachable:
        f.write(f"## {len(unreachable)} ligature below-base rule(s) whose base ligature akhn can never actually produce\n\n")
        f.write("A `blwf` rule was still written for these (harmless - it references two real\n")
        f.write("glyphs), but it's effectively dead code: the base ligature glyph itself isn't\n")
        f.write("a real output of any `akhn` rule (e.g. `ka_iMatra_dotreph-tutg` - a compound\n")
        f.write("whose name doesn't cleanly decompose, already flagged in GSUB_TODO.md's\n")
        f.write("skipped/unparsed list), so the glyph this `blwf` rule looks for never actually\n")
        f.write("appears in a real shaped glyph stream.\n\n")
        for name in unreachable:
            f.write(f"- `{name}`\n")
    else:
        f.write("**All clear** - every ligature below-base rule's base ligature is a real akhn "
                "output, so every one is actually reachable.\n")
    f.write("\n")

    if no_below_form:
        f.write(f"## {len(no_below_form)} ligature(s) with no below-base glyph at all\n\n")
        f.write("Neither a real `.below` nor an auto-generated `.below.auto` exists - shouldn't\n")
        f.write("happen given generate_below_auto_glyphs.py creates one for every ligature that\n")
        f.write("doesn't already have a real `.below`, but reported here rather than assumed.\n\n")
        for name in no_below_form:
            f.write(f"- `{name}`\n")
    else:
        f.write("**All clear** - every ligature candidate has a below-base glyph, real or auto.\n")
    f.write("\n")

    f.write(f"## Vowel-sign decompose fix ({len(decompose_rules)} conjunct ligatures)\n\n")
    f.write("See `VOWEL_SIGN_LIGATURE_GAP.md` for the full writeup. Grouped by identical "
            "missing-vowel-sign set (one contextual trigger line per group):\n\n")
    for missing_key in sorted(trigger_groups):
        ligs = sorted(trigger_groups[missing_key])
        f.write(f"- Missing `{'`, `'.join(missing_key)}` ({len(ligs)} ligatures): "
                f"`{'`, `'.join(ligs[:8])}`{', ...' if len(ligs) > 8 else ''}\n")
    f.write(f"\n{len(needed_pairs)} distinct (consonant, vowel-sign) re-ligate-and-shrink "
            "rules generated to support these.\n")
    f.write("\n")

    if decompose_ignored:
        f.write(f"## {len(decompose_ignored)} ligature(s) hand-excluded from the decompose fix\n\n")
        f.write("Via `blwf_decompose_ignore_list.json` - overrides whatever the automated "
                "missing-compound check would otherwise say:\n\n")
        for name in decompose_ignored:
            f.write(f"- `{name}`: {DECOMPOSE_IGNORE[name]}\n")
        f.write("\n")

    if decompose_not_plain_last:
        f.write(f"## {len(decompose_not_plain_last)} ligature(s) skipped from the decompose fix: last component isn't a plain consonant\n\n")
        f.write("Chillu-suffixed compounds (e.g. `ka_kChillu-tutg`), names that are actually a\n")
        f.write("vowel-sign compound misclassified as `conjunct_ligature` (e.g. `nya_UuMatra-tutg`,\n")
        f.write("`sa_ka_vocalicR-tutg` - already have their vowel sign, nothing to fix), and one\n")
        f.write("known trailing-underscore typo (`na_ta_ra_ya_-tutg`). Skipped rather than\n")
        f.write("guessed at, same principle as every other gap in this project's GSUB tooling.\n\n")
        for name in decompose_not_plain_last:
            f.write(f"- `{name}`\n")
        f.write("\n")

    if decompose_excluded_ya_ra:
        f.write(f"## {len(decompose_excluded_ya_ra)} ligature(s) excluded from the decompose fix: last component is YA/RA\n\n")
        f.write("Confirmed 2026-07-21 by project owner: decomposing e.g. `ka_ya-tutg` (a real, "
                "dedicated hand-drawn ligature) back into raw ka+ya just to re-ligate ya+U and "
                "shrink it below ka throws away that dedicated artwork for no reason. These stay "
                "intact instead, with U/UU/rVocalicMatra/rrVocalicMatra attaching directly via "
                "their own `bottomright` GPOS mark-anchor (see generate_anchors.py's "
                "BARE_YA_LIGATURES/BARE_RA_LIGATURES). The explicit conjoiner+VS1 forced-subjoiner "
                "path is unaffected - TutgBlwfSubjoiner's own per-ligature rules still apply there.\n\n")
        for name in decompose_excluded_ya_ra:
            f.write(f"- `{name}`\n")
        f.write("\n")

    if decompose_no_input_seq:
        f.write(f"## {len(decompose_no_input_seq)} ligature(s) needing decompose but with no known akhn input sequence\n\n")
        for name in decompose_no_input_seq:
            f.write(f"- `{name}`\n")
        f.write("\n")

    if compound_no_glyph:
        f.write(f"## {len(compound_no_glyph)} (consonant, vowel-sign) pair(s) needed but with no compound glyph at all\n\n")
        for consonant, root in compound_no_glyph:
            f.write(f"- `{consonant}` + `{root}`\n")
        f.write("\n")

    if compound_no_below:
        f.write(f"## {len(compound_no_below)} compound glyph(s) needed but with no below-form at all\n\n")
        for consonant, root in compound_no_below:
            f.write(f"- `{consonant}` + `{root}`\n")
        f.write("\n")

    if not (decompose_not_plain_last or decompose_no_input_seq or compound_no_glyph or compound_no_below):
        f.write("**All clear** - every ligature needing the decompose fix has a known akhn "
                "input sequence, and every (consonant, vowel-sign) pair it needs has both a "
                "compound glyph and a below-form for it.\n")

print(f"Consonants checked: {len(consonants)}")
print(f"Ligature candidates checked: {len(ligature_candidates)}")
print(f"  - using a real .below: {len(ligature_candidates) - len(below_auto_names) - len(no_below_form)}")
print(f"  - using an auto .below.auto: {len(below_auto_names)}")
print(f"Conjunct ligatures needing vowel-sign decompose: {len(decompose_rules)}")
print(f"Trigger groups (by missing-root set): {len(trigger_groups)}")
print(f"Distinct (consonant, vowel-sign) compound rules: {len(compound_rules)}")
print(f"Rules written: {len(compound_rules) + len(rules)} ({len(compound_rules)} compound + {len(rules)} plain)")
print(f"Missing below-base glyph (consonants): {len(missing)} {missing}")
print(f"No below-base glyph at all (ligatures): {len(no_below_form)} {no_below_form}")
print(f"Unreachable (base ligature not a real akhn output): {len(unreachable)} {unreachable}")
print(f"Decompose hand-excluded (blwf_decompose_ignore_list.json): {len(decompose_ignored)} {decompose_ignored}")
print(f"Decompose skipped (last component not a plain consonant): {len(decompose_not_plain_last)} {decompose_not_plain_last}")
print(f"Decompose excluded (last component is YA/RA): {len(decompose_excluded_ya_ra)} {decompose_excluded_ya_ra}")
print(f"Decompose ligatures with no known akhn input sequence: {len(decompose_no_input_seq)} {decompose_no_input_seq}")
print(f"Needed compound pairs with no glyph at all: {len(compound_no_glyph)} {compound_no_glyph}")
print(f"Needed compound pairs with no below-form: {len(compound_no_below)} {compound_no_below}")
print(f"TutgBlwfSubjoiner rules: {len(subjoiner_rules)} (including {subjoiner_ligature_rule_count} per-ligature)")
print(f"TutgBlwfSubjoiner compound rules: {len(subjoiner_compound_rules)}, no-below: {len(subjoiner_compound_no_below)} {subjoiner_compound_no_below}")
print(f"TutgBlwfSubjoiner compound ALT rules: {len(subjoiner_compound_alt_rules)}, no-below: {len(subjoiner_compound_alt_no_below)} {subjoiner_compound_alt_no_below}")
print(f"TutgBlwfSubjoiner variant entries skipped (not a real glyph): {len(subjoiner_missing_variant)} {subjoiner_missing_variant}")
print(f"Alt-consonant fallback rules added to TutgBlwf: {alt_consonant_rule_count}")
print(f"Alt-consonant fallback entries skipped (not a real glyph): {len(alt_consonant_missing)} {alt_consonant_missing}")
print(f"Alt-consonant fallback entries with no dedicated below.altN (reused plain below): {len(alt_consonant_no_dedicated_below)} {alt_consonant_no_dedicated_below}")
print(f"Pstf rules (TutgPstf): {len(pstf_rules)}")
print(f"Rkrf rules (TutgRakar): {len(rakar_rules)}")
print("Written to:", out_path)
print("Written to:", pstf_path)
print("Written to:", rkrf_path)
print("Written to:", report_path)
