"""
Builds test_page_data.json for glyph_test_page.html: real Unicode input sequences
(actual code points, not glyph names) for every consonant, independent vowel, the
452 auto-generated akhn conjunct/vowel-sign rules, and mark-attachment test rows for
the 9 GPOS-anchored marks - so the test page can render each one through the real
compiled font and visually confirm the GSUB/GPOS work actually renders correctly,
rather than just listing glyph names.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "glyph_svg_data.json"), encoding="utf-8") as f:
    glyphs = json.load(f)
with open(os.path.join(HERE, "tutg_akhn_rules.json"), encoding="utf-8") as f:
    akhn_rules = json.load(f)
with open(os.path.join(HERE, "glyph_classification.json"), encoding="utf-8") as f:
    classification = json.load(f)
with open(os.path.join(HERE, "variant_registry.json"), encoding="utf-8") as f:
    variant_registry = json.load(f)


def cp_of(glyph_name):
    u = glyphs.get(glyph_name, {}).get("unicodes", [])
    return u[0] if u else None


def is_default_form(name):
    # no ".below"/".altN"/other suffix after "-tutg"
    return "-tutg" in name and "." not in name.partition("-tutg")[2]


# --- consonants --- (sorted by Unicode codepoint, i.e. reading order in the
# actual Tulu-Tigalari block, not alphabetically by glyph name)
consonants = []
for name in classification.get("consonant", []):
    if not is_default_form(name):
        continue
    cp = cp_of(name)
    if cp is None:
        continue
    consonants.append({"name": name, "cp": cp})
consonants.sort(key=lambda c: c["cp"])

# --- independent vowels --- (same: codepoint order, not name order)
vowels = []
for name in classification.get("vowel_independent", []):
    if not is_default_form(name):
        continue
    cp = cp_of(name)
    if cp is None:
        continue
    vowels.append({"name": name, "cp": cp})
vowels.sort(key=lambda v: v["cp"])

# --- akhn conjunct/vowel-sign test rows: real code point sequence + expected output glyph ---
consonant_glyph_names = set(classification.get("consonant", []))
KA_CP = cp_of("ka-tutg")

akhn_tests = []
missing_cp = []
for rule in akhn_rules:
    cps = []
    ok = True
    for gname in rule["input"]:
        cp = cp_of(gname)
        if cp is None:
            ok = False
            missing_cp.append(gname)
            break
        cps.append(cp)
    if ok:
        # A rule whose sequence starts with a vowel-sign/mark rather than a
        # consonant (e.g. rVocalicMatra_uMatra-tutg = two matras, no base at all)
        # is a real, valid GSUB rule, but rendering it in isolation makes HarfBuzz
        # insert a dotted circle - correct USE behavior for a base-less mark
        # sequence, not a bug, but misleading in a proofing table. Prepend a
        # representative KA so the row reflects how this actually looks in real
        # text (some consonant always precedes it there) - EXCEPT repha-tutg
        # (REPHA_FIRST_RULE), which is the opposite: Repha attaches to the base
        # that FOLLOWS it, not one before it (confirmed this session - typed
        # order is always Repha-then-consonant, e.g. REPHA+MA -> ra_matutg), so
        # its representative KA needs to be a suffix, not a prefix.
        starts_with_consonant = rule["input"][0] in consonant_glyph_names
        prefix, suffix = [], []
        if not starts_with_consonant and KA_CP is not None:
            if rule["input"][0] == "repha-tutg":
                suffix = [KA_CP]
            else:
                prefix = [KA_CP]
        akhn_tests.append({"cps": prefix + cps + suffix, "output": rule["output"]})

# --- Marks tab: every independent vowel x the two Vedic tone marks we
# have glyphs for ("svaras" - Svarita and Anudatta; Udatta is conventionally
# unmarked), and every consonant x all 4 Repha/Svarita/Anudatta/Gemination marks -
# each as one compact grid (mark = row) rather than a full section per mark.
# Repha and Gemination are deliberately NOT tested against vowels: confirmed via
# uharfbuzz/visual check that HarfBuzz correctly refuses that combination (no GPOS
# anchor exists for a mark that's specified to attach to a consonant base being
# given a vowel instead) and renders a dotted-circle fallback - a real, correct
# "invalid input" result, not a rendering gap, so there's nothing valid to show.
SVARA_MARKS = [("Svarita", "svarita-tutg"), ("Anudatta", "anudatta-tutg")]
mark_vowel_grid = {"rowLabels": [], "colLabels": [v["name"] for v in vowels], "cells": []}
for label, glyph in SVARA_MARKS:
    mcp = cp_of(glyph)
    mark_vowel_grid["rowLabels"].append(label)
    mark_vowel_grid["cells"].append([[v["cp"], mcp] for v in vowels])

ALL_FOUR_MARKS = [
    ("Repha", "repha-tutg", "prefix"),
    ("Svarita", "svarita-tutg", "suffix"),
    ("Anudatta", "anudatta-tutg", "suffix"),
    ("Gemination", "germinationmark-tutg", "suffix"),
]
mark_consonant_grid = {"rowLabels": [], "colLabels": [c["name"] for c in consonants], "cells": []}
for label, glyph, position in ALL_FOUR_MARKS:
    mcp = cp_of(glyph)
    mark_consonant_grid["rowLabels"].append(label)
    mark_consonant_grid["cells"].append(
        [([mcp, c["cp"]] if position == "prefix" else [c["cp"], mcp]) for c in consonants]
    )

# --- consonant x vowel-sign matrix: EVERY consonant against EVERY vowel sign, not
# just the ones with a dedicated pre-drawn ligature. Complements akhnTests (which
# only covers what's already been drawn) by also exercising the vowel signs that
# don't need any special GSUB rule at all (AA/I/II/EE/AI/OO/AU are plain spacing/
# reordering marks) - and, for EE/AI (Left) and OO/AU (Left_And_Right), this
# specifically tests whether HarfBuzz's own built-in Tigalari USE support correctly
# reorders/splits them, since that's the shaping engine's job from Unicode's
# Indic_Positional_Category data, not something our font's GSUB controls at all.
VOWEL_SIGN_COLUMNS = [
    ("(inherent)", None),
    ("Halant", cp_of("virama-tutg")),
    ("AA", 0x113B8),
    ("I", 0x113B9),
    ("II", 0x113BA),
    ("U", 0x113BB),
    ("UU", 0x113BC),
    ("Vocalic R", 0x113BD),
    ("Vocalic RR", 0x113BE),
    ("Vocalic L", 0x113BF),
    ("Vocalic LL", 0x113C0),
    ("EE", 0x113C2),
    ("AI", 0x113C5),
    ("OO", 0x113C7),
    ("AU", 0x113C8),
    # not vowel signs, but same "consonant + one combining thing" column shape -
    # appended after AU per request, to also exercise these 3 anchored marks
    # across every consonant (see GPOS anchors: anusvara/visarga are topright-ish
    # signs, candraanunasika is candrabindu-equivalent - all post-base).
    ("Candrabindu", cp_of("candraanunasika-tutg")),
    ("Anusvara", cp_of("anusvara-tutg")),
    ("Visarga", cp_of("visarga-tutg")),
]
matrix = {
    "vowelSignLabels": [label for label, _ in VOWEL_SIGN_COLUMNS],
    "rows": [],
    # single-select overlay mark (dropdown on the test page) - None by default;
    # Repha is cluster-initial (precedes the base, per the mark-attachment tests
    # above), the other three are post-base and append after whatever's already
    # in the cell (vowel sign or one of the three mark columns above).
    "markOptions": {
        "Repha": {"cp": cp_of("repha-tutg"), "position": "prefix"},
        "Svarita": {"cp": cp_of("svarita-tutg"), "position": "suffix"},
        "Anudatta": {"cp": cp_of("anudatta-tutg"), "position": "suffix"},
        "Gemination": {"cp": cp_of("germinationmark-tutg"), "position": "suffix"},
    },
}
for c in consonants:
    row_cells = []
    for label, vs_cp in VOWEL_SIGN_COLUMNS:
        cps = [c["cp"]] if vs_cp is None else [c["cp"], vs_cp]
        row_cells.append(cps)
    matrix["rows"].append({"consonant": c["name"], "cells": row_cells})

# --- conjunct matrix: EVERY consonant x EVERY consonant (36x36, including the
# diagonal - geminate clusters like "kka" are real Sanskrit conjuncts too), typed
# as [C1, conjoiner, C2] - the same input shape our akhn GSUB rules match on. Most
# of the 1296 combinations have no dedicated ligature glyph (only 452 rules exist
# total, and many of those are 3+ consonant or vowel-sign-suffixed, not plain
# 2-consonant pairs) - this table is exactly what shows, at a glance, which pairs
# fall back to unligated default rendering vs. which have real akhn coverage.
# The vowel-sign suffix and overlay mark are both optional, client-side-applied
# suffixes (not baked into "rows" here) since the test page lets either be
# switched via a dropdown without needing a separate table per combination.
conjoiner_cp = cp_of("conjoiner-tutg")
# Same option set as the Standard Conjunct List's dropdown (build_conjunct_lists.py)
# and the syllable matrix's own columns above - kept identical on purpose so all
# three feel like the same control, not three subtly-different ones.
# "(inherent)" is excluded here - "None" plays that role in the dropdown instead.
vowel_sign_options = {label: vs_cp for label, vs_cp in VOWEL_SIGN_COLUMNS if vs_cp is not None}
conjunct_matrix = {
    "consonants": [c["name"] for c in consonants],
    "vowelSignOptions": vowel_sign_options,
    "markOptions": matrix["markOptions"],
    "rows": [],
}
for c1 in consonants:
    row_cells = []
    for c2 in consonants:
        row_cells.append([c1["cp"], conjoiner_cp, c2["cp"]])
    conjunct_matrix["rows"].append(row_cells)

# --- Variant Registry tab (added 2026-07-20): proofing table for the
# variation-selector-driven GSUB work (generate_akhn_feature.py's
# TutgVariantSelect/TutgSubjoinerForm/TutgConjunctVariantSelect,
# generate_blwf_feature.py's TutgBlwfSubjoiner). Real typed Unicode sequences
# (base + VS + ...), same principle as every other tab here - rendered
# through the compiled font, not hand-picked glyph names.
#
# VS_CP mirrors generate_vs_glyphs.py's VS_GLYPHS list exactly (index -> real
# codepoint of visN-tutg/vs{10+n}-tutg) - duplicated here rather than derived
# from glyphs.json, since that script's index-to-codepoint mapping isn't
# itself recorded anywhere machine-readable other than its own source.
VS_CP = {1: 0xFE00, 2: 0xFE01, 3: 0xFE02, 4: 0xFE03, 5: 0xFE04, 6: 0xFE05, 11: 0xFE0A, 12: 0xFE0B}
# Matches generate_akhn_feature.py's CONJUNCT_VS_OFFSET exactly - registry index
# "1" is real selector VS11 for this layer, not VS1 (which means something else
# entirely, on other bases/lookups).
CONJUNCT_VS_OFFSET = 10
consonant_names = set(classification.get("consonant", []))
vowel_sign_names = set(classification.get("vowel_sign", []))
ka_cp = cp_of("ka-tutg")

character_variants = []  # one row per (consonant base, altN): {label, cells: [[vowelSignLabel, cps], ...]}
consonant_variant_entries = []  # one per (consonant base, altN): {label, variant, baseCp, vsCp} - reused by consonant_variant_matrix below
vowel_variants = []      # one row per (non-consonant base, altN): {label, cps}
variant_missing = []     # (base_name, variant_name) - no cmap entry, skipped
for base_name, variants in sorted(variant_registry.items()):
    if base_name.startswith("_"):
        continue
    base_cp = cp_of(base_name)
    if base_cp is None:
        variant_missing.append((base_name, None))
        continue
    base = base_name[: -len("-tutg")]
    for index_str, variant_name in sorted(variants.items(), key=lambda kv: int(kv[0])):
        vs_cp = VS_CP.get(int(index_str))
        label = f"{base} alt{index_str}"
        if vs_cp is None:
            variant_missing.append((base_name, variant_name))
            continue
        if base_name in consonant_names:
            cells = []
            for vs_label, sign_cp in VOWEL_SIGN_COLUMNS:
                cps = [base_cp, vs_cp] + ([] if sign_cp is None else [sign_cp])
                cells.append([vs_label, cps])
            character_variants.append({"label": label, "variant": variant_name, "cells": cells})
            consonant_variant_entries.append({"label": label, "variant": variant_name, "baseCp": base_cp, "vsCp": vs_cp})
        else:
            # Vowel-SIGN bases (uMatra/uuMatra/iiMatra/lVocalicMatra) are
            # combining marks with no independent glyph shape of their own -
            # rendered orphaned (no preceding consonant) they correctly show
            # HarfBuzz's dotted-circle "invalid base" fallback, which is
            # accurate but useless as a proofing display. Prefix KA so they're
            # shown attached the way they'd actually appear in real text.
            # Independent vowels and repha (the rest of this branch) stand
            # alone fine and get no prefix.
            prefix = [ka_cp] if base_name in vowel_sign_names else []
            vowel_variants.append({"label": label, "variant": variant_name, "cps": prefix + [base_cp, vs_cp]})

# Consonant Variant Matrix: every registered consonant-variant entry (24, e.g.
# "bha alt1", "da alt1", "da alt2", ...) crossed against every OTHER registered
# consonant-variant entry, joined by a conjoiner - a 24x24 grid testing what
# happens when TWO variant-selected consonant forms are conjoined together
# (typed as ROW's base+VS, then conjoiner, then COL's base+VS - so
# TutgVariantSelect resolves both to their .altN forms BEFORE TutgAkhand/blwf
# ever see the pair, since TutgVariantSelect is akhn's first lookup).
consonant_variant_matrix = {
    "labels": [e["label"] for e in consonant_variant_entries],
    "rows": [],
}
for row_e in consonant_variant_entries:
    row_cells = []
    for col_e in consonant_variant_entries:
        cps = [row_e["baseCp"], row_e["vsCp"], conjoiner_cp, col_e["baseCp"], col_e["vsCp"]]
        row_cells.append(cps)
    consonant_variant_matrix["rows"].append(row_cells)

# Conjunct-ligature alternates (registry["_conjunct_variants"]) - VS attaches
# AFTER the whole formed ligature (TutgConjunctVariantSelect matches the
# ligature's own output glyph + a trailing VS, not the conjoiner), unlike the
# subjoiner demo below where the VS sits right after the conjoiner instead -
# these are two genuinely different attachment points, not a typo.
conjunct_variants = []
for first_name, seconds in sorted(variant_registry.get("_conjunct_variants", {}).items()):
    first_cp = cp_of(first_name)
    for second_name, variants in sorted(seconds.items()):
        second_cp = cp_of(second_name)
        if first_cp is None or second_cp is None:
            variant_missing.append((f"{first_name}+{second_name}", None))
            continue
        default_cps = [first_cp, conjoiner_cp, second_cp]
        alts = []
        for index_str, variant_name in sorted(variants.items(), key=lambda kv: int(kv[0])):
            vs_cp = VS_CP.get(CONJUNCT_VS_OFFSET + int(index_str))
            if vs_cp is None:
                variant_missing.append((variant_name, None))
                continue
            alts.append({"variant": variant_name, "cps": default_cps + [vs_cp]})
        conjunct_variants.append({
            "label": f"{first_name[: -len('-tutg')]}_{second_name[: -len('-tutg')]}",
            "default": default_cps,
            "alts": alts,
        })

# Forced-below-base subjoining demo (TutgSubjoinerForm + TutgBlwfSubjoiner) -
# KA+KA as a simple, always-available representative example (unlike the
# conjunct-ligature alternates above, this mechanism works for ANY consonant
# pair, not just a registered list, so one clear example stands in for all of
# them rather than enumerating 36x36 pairs).
subjoiner_demo = {
    "examples": [
        {"label": "KA + KA (plain, no conjoiner)", "cps": [ka_cp, ka_cp]},
        {"label": "KA + conjoiner + KA (default conjunct)", "cps": [ka_cp, conjoiner_cp, ka_cp]},
        {"label": "KA + conjoiner + VS1 + KA (forced below-base)", "cps": [ka_cp, conjoiner_cp, VS_CP[1], ka_cp]},
    ],
}

variant_registry_data = {
    "characterVariants": character_variants,
    "consonantVariantMatrix": consonant_variant_matrix,
    "vowelVariants": vowel_variants,
    "conjunctVariants": conjunct_variants,
    "subjoinerDemo": subjoiner_demo,
}

# --- Unicode tab: every actually-encoded character in the Tulu-Tigalari block
# (U+11380-U+113FF) - i.e. every glyph with a real cmap entry there, regardless of
# category (consonant/vowel/vowel-sign/mark/...). .alt/.below variants are reached
# via GSUB (salt/ss0N), not their own cmap entry, so filtering on "has a unicode in
# this block" naturally excludes them and leaves just the real character
# inventory - a click-to-type palette, one cell per encoded character.
TUTG_BLOCK = (0x11380, 0x113FF)
unicode_chars = []
for name, info in glyphs.items():
    for u in info.get("unicodes", []):
        if TUTG_BLOCK[0] <= u <= TUTG_BLOCK[1]:
            unicode_chars.append({"name": name, "cp": u})
unicode_chars.sort(key=lambda e: e["cp"])

out = {
    "consonants": consonants,
    "vowels": vowels,
    "akhnTests": akhn_tests,
    "markVowelGrid": mark_vowel_grid,
    "markConsonantGrid": mark_consonant_grid,
    "matrix": matrix,
    "conjunctMatrix": conjunct_matrix,
    "variantRegistry": variant_registry_data,
    "unicodeChars": unicode_chars,
}
out_path = os.path.join(HERE, "test_page_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)

print("Consonants:", len(consonants))
print("Independent vowels:", len(vowels))
print("Akhn test rows:", len(akhn_tests), " (skipped, missing cmap:", len(missing_cp), set(missing_cp), ")")
print("Matrix:", len(matrix["rows"]), "consonants x", len(matrix["vowelSignLabels"]), "vowel-sign columns")
print("Conjunct matrix:", len(conjunct_matrix["rows"]), "x", len(conjunct_matrix["consonants"]))
print("Variant registry - character variants:", len(character_variants))
print("Variant registry - consonant variant matrix:", len(consonant_variant_matrix["labels"]), "x", len(consonant_variant_matrix["labels"]))
print("Variant registry - vowel variants:", len(vowel_variants))
print("Variant registry - conjunct variants:", len(conjunct_variants))
print("Variant registry - skipped (missing cmap):", len(variant_missing), variant_missing)
print("Unicode chars:", len(unicode_chars))
print("Written to:", out_path)
