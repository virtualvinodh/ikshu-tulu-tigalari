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
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "glyph_classification.json"), encoding="utf-8") as f:
    d = json.load(f)
with open(os.path.join(HERE, "gsub_ignore_list.json"), encoding="utf-8") as f:
    IGNORE = json.load(f)

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

# "raMatra" is this font's alternate token for the consonant RA in its final/combining
# form (see e.g. ba_ra-tutg, which is built from ba-tutg + raMatra-tutg components) -
# semantically it IS just consonant RA for GSUB input-sequence purposes, regardless of
# which component was used to draw the ligature. Confirmed 2026-07-16: sa_ta_raMatra-tutg
# is the SA+TA+RA conjunct ("stra"), not an unparseable oddity.
#
# The rest are confirmed 2026-07-16 as typos/alternate spellings of tokens already
# known elsewhere in the font, not genuinely different concepts:
#   - "UuMatra"      -> capital U typo for "uuMatra" (nya_UuMatra-tutg)
#   - "rvocalicMatra" -> lowercase-r typo for "rVocalicMatra" (sa_pa_rvocalicMatra-tutg)
#   - "vocalicR"      -> different spelling/word-order for "rVocalicMatra"
#                        (sa_ka_vocalicR-tutg, ssa_ka_vocalicR-tutg)
TOKEN_ALIASES = {
    "raMatra": ("ra-tutg", "consonant"),
    "UuMatra": ("uuMatra-tutg", "vowelsign"),
    "rvocalicMatra": ("rVocalicMatra-tutg", "vowelsign"),
    "vocalicR": ("rVocalicMatra-tutg", "vowelsign"),
}

# "XChillu" is this font's shorthand for [consonant X] + Looped Virama, e.g. kChillu-tutg
# = ka-tutg + loopedvirama-tutg. Confirmed 2026-07-16: decompose it the same way as any
# other multi-part name rather than treating it as an opaque single token, so
# ka_kChillu-tutg correctly resolves to ka + conjoiner + ka + loopedvirama.
CHILLU_ABBREV = {"k": "ka", "t": "ta", "tt": "tta", "n": "na", "nn": "nna",
                  "ll": "lla", "rr": "rra", "bh": "bha",
                  "ta": "ta"}  # see note below - this is NOT the same thing as "taChillu-tutg"
# "ta" here means: within a COMPOUND name, a "taChillu" token decomposes to TA + Looped
# Virama - confirmed 2026-07-16 for `ta_taChillu-tutg` specifically, whose components
# are `_taleftarm`/`_tamiddle` (TA's own parts, same ones tChillu-tutg itself uses) +
# `_loopedviramaCombining.alt1` + a second `_tamiddle` - i.e. real T.T+Looped-Virama
# (documented in the proposal §5.4c), nothing YA-related. This is a DIFFERENT glyph
# from the standalone `taChillu-tutg` (which IS the confirmed name/artwork mismatch,
# built from ya-tutg.below) - the two just happen to share the token "taChillu". The
# IGNORE check below is the actual guarantee that adding "ta" here can never silently
# resolve the standalone broken glyph, rather than relying on it not being in the
# categories this script iterates over.


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


def build_input_sequence(resolved_parts):
    seq = []
    for i, (name, kind) in enumerate(resolved_parts):
        if i > 0 and resolved_parts[i - 1][1] == "consonant" and kind == "consonant":
            seq.append("conjoiner-tutg")
        seq.append(name)
    return seq


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
for category in ("conjunct_ligature", "vowel_sign_ligature"):
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
# have to re-parse the .fea text.
with open(os.path.join(HERE, "tutg_akhn_rules.json"), "w", encoding="utf-8") as f:
    json.dump([{"input": seq, "output": out} for seq, out in rules], f, indent=2)

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

print(f"Total akhn rules: {len(rules)}")
print(f"Longest sequence: {len(rules[0][0])} glyphs ({rules[0][1]})")
print(f"Shortest sequence: {len(rules[-1][0])} glyphs ({rules[-1][1]})")
print(f"Stylistic-alternate groups (not included, listed separately): {len(alt_candidates)}")
print(f"Skipped / unparsed: {len(skipped_unparsed)}")
print(f"Skipped / explicitly ignored: {len(rules_skipped_by_ignore)} {rules_skipped_by_ignore}")
print()
print("Written to:", out_path)
