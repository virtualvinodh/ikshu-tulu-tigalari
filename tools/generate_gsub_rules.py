"""
Auto-generates GSUB ligature-substitution rules from the naming convention of the
existing conjunct/vowel-sign ligature glyphs. A ligature glyph's name IS its GSUB
input sequence, by construction: splitting on "_" and reattaching "-tutg" gives the
input glyphs; a conjoiner is inserted between two consecutive CONSONANT parts (no
separator between a consonant and a vowel-sign part, or between two vowel-sign parts).

How the glyph itself was drawn (components vs hand contours) is irrelevant here -
only the *name* determines the rule.

Handles three tiers:
  1. Regular conjunct/vowel-sign ligatures (default substitution) - fully mechanical.
  2. `.altN` suffixed variants of the above - routed to a stylistic-alternate block,
     not the default substitution (OpenType alternate substitution is single-glyph-in,
     single-glyph-out, so these key off the already-ligated default glyph).
  3. The `*Chillu-tutg` (Looped Virama ligature) family - not name-decomposable by
     underscore-splitting, so uses an explicit small mapping table instead. Entries in
     gsub_ignore_list.json are skipped and reported separately.

Anything that doesn't fit these patterns (Repha/Virama compound glyphs, pluta_pluta,
etc.) is deliberately NOT guessed at - it's listed under NEEDS_MANUAL_REVIEW instead.
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
                    "lVocalicMatra", "llVocalicMatra", "eeMatra", "aiMatra", "ooMatra", "auMatra", "dotreph"}

# Explicit mapping for the Chillu (Looped Virama ligature) family - not derivable from
# underscore-splitting since these names have no underscore at all.
CHILLU_MAP = {
    "kChillu-tutg": "ka-tutg",
    "tChillu-tutg": "ta-tutg",
    "ttChillu-tutg": "tta-tutg",
    "ttChillu-tutg.alt1": "tta-tutg",
    "nChillu-tutg": "na-tutg",       # unverified by structure - components are generic, not na-specific
    "nnChillu-tutg": "nna-tutg",     # unverified by structure
    "llChillu-tutg": "lla-tutg",     # unverified by structure; also beyond proposal's documented K/G/TT/T/N list
    "rrChillu-tutg": "rra-tutg",     # unverified by structure; also beyond proposal's documented list
    "bhChillu-tutg": "bha-tutg",     # unverified by structure; also beyond proposal's documented list
    # "taChillu-tutg" intentionally omitted - see gsub_ignore_list.json
}
STRUCTURALLY_CONFIRMED = {"kChillu-tutg", "tChillu-tutg", "ttChillu-tutg", "ttChillu-tutg.alt1"}

NEEDS_MANUAL_REVIEW = [
    "rVocalic_repha-tutg", "virama_dotrepha-tutg", "virama_virama-tutg",
    "rephajoiner_dottedCircle-tutg", "pluta_pluta-tutg", "ramatra_uumatra-tutg.below",
    "lVocalicMatra_tall-tutg.alt2",
]


def split_name(glyph_name):
    """Return (base_input_sequence_parts, suffix_tags) or None if not decomposable."""
    if "-tutg" not in glyph_name:
        return None
    core, _, suffix = glyph_name.partition("-tutg")
    suffix_tags = [t for t in suffix.split(".") if t]
    core = core.replace("_tall", "")  # a size-variant tag, not a ligature component
    parts = core.split("_")
    resolved = []
    for p in parts:
        if p in CONSONANTS or p in VOWEL_SIGN_ROOTS:
            resolved.append((p + "-tutg", "consonant" if p in CONSONANTS else "vowelsign"))
        else:
            return None  # unknown part, bail - don't guess
    return resolved, suffix_tags


def build_input_sequence(resolved_parts):
    seq = []
    for i, (name, kind) in enumerate(resolved_parts):
        if i > 0 and resolved_parts[i - 1][1] == "consonant" and kind == "consonant":
            seq.append("conjoiner-tutg")
        seq.append(name)
    return seq


default_rules = {"conjunct_ligature": [], "vowel_sign_ligature": []}
alt_candidates = {}  # base_output_glyph_name -> [alt_glyph_names]
skipped_unparsed = []

for category in ("conjunct_ligature", "vowel_sign_ligature"):
    # group by base (no-suffix) name first so alt variants can be matched to their default
    by_base = {}
    for gname in d[category]:
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
            by_base[base_key]["default"] = gname

    for base_key, info in by_base.items():
        if info["default"] is None:
            # no bare/default glyph exists, only alt(s) - still needs a default; skip for manual pick
            skipped_unparsed.extend(info["alts"])
            continue
        seq = build_input_sequence(info["resolved"])
        default_rules[category].append(f"sub {' '.join(seq)} by {info['default']};")
        if info["alts"]:
            alt_candidates[info["default"]] = info["alts"]

# Chillu family
chillu_rules = []
chillu_unverified_note = []
for gname, base in CHILLU_MAP.items():
    chillu_rules.append(f"sub {base} loopedvirama-tutg by {gname};")
    if gname not in STRUCTURALLY_CONFIRMED:
        chillu_unverified_note.append(gname)

# --- write output ---
out_path = os.path.join(HERE, "generated_gsub_rules.fea")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("# Auto-generated from glyph naming convention - see generate_gsub_rules.py\n")
    f.write("# Review before merging into features.fea. Not yet wired into any feature block.\n\n")

    f.write("# --- Conjunct ligatures (consonant + conjoiner + consonant[+...]) ---\n")
    f.write(f"# {len(default_rules['conjunct_ligature'])} rules\n")
    f.write("\n".join(default_rules["conjunct_ligature"]) + "\n\n")

    f.write("# --- Vowel-sign ligatures (consonant + vowel sign[+vowel sign]) ---\n")
    f.write(f"# {len(default_rules['vowel_sign_ligature'])} rules\n")
    f.write("\n".join(default_rules["vowel_sign_ligature"]) + "\n\n")

    f.write("# --- Looped Virama ligatures (Chillu family) ---\n")
    f.write(f"# {len(chillu_rules)} rules. UNVERIFIED BY STRUCTURE (name trusted as-is, not cross-checked "
            f"against components): {', '.join(chillu_unverified_note)}\n")
    f.write("# 'taChillu-tutg' excluded - see gsub_ignore_list.json (confirmed name/artwork mismatch)\n")
    f.write("\n".join(chillu_rules) + "\n\n")

    f.write("# --- Stylistic alternates (candidates for salt/ss0N feature) ---\n")
    for base, alts in alt_candidates.items():
        f.write(f"# {base} -> {', '.join(alts)}\n")
    f.write("\n")

    f.write("# --- NOT auto-generated, needs manual rule ---\n")
    for gname in NEEDS_MANUAL_REVIEW + skipped_unparsed:
        f.write(f"# {gname}\n")

print("Conjunct ligature rules:", len(default_rules["conjunct_ligature"]))
print("Vowel-sign ligature rules:", len(default_rules["vowel_sign_ligature"]))
print("Chillu rules:", len(chillu_rules), " (unverified by structure:", len(chillu_unverified_note), ")")
print("Stylistic-alternate groups:", len(alt_candidates))
print("Skipped / unparsed (need manual rule):", len(skipped_unparsed) + len(NEEDS_MANUAL_REVIEW))
print("Ignored (documented, e.g. taChillu-tutg):", len(IGNORE))
print()
print("Written to:", out_path)
