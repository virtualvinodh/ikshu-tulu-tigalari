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

print(f"Total akhn rules: {len(rules)} + 1 hand-written (REPHA_FIRST_RULE)")
print(f"Longest sequence: {len(rules[0][0])} glyphs ({rules[0][1]})")
print(f"Shortest sequence: {len(rules[-1][0])} glyphs ({rules[-1][1]})")
print(f"Stylistic-alternate groups (not included, listed separately): {len(alt_candidates)}")
print(f"Skipped / unparsed: {len(skipped_unparsed)}")
print(f"Skipped / explicitly ignored: {len(rules_skipped_by_ignore)} {rules_skipped_by_ignore}")
print()
print("Written to:", out_path)
