"""
Regenerates variant_registry.json by scanning the font's own glyph inventory
for every "<name>.altN" glyph and grouping it by its base - so adding a new
hand-drawn alt glyph to the font, then re-running this script, is all that's
needed to register it (instead of hand-editing variant_registry.json, which
is what this file used to be).

Detection: any glyph name matching "<base>-tutg.altN" (or a bare "<base>-tutg.alt"
with no digit, e.g. lVocalicMatra-tutg.alt - a real naming inconsistency already
in the font, treated as index "1" the same way the hand-maintained file already
did) where "<base>-tutg" is itself a real glyph. Routed into one of two
sections by what the base actually is:

  - Single glyph (registry's top-level entries): base is classified as a
    "consonant", "vowel_independent", "vowel_sign", or "special_mark" (repha) -
    one real Unicode character with its own alt presentation forms. Consumed
    by generate_akhn_feature.py's TutgVariantSelect (akhn's first lookup).

  - Ligature (registry["_ligature_variants"]): base is classified under
    "conjunct_ligature", "vowel_sign_ligature", or "looped_virama_ligature" -
    i.e. it's a real output of one of TutgAkhand's own ligature-formation
    rules (confirmed against tutg_akhn_rules.json), regardless of how many
    tokens its name has or what they represent (two consonants, a consonant +
    its own vowel sign, three consonants, a consonant+consonant+vowel-sign
    mix, a Chillu form, ...). Consumed by generate_akhn_feature.py's
    TutgConjunctVariantSelect (akhn's last lookup), which just matches
    "ligature glyph + VSn -> alt glyph" - it never needed to know what KIND
    of ligature it is, only that TutgAkhand already produced it as a single
    glyph by the time this lookup runs. An earlier version of this script
    tried to hand-decompose ligature names into "first consonant + second
    consonant" and only handled the 2-consonant and consonant+vowel-sign
    cases (as two separate registry sections) - unnecessary complexity that
    also meant genuine 3+-token ligatures (ka_sa_sa-tutg, na_ka_ta-tutg,
    na_ta_sa-tutg, sha_ra_iiMatra-tutg) and Chillu forms (ttChillu-tutg) sat
    unhandled in VARIANT_REGISTRY_TODO.md even though they need zero special
    handling - the classification-category check below is both simpler and
    strictly more correct.

Anything else with an ".altN" sibling - a base that isn't a real TutgAkhand
ligature output at all (e.g. vamatra-tutg, classified as
"vowel_sign_component" - a drawing component used inside OTHER glyphs, like
raMatra-tutg, never itself a shaped output of any GSUB rule, so selecting an
"alt" of it via VS would never be reachable in real text), or a base that
turns out not to be a real glyph at all (a few genuine typos/internal-tool
artifacts already in the font, e.g. "_smart.vamatra-tutg.alt1") - is reported
instead of guessed at, in VARIANT_REGISTRY_TODO.md, same principle as every
other gap in this project's GSUB tooling.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "glyph_svg_data.json"), encoding="utf-8") as f:
    glyphs = json.load(f)
with open(os.path.join(HERE, "glyph_classification.json"), encoding="utf-8") as f:
    classification = json.load(f)

consonant_names = set(classification.get("consonant", []))
vowel_independent_names = set(classification.get("vowel_independent", []))
vowel_sign_names = set(classification.get("vowel_sign", []))
special_mark_names = set(classification.get("special_mark", []))
single_glyph_bases = consonant_names | vowel_independent_names | vowel_sign_names | special_mark_names

# The 3 categories TutgAkhand's own ligature-formation rules (in
# generate_akhn_feature.py) already build rules for - see that script's
# "for category in (...)" loop. Anything in one of these is, by
# construction, a real single-glyph output some akhn rule produces, so
# TutgConjunctVariantSelect can always match "this glyph + VSn -> its alt"
# regardless of how the name is put together.
ligature_bases = (
    set(classification.get("conjunct_ligature", []))
    | set(classification.get("vowel_sign_ligature", []))
    | set(classification.get("looped_virama_ligature", []))
)

# Bare ".alt" (no digit) is a real, existing naming inconsistency in this font
# (lVocalicMatra-tutg.alt, plus every "<cons>_lVocalicMatra-tutg.alt" compound)
# - treated as index "1", matching how the hand-maintained file already had it.
ALT_RE = re.compile(r"^(?P<base>.+-tutg)\.alt(?P<idx>\d*)$")

single_glyph_variants = {}  # base_name -> {index_str: alt_name}
ligature_variants = {}      # ligature_name -> {index_str: alt_name}
skipped_no_base = []        # alt exists but "<base>-tutg" isn't a real glyph
skipped_unclassified = []   # base is a real glyph but not a category this registry handles

for name in sorted(glyphs):
    m = ALT_RE.match(name)
    if not m:
        continue
    base = m.group("base")
    idx = m.group("idx") or "1"
    if base not in glyphs:
        skipped_no_base.append(name)
        continue
    if base in single_glyph_bases:
        single_glyph_variants.setdefault(base, {})[idx] = name
        continue
    if base in ligature_bases:
        ligature_variants.setdefault(base, {})[idx] = name
        continue
    skipped_unclassified.append(name)

registry = {
    "_readme": (
        "Auto-generated by generate_variant_registry.py - re-run it after "
        "adding a new '<name>-tutg.altN' glyph to the font instead of "
        "hand-editing this file; it will pick up the new variant "
        "automatically. Registry for selecting stylistic-alternate glyphs "
        "via Unicode Variation Selectors (VS1-VS6 for this layer - "
        "U+FE00-U+FE05) instead of OpenType stylistic-set features (ssXX). "
        "Consumed by generate_akhn_feature.py's TutgVariantSelect (akhn's "
        "first lookup): \"sub bha-tutg vs1-tutg by bha-tutg.alt1;\" and so "
        "on for every entry below - typing <base character><VSn> resolves "
        "to the glyph listed under key \"N\" here. Typing the base character "
        "alone (no selector) still resolves to its normal default glyph. "
        "Index \"1\" = VS1 (U+FE00), \"2\" = VS2 (U+FE01), etc. - built from "
        "every single-codepoint glyph (consonant/independent vowel/vowel "
        "sign/special mark) that has one or more '.altN' siblings in the "
        "font. This is a private/font-specific convention, not a "
        "Unicode-registered Ideographic Variation Sequence - only this font "
        "(and any tooling that reads this registry) knows what these "
        "particular base+selector pairs mean."
    ),
}
for base, variants in sorted(single_glyph_variants.items()):
    registry[base] = dict(sorted(variants.items(), key=lambda kv: int(kv[0])))

registry["_ligature_variants_readme"] = (
    "Auto-generated alongside the section above - see generate_variant_registry.py. "
    "Selecting among alternate LIGATURE forms (e.g. ca_ca-tutg vs ca_ca-tutg.alt1) - "
    "any glyph classified under conjunct_ligature/vowel_sign_ligature/"
    "looped_virama_ligature (i.e. any real output of one of TutgAkhand's own "
    "ligature-formation rules), regardless of what kind of ligature it is: "
    "two consonants (ca_ca-tutg), a consonant + its own vowel sign "
    "(ka_uMatra-tutg), three consonants (ka_sa_sa-tutg), a mixed "
    "consonant+consonant+vowel-sign compound (sha_ra_iiMatra-tutg), or a "
    "Chillu form (ttChillu-tutg). Mechanism (generate_akhn_feature.py's "
    "TutgConjunctVariantSelect, the LAST lookup in feature akhn): by the "
    "time this lookup runs, TutgAkhand has already collapsed the ligature's "
    "raw input sequence into this single glyph, so this is just a plain "
    "2-glyph substitution keyed on the ligature's own OUTPUT name - 'sub "
    "ca_ca-tutg vs11-tutg by ca_ca-tutg.alt1;' - same principle blwf's "
    "per-ligature rules already rely on. Indices here are offset by +10 "
    "(index \"1\" -> VS11, \"2\" -> VS12, ...) to keep this layer's selector "
    "range visually distinct from the base-glyph variant registry above "
    "(VS1-VS6) and the subjoiner mechanism (VS1 on the conjoiner) - though "
    "nothing stops index reuse across layers in practice, since GSUB always "
    "disambiguates by the full starting glyph, not the selector alone."
)
registry["_ligature_variants"] = {
    name: dict(sorted(variants.items(), key=lambda kv: int(kv[0])))
    for name, variants in sorted(ligature_variants.items())
}

ligature_entry_count = sum(len(v) for v in ligature_variants.values())

out_path = os.path.join(HERE, "variant_registry.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(registry, f, indent=2, ensure_ascii=False)
    f.write("\n")

# markdown report - written even when nothing is unclassified, so a re-run's
# "all clear" is an explicit, checkable fact rather than the mere absence of a file.
report_path = os.path.join(HERE, "VARIANT_REGISTRY_TODO.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("# variant_registry.json coverage report\n\n")
    f.write(f"Generated by `generate_variant_registry.py` - {sum(len(v) for v in single_glyph_variants.values())} "
            f"single-glyph variant entries ({len(single_glyph_variants)} bases), "
            f"{ligature_entry_count} ligature variant entries ({len(ligature_variants)} bases).\n\n")

    if skipped_unclassified:
        f.write(f"## {len(skipped_unclassified)} alt glyph(s) with a base this registry doesn't handle\n\n")
        f.write("Base isn't consonant/vowel/vowel-sign/mark, and isn't classified under "
                "conjunct_ligature/vowel_sign_ligature/looped_virama_ligature either (i.e. it's not "
                "a real TutgAkhand ligature output) - e.g. vamatra-tutg, a drawing component used "
                "inside other glyphs, never itself a shaped output. Listed here for a future "
                "decision, not included in variant_registry.json.\n\n")
        for name in skipped_unclassified:
            f.write(f"- `{name}`\n")
        f.write("\n")
    else:
        f.write("**All clear** - every `.altN` glyph in the font is either a registered "
                "single-glyph or ligature variant.\n\n")

    if skipped_no_base:
        f.write(f"## {len(skipped_no_base)} alt glyph(s) with no real base glyph at all\n\n")
        f.write("The glyph name implies a base (`<name>-tutg`) that doesn't actually exist in "
                "the font - likely a typo or an internal tool artifact, not a real variant.\n\n")
        for name in skipped_no_base:
            f.write(f"- `{name}`\n")
        f.write("\n")

print(f"Single-glyph variant bases: {len(single_glyph_variants)}")
print(f"Single-glyph variant entries: {sum(len(v) for v in single_glyph_variants.values())}")
print(f"Ligature variant bases: {len(ligature_variants)}")
print(f"Ligature variant entries: {ligature_entry_count}")
print(f"Skipped - unclassified base: {len(skipped_unclassified)} {skipped_unclassified}")
print(f"Skipped - no real base glyph: {len(skipped_no_base)} {skipped_no_base}")
print("Written to:", out_path)
print("Written to:", report_path)
