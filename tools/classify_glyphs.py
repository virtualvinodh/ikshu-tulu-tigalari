import plistlib, re, sys, json, os
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
UFO = os.path.join(os.path.dirname(HERE), "Ikshu-Regular.ufo")
with open(os.path.join(UFO, "glyphs", "contents.plist"), "rb") as f:
    contents = plistlib.load(f)

names = [n for n in contents if "-tutg" in n]

INDEP_VOWELS = {"a","aa","i","ii","u","uu","rVocalic","rrVocalic","lVocalic","llVocalic","ee","ai","oo","au"}
VOWEL_SIGN_ROOTS = {"aaMatra","iMatra","iiMatra","uMatra","uuMatra","rVocalicMatra","rrVocalicMatra",
                     "lVocalicMatra","llVocalicMatra","eeMatra","aiMatra","ooMatra","auMatra","dotreph"}
CONSONANTS = {"ka","kha","ga","gha","nga","ca","cha","ja","jha","nya","tta","ttha","dda","ddha","nna",
              "ta","tha","da","dha","na","pa","pha","ba","bha","ma","ya","ra","la","va","sha","ssa",
              "sa","ha","lla","rra","llla","nnna"}
SPECIAL_ROOTS = {"virama","loopedvirama","conjoiner","repha","rephajoiner","rephajoiner_dottedCircle",
                  "anusvara","visarga","candraanunasika","candrabindu","germinationmark","svarita","anudatta",
                  "avagraha","pluta","danda","doubledanda","om","shrii","dotrepha","aulengthmark",
                  "ompushpika","rVocalic_repha"}
NUMERAL_ROOTS = {"zero","one","two","three","four","five","six","seven","eight","nine","ten","onehundred"}
CHILLU_ROOTS = {"kChillu","tChillu","ttChillu","nChillu","nnChillu","llChillu","rrChillu","bhChillu","taChillu"}
VOWEL_SIGN_COMPONENTS = {"raMatra","vamatra","yamatra","mamatra"}
UNENCODED_REFERENCE = {"e","eMatra","o","oMatra"}

def classify(name):
    if name.startswith("_smart.") or name.startswith("_"):
        return "component/utility", None
    # split off "-tutg" and trailing dotted suffixes
    m = re.match(r"^(.*)-tutg(.*)$", name)
    if not m:
        return "non-tutg", None
    core, suffix = m.group(1), m.group(2)  # suffix like "", ".below", ".alt1", ".below.alt1", ".conjunct"
    suffix_tags = [t for t in suffix.split(".") if t]  # e.g. ['below','alt1']

    # glyphs with all-caps components are stray test/sample glyphs, not real characters
    if re.search(r"[A-Z]{2}", core):
        return "test/sample_glyph", suffix_tags

    # normalize a trailing "_tall" (a size variant tag, not a ligature component)
    core2 = re.sub(r"_tall$", "", core)

    parts = core2.split("_")  # underscore-joined components

    if len(parts) == 1:
        root = parts[0]
        if root in NUMERAL_ROOTS:
            return "tulu_numeral_alt", suffix_tags
        if root in CHILLU_ROOTS:
            return "looped_virama_ligature", suffix_tags
        if root in VOWEL_SIGN_COMPONENTS:
            return "vowel_sign_component", suffix_tags
        if root in UNENCODED_REFERENCE:
            return "unencoded_reference_vowel", suffix_tags
        if root in INDEP_VOWELS:
            return "vowel_independent", suffix_tags
        if root in VOWEL_SIGN_ROOTS:
            return "vowel_sign", suffix_tags
        if root in CONSONANTS:
            if "below" in suffix_tags:
                return "consonant_below_base", suffix_tags
            return "consonant", suffix_tags
        if root in SPECIAL_ROOTS:
            return "special_mark", suffix_tags
        return "unclassified_single", suffix_tags
    else:
        known_kind = lambda p: (
            "vowelsign" if p in VOWEL_SIGN_ROOTS or p in VOWEL_SIGN_COMPONENTS else
            "consonant" if p in CONSONANTS else
            "special" if p in SPECIAL_ROOTS or p in INDEP_VOWELS or p in CHILLU_ROOTS else
            None
        )
        kinds = [known_kind(p) for p in parts]
        has_vowelsign = "vowelsign" in kinds
        has_consonant = "consonant" in kinds
        all_known = all(k is not None for k in kinds)
        if has_vowelsign and has_consonant:
            return "vowel_sign_ligature", suffix_tags
        elif has_vowelsign and not has_consonant:
            return "vowel_sign_ligature", suffix_tags  # matra+matra combos (e.g. rVocalicMatra_uMatra)
        elif has_consonant and not has_vowelsign:
            return "conjunct_ligature", suffix_tags
        elif not all_known:
            return "unclassified_multi", suffix_tags
        else:
            return "special_mark", suffix_tags  # e.g. virama_virama, virama_dotrepha

results = defaultdict(list)
for n in sorted(names):
    cat, tags = classify(n)
    results[cat].append(n)

print("=== Counts ===")
for cat, lst in sorted(results.items(), key=lambda x: -len(x[1])):
    print(f"{cat}: {len(lst)}")

print()
print("=== Samples (up to 8 each) ===")
for cat, lst in sorted(results.items(), key=lambda x: -len(x[1])):
    print(f"\n--- {cat} ({len(lst)}) ---")
    for n in lst[:8]:
        print(" ", n)

with open(os.path.join(HERE, "glyph_classification.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\nTotal tutg glyphs:", len(names))
