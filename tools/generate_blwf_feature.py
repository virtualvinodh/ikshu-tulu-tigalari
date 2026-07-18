"""
Builds a ready-to-merge .fea file for the `blwf` (Below-base Forms) feature.

Three kinds of rule now, in two lookups:

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
ka-tutg -> ka-tutg.below), EXCEPT for RA: its below-base combining form is a
completely different glyph, "raMatra-tutg" (used as a component in ligatures like
ba_ra-tutg) - the same fact generate_akhn_feature.py's TOKEN_ALIASES already
relies on. BELOW_FORM_OVERRIDES documents that one exception explicitly rather
than assuming the ".below" suffix pattern always holds.

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

# RA's below-base combining form is a different glyph entirely, not "ra-tutg.below"
# (which doesn't exist) - see module docstring.
BELOW_FORM_OVERRIDES = {"ra-tutg": "raMatra-tutg"}

rules = []    # (input_seq, output_name) - input_seq always ["conjoiner-tutg", X]
missing = []  # consonant_name

for name in consonants:
    below = BELOW_FORM_OVERRIDES.get(name, name + ".below")
    if below in glyphs:
        rules.append((["conjoiner-tutg", name], below))
    else:
        missing.append(name)

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
    rules.append((["conjoiner-tutg", base_name], below_name))
    if base_name not in akhn_outputs:
        unreachable.append(base_name)

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

# 3-glyph compound rules first (see module docstring for why), then the
# existing 2-glyph rules - alphabetical by output name within each group as a
# stable tiebreaker so re-runs produce byte-identical output.
compound_rules.sort(key=lambda r: r[1])
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
print(f"Decompose ligatures with no known akhn input sequence: {len(decompose_no_input_seq)} {decompose_no_input_seq}")
print(f"Needed compound pairs with no glyph at all: {len(compound_no_glyph)} {compound_no_glyph}")
print(f"Needed compound pairs with no below-form: {len(compound_no_below)} {compound_no_below}")
print("Written to:", out_path)
print("Written to:", report_path)
