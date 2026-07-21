"""
Builds a ready-to-merge .fea file containing every conjunct ligature, vowel-sign
ligature, and combined conjunct+vowel-sign ligature (all three fall out of the same
underscore-splitting logic - a name like "sa_ta_uMatra-tutg" naturally produces
"sub sa-tutg conjoiner-tutg ta-tutg uMatra-tutg by sa_ta_uMatra-tutg;" without any
special-casing), wrapped in a single `feature akhn { script tutg; ... }` block.

Critical detail: rules are sorted by DESCENDING input-sequence length before being
written. Within a GSUB ligature-substitution lookup, HarfBuzz (and most shapers)
tries each rule for a given starting glyph in listed order and commits to the FIRST
match - it does not search for the longest possible match on its own. If a 2-glyph
rule like "KA + CONJOINER + SSA" were listed before the 4-glyph
"KA + CONJOINER + SSA + CONJOINER + NNA + CONJOINER + YA", the shorter one would win
and the longer, more specific conjunct could never form. Longest-first ordering is
what makes the more specific match take priority.

Same exclusions as generate_gsub_rules.py (glyphs that don't cleanly decompose, or
are flagged in gsub_ignore_list.json) are skipped here too, for the same reasons -
see GSUB_TODO.md.

Repha handling (added 2026-07-17): the expected typed input for repha is Tulu-
Tigalari's own encoded REPHA character (U+113D1, cmap'd to repha-tutg), not "RA +
conjoiner". A hand-written rule (REPHA_FIRST_RULE) unconditionally upgrades that
typed repha-tutg into its ligating variant repha-tutg.alt1 (the proposal's
recommended default shape). This lives in its OWN lookup (TutgRephaUpgrade),
applied as a separate pass BEFORE the main TutgAkhand lookup - not just as the
first rule inside TutgAkhand - because a single GSUB lookup only substitutes once
per starting position per pass and won't re-examine a glyph it just substituted,
so the ra_X-tutg ligature rules (keyed on repha-tutg.alt1) would never see a
repha-tutg it had just converted in that same pass. Every ra_X-tutg ligature's own
auto-generated rule (built by build_input_sequence()) matches on repha-tutg.alt1 +
X accordingly, even though the glyph's *name* starts with "ra" - see that
function's docstring for the full reasoning and why RA+own-vowel-sign ligatures
like ra_uMatra-tutg are excluded from this.

Variation-selector variants (added 2026-07-20): two more lookups, TutgVariantSelect
and TutgSubjoinerForm, run before TutgRephaUpgrade/TutgAkhand - see their own
comments below for what each does and why they're both first. Chose real lookups
inside `akhn` over a separate `rlig`-tagged feature or a cmap format 14 hack:
`rlig` isn't part of the fixed feature set Indic/USE shapers actually apply by
default, so it silently does nothing in real applications; `akhn`, by contrast,
is already relied on for everything else in this font.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "glyph_classification.json"), encoding="utf-8") as f:
    d = json.load(f)
with open(os.path.join(HERE, "gsub_ignore_list.json"), encoding="utf-8") as f:
    IGNORE = json.load(f)
with open(os.path.join(HERE, "names_override.json"), encoding="utf-8") as f:
    NAMES_OVERRIDE = json.load(f)
with open(os.path.join(HERE, "variant_registry.json"), encoding="utf-8") as f:
    VARIANT_REGISTRY = json.load(f)

CONSONANTS = {"ka", "kha", "ga", "gha", "nga", "ca", "cha", "ja", "jha", "nya", "tta", "ttha", "dda", "ddha", "nna",
              "ta", "tha", "da", "dha", "na", "pa", "pha", "ba", "bha", "ma", "ya", "ra", "la", "va", "sha", "ssa",
              "sa", "ha", "lla", "rra", "llla", "nnna"}
VOWEL_SIGN_ROOTS = {"aaMatra", "iMatra", "iiMatra", "uMatra", "uuMatra", "rVocalicMatra", "rrVocalicMatra",
                    "lVocalicMatra", "llVocalicMatra", "eeMatra", "aiMatra", "ooMatra", "auMatra"}
# "dotreph" removed 2026-07-16: neither "dotreph-tutg" nor "dotrepha-tutg" actually
# exist in the font. The one glyph that used to match via this token,
# ka_iMatra_dotreph-tutg, is a Repha-involving compound built from
# ka-tutg + repha-tutg.alt1 + iiMatra-tutg - it doesn't even match its own name
# cleanly (says "iMatra", uses iiMatra) - same family as the other Repha/Virama
# compounds already flagged as needing a hand-written rule, not auto-generation.
# Having "dotreph" in this set was a bug: it let the parser "succeed" and emit a
# rule referencing a glyph that doesn't exist, instead of correctly bailing out.

# Every non-standard/typo/shorthand glyph-name token this generator has to
# special-case lives in names_override.json now, not inline here - see its
# "_readme" for why (short version: it's built so a manual glyph rename to the
# standard form keeps working without editing this file again).
TOKEN_ALIASES = {
    token: (info["resolves_to"], info["kind"])
    for token, info in NAMES_OVERRIDE["token_aliases"].items()
}
CHILLU_ABBREV = {
    abbrev: info["resolves_to"]
    for abbrev, info in NAMES_OVERRIDE["chillu_abbreviations"].items()
    if not abbrev.startswith("_")
}


def split_name(glyph_name):
    if "-tutg" not in glyph_name:
        return None
    core, _, suffix = glyph_name.partition("-tutg")
    suffix_tags = [t for t in suffix.split(".") if t]
    core = core.replace("_tall", "")
    # a stray trailing "_" (e.g. "na_ta_ra_ya_-tutg", confirmed 2026-07-16 as a typo,
    # not a real empty component) splits into a trailing "" - drop empty parts rather
    # than let them fail the whole name.
    parts = [p for p in core.split("_") if p]
    resolved = []
    for p in parts:
        if p in CONSONANTS or p in VOWEL_SIGN_ROOTS:
            resolved.append((p + "-tutg", "consonant" if p in CONSONANTS else "vowelsign"))
        elif p in TOKEN_ALIASES:
            resolved.append(TOKEN_ALIASES[p])
        elif p.endswith("Chillu") and p[:-len("Chillu")] in CHILLU_ABBREV:
            consonant = CHILLU_ABBREV[p[: -len("Chillu")]]
            resolved.append((consonant + "-tutg", "consonant"))
            resolved.append(("loopedvirama-tutg", "mark"))
        else:
            return None
    return resolved, suffix_tags


# names_override.json's "ligature_alt_overrides" (added 2026-07-21): a small,
# explicitly per-glyph table for the rare ligature ".altN" glyph that is really
# "one specific component's own registered alt substituted in" (confirmed per
# entry - by visual inspection, or by the glyph's own component structure - not
# assumed from the name). For those, this makes generate_akhn_feature.py build
# a genuine, separate TutgAkhand rule keyed on that component's own alt form
# (looked up in variant_registry.json, same source TutgVariantSelect's rules
# come from) instead of leaving the ".altN" glyph to be picked up only via
# variant_registry.json's "_ligature_variants" / TutgConjunctVariantSelect
# (VS11+, a post-ligature-formation substitution). Once overridden this way,
# generate_variant_registry.py excludes the glyph from "_ligature_variants" -
# it's reachable directly by typing "<component><VSn>" BEFORE the conjunct/
# vowel-sign forms, exactly like every other TutgVariantSelect-driven variant,
# with no VS11 layer involved at all. Deliberately keyed by the glyph's real,
# unrenamed font name (not a renamed "bha_alt1_ra-tutg" style name) - the font
# glyph itself is untouched, only how the generator interprets it changes.
LIGATURE_ALT_OVERRIDES = {
    k: v for k, v in NAMES_OVERRIDE.get("ligature_alt_overrides", {}).items() if not k.startswith("_")
}


def apply_ligature_alt_override(resolved_parts, override):
    target = override["resolved_target"]
    alt_index = str(override["alt_index"])
    occurrence = override.get("occurrence", 1)
    resolved_parts = list(resolved_parts)
    seen = 0
    for i, (name, kind) in enumerate(resolved_parts):
        if name != target:
            continue
        seen += 1
        if seen != occurrence:
            continue
        variant_name = VARIANT_REGISTRY.get(target, {}).get(alt_index)
        if variant_name is None:
            return None
        resolved_parts[i] = (variant_name, kind)
        return resolved_parts
    return None


# Tulu-Tigalari has its own encoded REPHA character (U+113D1, cmap'd to the base
# glyph repha-tutg) - unlike Devanagari-style scripts, the expected typed input for
# repha is that character directly, NOT "RA + conjoiner". The hand-written first akhn
# rule below (REPHA_FIRST_RULE) unconditionally upgrades the typed repha-tutg into
# its ligating variant repha-tutg.alt1 (the proposal's recommended default shape)
# before any other akhn rule runs. So every "ra_X-tutg" ligature glyph's OWN rule
# (built here) must match on repha-tutg.alt1 + X, not X + repha-tutg.alt1, even
# though the glyph is *named* starting with "ra" - that name reflects the ligature's
# drawn components/history, not its GSUB input, which is really "Repha + X". Only
# applies when RA is the very first part AND immediately precedes another CONSONANT
# (a real RA-initial conjunct, e.g. ra_ma-tutg) - RA+own-vowel-sign ligatures like
# ra_uMatra-tutg are a completely different thing (RA is the base taking its own
# vowel sign, nothing to do with Repha) and must stay untouched.
#
# CONFIRMED 2026-07-17 via uharfbuzz shaping (not just visual inspection - see
# GSUB_TODO.md): GSUB lookups run on TYPED/logical order (Repha first, then
# consonant) - HarfBuzz's own reph-repositioning is a separate, LATER shaping step
# that only reorders glyphs for on-screen placement, so it can't be relied on to
# feed a "consonant-then-Repha" GSUB rule. A consonant-then-Repha version of this
# rule was tried and confirmed (via hb shaping, not screenshots) to never match -
# repha-tutg.alt1-then-X is the only order that actually works.
def build_input_sequence(resolved_parts):
    seq = []
    prev_kind = None
    is_ra_initial_conjunct = (
        len(resolved_parts) > 1
        and resolved_parts[0] == ("ra-tutg", "consonant")
        and resolved_parts[1][1] == "consonant"
    )
    for i, (name, kind) in enumerate(resolved_parts):
        if i == 0 and is_ra_initial_conjunct:
            seq.append("repha-tutg.alt1")
            prev_kind = "repha"
            continue
        if prev_kind == "consonant" and kind == "consonant":
            seq.append("conjoiner-tutg")
        seq.append(name)
        prev_kind = kind
    return seq


# Hand-written, not derived from any classified glyph name - both repha-tutg and
# repha-tutg.alt1 are existing font glyphs, not "-tutg" compound ligatures. Must run
# before every other akhn rule (every ra_X-tutg rule below assumes repha-tutg.alt1 is
# already the input, not repha-tutg), which is why it's written as literally the
# first line of the lookup block rather than sorted in with the rest.
REPHA_FIRST_RULE = (["repha-tutg"], "repha-tutg.alt1")

# --- Variation-selector-driven glyph variants (added 2026-07-20) ---
#
# variant_registry.json's top-level entries (single base glyph -> {selector
# index: alternate glyph}) become a real GSUB lookup here, TutgVariantSelect -
# "sub bha-tutg vs1-tutg by bha-tutg.alt1;" and so on - instead of the earlier
# prototype's cmap format 14 approach. See generate_vs_glyphs.py for why
# vs1-tutg/vs2-tutg/vs3-tutg exist as real, ordinary encoded glyphs (U+FE00-
# U+FE02): GSUB can only match glyph IDs, never Unicode codepoints directly, so
# the selector characters need a real glyph identity before any `sub` rule can
# reference them at all.
#
# This must be the FIRST lookup in the feature (before TutgRephaUpgrade and
# TutgAkhand) so a requested variant is already resolved before any conjunct-
# forming rule gets a chance to see the base glyph - same reasoning
# TutgRephaUpgrade already establishes for repha-tutg -> repha-tutg.alt1 (which
# is really the same pattern, just hand-written instead of registry-driven).
#
# registry["_conjunct_variants"] (two-consonant ligature alternates, e.g.
# bha_ra-tutg -> bha_ra-tutg.alt1) is deliberately NOT included here - shelved
# for now, see TutgSubjoinerForm below for the mechanism actually used instead.
ALL_CLASSIFIED_GLYPHS = {n for category in d.values() for n in category}
VARIANT_SELECT_RULES = []       # (base_name, vs_glyph, variant_name)
variant_select_missing = []     # (base_name, variant_name) - not a known glyph, skipped
for base_name, variants in sorted(VARIANT_REGISTRY.items()):
    if base_name.startswith("_"):
        continue
    for index_str, variant_name in sorted(variants.items(), key=lambda kv: int(kv[0])):
        if base_name not in ALL_CLASSIFIED_GLYPHS or variant_name not in ALL_CLASSIFIED_GLYPHS:
            variant_select_missing.append((base_name, variant_name))
            continue
        vs_glyph = f"vs{int(index_str)}-tutg"
        VARIANT_SELECT_RULES.append((base_name, vs_glyph, variant_name))

# --- Subjoiner formation (added 2026-07-20) ---
#
# "conjoiner-tutg + vs1-tutg" (typed to request forced below-base stacking
# instead of whatever akhn/blwf would otherwise produce) collapses into a
# single real glyph, subjoiner-tutg, so that blwf's own lookup only ever needs
# a plain 2-glyph pattern ("subjoiner-tutg + CONSONANT -> CONSONANT.below",
# see generate_blwf_feature.py's TutgBlwfSubjoiner) instead of having to
# recognize a longer "CONS1 conjoiner-tutg vs1-tutg CONS2" sequence itself.
# Reusing VS1 (rather than a dedicated index) is safe: TutgVariantSelect's
# rules are keyed off variant_registry.json, which has no "conjoiner-tutg"
# entry, so nothing there ever starts with conjoiner-tutg - this rule and any
# "<other base> + vs1-tutg" rule can never both match the same input, no
# matter which lookup either lives in.
# Must be its OWN lookup (not folded into TutgVariantSelect above) so it runs
# as a full separate pass, same reasoning as TutgRephaUpgrade/TutgAkhand's
# split: a single lookup won't re-examine a glyph it just substituted, and
# here nothing downstream needs to re-examine conjoiner-tutg/vs1-tutg anyway,
# so a second lookup (not merged into the first) keeps this independent and
# easy to reason about on its own.
SUBJOINER_RULE = (["conjoiner-tutg", "vs1-tutg"], "subjoiner-tutg")

# --- Ligature alternates (added 2026-07-20, simplified 2026-07-21) ---
#
# registry["_ligature_variants"] (e.g. ca_ca-tutg -> ca_ca-tutg.alt1) becomes
# TutgConjunctVariantSelect, the LAST lookup in this feature - it runs AFTER
# TutgAkhand, not before/inside it, because by then TutgAkhand has already
# collapsed the ligature's raw input sequence (e.g. "ca-tutg conjoiner-tutg
# ca-tutg") into the single glyph (ca_ca-tutg), so this only needs a plain
# 2-glyph rule keyed on the ligature's own OUTPUT name - "sub ca_ca-tutg
# vs11-tutg by ca_ca-tutg.alt1;" - same "match the output, not the raw input
# sequence" principle blwf's per-ligature rules already rely on. Has to be
# its own lookup for the same reason TutgRephaUpgrade/TutgAkhand are split: a
# single lookup won't re-examine a glyph an earlier rule (here, TutgAkhand)
# just produced in the same pass. Every registry entry here is, by
# construction (see generate_variant_registry.py), already classified as a
# conjunct_ligature/vowel_sign_ligature/looped_virama_ligature output, so this
# needs no per-kind special-casing - two consonants, a consonant + its own
# vowel sign, three consonants, a mixed compound, or a Chillu form are all the
# exact same rule shape.
#
# Index offset by +10 (registry index "1" -> VS11, "2" -> VS12) purely to keep
# this layer's selectors visually distinct from TutgVariantSelect's VS1-VS6
# and TutgSubjoinerForm's VS1 - see variant_registry.json's
# "_ligature_variants_readme" for why that's a convenience, not a requirement
# (GSUB always disambiguates by the full starting glyph, never the selector
# alone, so index reuse across layers is never actually ambiguous).
CONJUNCT_VS_OFFSET = 10
CONJUNCT_VARIANT_RULES = []      # (ligature_name, vs_glyph, variant_name)
conjunct_variant_missing = []    # (ligature_name, variant_name) - not a known glyph, skipped
for ligature_name, variants in sorted(VARIANT_REGISTRY.get("_ligature_variants", {}).items()):
    for index_str, variant_name in sorted(variants.items(), key=lambda kv: int(kv[0])):
        if ligature_name not in ALL_CLASSIFIED_GLYPHS or variant_name not in ALL_CLASSIFIED_GLYPHS:
            conjunct_variant_missing.append((ligature_name, variant_name))
            continue
        vs_glyph = f"vs{CONJUNCT_VS_OFFSET + int(index_str)}-tutg"
        CONJUNCT_VARIANT_RULES.append((ligature_name, vs_glyph, variant_name))


rules = []          # list of (seq_list, output_glyph_name)
alt_candidates = {}  # default output glyph -> [alt glyph names]
skipped_unparsed = []

rules_skipped_by_ignore = []
# Grouping is intentionally GLOBAL across both categories, not per-category: a glyph
# like raMatra_ya-tutg.below (filed under vowel_sign_ligature by the original
# classifier, since it didn't recognize "raMatra" as a consonant token) can resolve
# to the exact same base_key as a glyph filed under conjunct_ligature (ra_ya-tutg) -
# grouping per-category would miss that link entirely and emit both as separate,
# conflicting top-level rules (confirmed 2026-07-16: fontmake caught this as
# "Already defined substitution for ra-tutg, conjoiner-tutg, ya-tutg").
by_base = {}
# "looped_virama_ligature" added 2026-07-17: the standalone Chillu glyphs
# (kChillu-tutg, tChillu-tutg, etc.) live in their own classification bucket,
# separate from the conjunct/vowel-sign ligature categories below - they were
# simply never in this tuple before, which meant e.g. "KA + Looped Virama ->
# kChillu-tutg" had no akhn rule even though the compound "ka_kChillu-tutg"
# (filed under conjunct_ligature, and resolving via the same CHILLU_ABBREV
# decomposition) did. taChillu-tutg stays excluded via the IGNORE check below,
# same as always.
for category in ("conjunct_ligature", "vowel_sign_ligature", "looped_virama_ligature"):
    for gname in d[category]:
        if gname in IGNORE:
            rules_skipped_by_ignore.append(gname)
            continue
        result = split_name(gname)
        if result is None:
            skipped_unparsed.append(gname)
            continue
        resolved_parts, suffix_tags = result
        override = LIGATURE_ALT_OVERRIDES.get(gname)
        if override:
            # Confirmed per-entry to be "one component's own registered alt
            # substituted in" - a first-class ligature with its OWN input
            # sequence, not "an alt of the bare ligature's base_key" (so it
            # must NOT be appended to that base_key's "alts" list below).
            overridden = apply_ligature_alt_override(resolved_parts, override)
            if overridden is None:
                skipped_unparsed.append(gname)
                continue
            resolved_parts, suffix_tags = overridden, []
        base_key = tuple(p[0] for p in resolved_parts)
        by_base.setdefault(base_key, {"default": None, "alts": [], "resolved": resolved_parts})
        if suffix_tags:
            by_base[base_key]["alts"].append(gname)
        else:
            if by_base[base_key]["default"] is not None:
                # two different bare (non-suffixed) glyphs both claim the same
                # input sequence - a genuine naming conflict, not resolvable here.
                skipped_unparsed.append(gname)
            else:
                by_base[base_key]["default"] = gname

for base_key, info in by_base.items():
    if info["default"] is None:
        # No bare glyph exists for this input sequence. A lone ".below"-suffixed
        # variant used to get silently promoted to serve as the default here (e.g.
        # ha_ra-tutg.below standing in for a bare ha_ra-tutg that doesn't exist) -
        # removed 2026-07-17: confirmed these are below-base-only construction
        # pieces, not stand-ins for the real bare ligature. The real ha_ra-tutg /
        # pa_ra-tutg glyphs are genuinely missing artwork that needs to be drawn,
        # not auto-substituted - see GSUB_TODO.md item 12. Skip and report instead.
        skipped_unparsed.extend(info["alts"])
        continue
    seq = build_input_sequence(info["resolved"])
    rules.append((seq, info["default"]))
    if info["alts"]:
        alt_candidates[info["default"]] = info["alts"]

# longest input sequence first (see module docstring); alphabetical by output name
# as a stable tiebreaker so re-runs produce byte-identical output.
rules.sort(key=lambda r: (-len(r[0]), r[1]))

# machine-readable dump for other tools (e.g. the test-page generator) so they don't
# have to re-parse the .fea text. REPHA_FIRST_RULE goes first, matching its position
# in the .fea lookup block.
with open(os.path.join(HERE, "tutg_akhn_rules.json"), "w", encoding="utf-8") as f:
    all_rules = [REPHA_FIRST_RULE] + rules
    json.dump([{"input": seq, "output": out} for seq, out in all_rules], f, indent=2)

out_path = os.path.join(HERE, "tutg_akhn.fea")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("# Auto-generated by generate_akhn_feature.py - conjunct + vowel-sign ligatures\n")
    f.write("# for the Tulu-Tigalari (tutg) script, sorted longest-input-sequence-first so\n")
    f.write("# HarfBuzz's first-match ligature lookup resolves the most specific conjunct\n")
    f.write("# instead of a shorter prefix stealing the match. Review before merging into\n")
    f.write("# the real features.fea (which still has unrelated Latin kerning/numeral\n")
    f.write("# features and a dead Malayalam scaffold that should be removed separately).\n\n")

    f.write("languagesystem DFLT dflt;\n")
    f.write("languagesystem tutg dflt;\n\n")

    f.write("feature akhn {\n")
    f.write("    script tutg;\n")
    f.write("    lookup TutgVariantSelect {\n")
    f.write("        # Base glyph + variation selector -> registered alternate glyph.\n")
    for base_name, vs_glyph, variant_name in VARIANT_SELECT_RULES:
        f.write(f"        sub {base_name} {vs_glyph} by {variant_name};\n")
    f.write("    } TutgVariantSelect;\n")
    f.write("    lookup TutgSubjoinerForm {\n")
    f.write("        # Conjoiner + VS1 -> subjoiner-tutg (forces below-base stacking - see blwf's TutgBlwfSubjoiner).\n")
    subjoiner_seq, subjoiner_out = SUBJOINER_RULE
    f.write(f"        sub {' '.join(subjoiner_seq)} by {subjoiner_out};\n")
    f.write("    } TutgSubjoinerForm;\n")
    # Must be its OWN lookup, applied as a separate pass BEFORE TutgAkhand - not
    # just the first rule inside the same lookup. Confirmed 2026-07-17 via
    # uharfbuzz shaping: within a single GSUB lookup, HarfBuzz scans left-to-right
    # and substitutes at most once per starting position, then moves on - it
    # never re-examines a glyph it just substituted to try a LONGER match against
    # a later rule in that same lookup. So "repha-tutg -> repha-tutg.alt1" (a
    # single-glyph rule keyed on the FIRST glyph) would consume that position
    # and advance, and the ra_X-tutg ligature rules (keyed on repha-tutg.alt1,
    # one position later) would never get a chance to see the just-substituted
    # glyph. Splitting into two lookups makes the upgrade a complete first pass
    # over the whole buffer, so by the time TutgAkhand's second pass runs, every
    # repha-tutg is already repha-tutg.alt1.
    f.write("    lookup TutgRephaUpgrade {\n")
    f.write("        # Typed Repha (repha-tutg) -> ligating variant (repha-tutg.alt1).\n")
    first_seq, first_out = REPHA_FIRST_RULE
    f.write(f"        sub {' '.join(first_seq)} by {first_out};\n")
    f.write("    } TutgRephaUpgrade;\n")
    f.write("    lookup TutgAkhand {\n")
    for seq, out in rules:
        f.write(f"        sub {' '.join(seq)} by {out};\n")
    f.write("    } TutgAkhand;\n")
    f.write("    lookup TutgConjunctVariantSelect {\n")
    f.write("        # Conjunct ligature + variation selector -> registered alternate ligature.\n")
    for ligature_name, vs_glyph, variant_name in CONJUNCT_VARIANT_RULES:
        f.write(f"        sub {ligature_name} {vs_glyph} by {variant_name};\n")
    f.write("    } TutgConjunctVariantSelect;\n")
    f.write("} akhn;\n\n")

    f.write("# --- Stylistic alternates (candidates for a later salt/ss0N feature, NOT included above) ---\n")
    for base, alts in sorted(alt_candidates.items()):
        f.write(f"# {base} -> {', '.join(alts)}\n")
    f.write("\n")

    f.write("# --- Skipped: name doesn't cleanly decompose, needs manual rule (see GSUB_TODO.md) ---\n")
    for gname in skipped_unparsed:
        f.write(f"# {gname}\n")

    f.write("\n# --- Skipped: explicitly excluded via gsub_ignore_list.json ---\n")
    for gname in rules_skipped_by_ignore:
        f.write(f"# {gname}: {IGNORE[gname]}\n")

    if variant_select_missing:
        f.write("\n# --- Skipped: variant_registry.json entry referencing an unknown glyph ---\n")
        for base_name, variant_name in variant_select_missing:
            f.write(f"# {base_name} -> {variant_name}\n")

    if conjunct_variant_missing:
        f.write("\n# --- Skipped: _conjunct_variants entry referencing an unknown glyph ---\n")
        for ligature_name, variant_name in conjunct_variant_missing:
            f.write(f"# {ligature_name} -> {variant_name}\n")

print(f"Total akhn rules: {len(rules)} + 1 hand-written (REPHA_FIRST_RULE)")
print(f"Variant-select rules (TutgVariantSelect): {len(VARIANT_SELECT_RULES)}")
print(f"Variant-select entries skipped (unknown glyph): {len(variant_select_missing)} {variant_select_missing}")
print(f"Conjunct-variant rules (TutgConjunctVariantSelect): {len(CONJUNCT_VARIANT_RULES)}")
print(f"Conjunct-variant entries skipped (unknown glyph): {len(conjunct_variant_missing)} {conjunct_variant_missing}")
print(f"Longest sequence: {len(rules[0][0])} glyphs ({rules[0][1]})")
print(f"Shortest sequence: {len(rules[-1][0])} glyphs ({rules[-1][1]})")
print(f"Stylistic-alternate groups (not included, listed separately): {len(alt_candidates)}")
print(f"Skipped / unparsed: {len(skipped_unparsed)}")
print(f"Skipped / explicitly ignored: {len(rules_skipped_by_ignore)} {rules_skipped_by_ignore}")
print()
print("Written to:", out_path)
