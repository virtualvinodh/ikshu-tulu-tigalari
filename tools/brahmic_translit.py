"""
Mechanical Brahmic-script transliteration between any of {Sharada, Devanagari,
Kannada, Tigalari}, plus a one-way Latin (IAST) rendering.

Devanagari, Kannada, Sharada and Tigalari all lay out the same phonetic inventory
(independent vowels, then consonants in varga order, then dependent vowel signs, in
that order) in their Unicode block, by deliberate design (see Unicode's "Indic
scripts" rationale) - so a single phoneme-keyed table drives every direction, in
either direction: text_to_phonemes(text, source_script) parses any one of the four
into the same intermediate token stream, and phonemes_to_script(tokens, table) /
phonemes_to_iast(tokens) render that stream into any target.

Codepoints verified against the Unicode 17.0 code charts:
  Devanagari U+0900, Kannada U+0C80, Sharada U+11180 (unicode.org/charts/PDF/).
Tigalari codepoints are this project's own, already-verified glyph/cmap data
(see build_test_page_data.py / glyph_svg_data.json).

Sanskrit source texts only ever use the standard 34-consonant set - Tigalari's two
extra consonants (rra, llla, for Tulu/Dravidian sounds) have no Sharada/Devanagari
equivalent and are simply never hit when parsing those scripts as a source.
"""

INDEPENDENT_VOWELS = ["a", "aa", "i", "ii", "u", "uu", "vocalicR", "vocalicRR",
                       "vocalicL", "vocalicLL", "e", "ai", "o", "au"]

VOWEL_SIGNS = ["aa", "i", "ii", "u", "uu", "vocalicR", "vocalicRR",
               "vocalicL", "vocalicLL", "e", "ai", "o", "au"]

CONSONANTS = ["ka", "kha", "ga", "gha", "nga", "ca", "cha", "ja", "jha", "nya",
              "tta", "ttha", "dda", "ddha", "nna", "ta", "tha", "da", "dha", "na",
              "pa", "pha", "ba", "bha", "ma", "ya", "ra", "la", "lla", "va",
              "sha", "ssa", "sa", "ha", "rra", "llla"]

# --- Devanagari (U+0900 block, verified against Unicode 17.0 chart) ---
DEVANAGARI = {
    "independent_vowels": dict(zip(INDEPENDENT_VOWELS, [
        0x905, 0x906, 0x907, 0x908, 0x909, 0x90A, 0x90B, 0x960,
        0x90C, 0x961, 0x90F, 0x910, 0x913, 0x914,
    ])),
    "vowel_signs": dict(zip(VOWEL_SIGNS, [
        0x93E, 0x93F, 0x940, 0x941, 0x942, 0x943, 0x944,
        0x962, 0x963, 0x947, 0x948, 0x94B, 0x94C,
    ])),
    "consonants": dict(zip(CONSONANTS, [
        0x915, 0x916, 0x917, 0x918, 0x919, 0x91A, 0x91B, 0x91C, 0x91D, 0x91E,
        0x91F, 0x920, 0x921, 0x922, 0x923, 0x924, 0x925, 0x926, 0x927, 0x928,
        0x92A, 0x92B, 0x92C, 0x92D, 0x92E, 0x92F, 0x930, 0x932, 0x933, 0x935,
        0x936, 0x937, 0x938, 0x939, 0x931, 0x934,
    ])),
    "virama": 0x94D, "conjoiner": 0x94D,
    "anusvara": 0x902, "visarga": 0x903, "candrabindu": 0x901, "avagraha": 0x93D,
    "danda": 0x964, "doubleDanda": 0x965,
}

# --- Kannada (U+0C80 block, verified against Unicode 17.0 chart) ---
# Sanskrit e/o are long in Sanskrit, so use Kannada's EE/OO (long) letters/signs,
# matching standard Kannada orthographic practice for Sanskrit loanwords/mantras.
KANNADA = {
    "independent_vowels": dict(zip(INDEPENDENT_VOWELS, [
        0xC85, 0xC86, 0xC87, 0xC88, 0xC89, 0xC8A, 0xC8B, 0xCE0,
        0xC8C, 0xCE1, 0xC8F, 0xC90, 0xC93, 0xC94,
    ])),
    "vowel_signs": dict(zip(VOWEL_SIGNS, [
        0xCBE, 0xCBF, 0xCC0, 0xCC1, 0xCC2, 0xCC3, 0xCC4,
        0xCE2, 0xCE3, 0xCC7, 0xCC8, 0xCCB, 0xCCC,
    ])),
    "consonants": dict(zip(CONSONANTS, [
        0xC95, 0xC96, 0xC97, 0xC98, 0xC99, 0xC9A, 0xC9B, 0xC9C, 0xC9D, 0xC9E,
        0xC9F, 0xCA0, 0xCA1, 0xCA2, 0xCA3, 0xCA4, 0xCA5, 0xCA6, 0xCA7, 0xCA8,
        0xCAA, 0xCAB, 0xCAC, 0xCAD, 0xCAE, 0xCAF, 0xCB0, 0xCB2, 0xCB3, 0xCB5,
        0xCB6, 0xCB7, 0xCB8, 0xCB9, 0xCB1, 0xCDE,
    ])),
    "virama": 0xCCD, "conjoiner": 0xCCD,
    "anusvara": 0xC82, "visarga": 0xC83, "candrabindu": 0xC81, "avagraha": 0xCBD,
    "danda": 0x964, "doubleDanda": 0x965,  # Kannada block has none; chart says use the generic Devanagari ones
}

# --- Sharada (U+11180 block, verified against Unicode 17.0 chart) ---
# Sharada has no rra/llla - never needed since these source texts are Sanskrit.
SHARADA = {
    "independent_vowels": dict(zip(INDEPENDENT_VOWELS[:14], [
        0x11183, 0x11184, 0x11185, 0x11186, 0x11187, 0x11188, 0x11189, 0x1118A,
        0x1118B, 0x1118C, 0x1118D, 0x1118E, 0x1118F, 0x11190,
    ])),
    "vowel_signs": dict(zip(VOWEL_SIGNS, [
        0x111B3, 0x111B4, 0x111B5, 0x111B6, 0x111B7, 0x111B8, 0x111B9,
        0x111BA, 0x111BB, 0x111BC, 0x111BD, 0x111BE, 0x111BF,
    ])),
    "consonants": dict(zip(CONSONANTS[:34], [
        0x11191, 0x11192, 0x11193, 0x11194, 0x11195, 0x11196, 0x11197, 0x11198, 0x11199, 0x1119A,
        0x1119B, 0x1119C, 0x1119D, 0x1119E, 0x1119F, 0x111A0, 0x111A1, 0x111A2, 0x111A3, 0x111A4,
        0x111A5, 0x111A6, 0x111A7, 0x111A8, 0x111A9, 0x111AA, 0x111AB, 0x111AC, 0x111AD, 0x111AE,
        0x111AF, 0x111B0, 0x111B1, 0x111B2,
    ])),
    "virama": 0x111C0, "conjoiner": 0x111C0,
    "anusvara": 0x11181, "visarga": 0x11182, "candrabindu": 0x11180, "avagraha": 0x111C1,
    "danda": 0x111C5, "doubleDanda": 0x111C6,
}

# --- Tigalari (this project's own verified glyph cmap data) ---
# NOTE: unlike the other three scripts, Tigalari uses two *different* codepoints
# for "conjoiner" (medial, joins consonants into a conjunct/akhand ligature - see
# this project's akhn GSUB rules) vs "virama" (word/syllable-final, shaped as a
# Bindu-like mark per the Universal Shaping Engine override - see
# tulu-tigalari-shaping-model memory). Getting this backwards silently produces the
# wrong glyph, so the conversion routine picks one or the other explicitly rather
# than reusing a single "virama" constant like the other three scripts can.
TIGALARI = {
    "independent_vowels": dict(zip(INDEPENDENT_VOWELS, [
        0x11380, 0x11381, 0x11382, 0x11383, 0x11384, 0x11385, 0x11386, 0x11387,
        0x11388, 0x11389, 0x1138B, 0x1138E, 0x11390, 0x11391,
    ])),
    "vowel_signs": dict(zip(VOWEL_SIGNS, [
        0x113B8, 0x113B9, 0x113BA, 0x113BB, 0x113BC, 0x113BD, 0x113BE,
        0x113BF, 0x113C0, 0x113C2, 0x113C5, 0x113C7, 0x113C8,
    ])),
    "consonants": dict(zip(CONSONANTS, [
        0x11392, 0x11393, 0x11394, 0x11395, 0x11396, 0x11397, 0x11398, 0x11399, 0x1139A, 0x1139B,
        0x1139C, 0x1139D, 0x1139E, 0x1139F, 0x113A0, 0x113A1, 0x113A2, 0x113A3, 0x113A4, 0x113A5,
        0x113A6, 0x113A7, 0x113A8, 0x113A9, 0x113AA, 0x113AB, 0x113AC, 0x113AD, 0x113B3, 0x113AE,
        0x113AF, 0x113B0, 0x113B1, 0x113B2, 0x113B4, 0x113B5,
    ])),
    "virama": 0x113CE, "conjoiner": 0x113D0,
    "anusvara": 0x113CC, "visarga": 0x113CD, "candrabindu": 0x113CA, "avagraha": 0x113B7,
    "danda": 0x113D4, "doubleDanda": 0x113D5,
}

# --- IAST (Latin, diacritic transliteration) ---
# Not a codepoint table like the Brahmic scripts above: IAST is an alphabetic
# script, so a consonant's inherent "a" has to be spelled out explicitly (or
# suppressed, when a virama/conjoiner follows) rather than being implicit the way
# it is in every abugida above. phonemes_to_iast() below handles that directly.
IAST_INDEPENDENT_VOWELS = dict(zip(INDEPENDENT_VOWELS, [
    "a", "ā", "i", "ī", "u", "ū", "ṛ", "ṝ", "ḷ", "ḹ", "e", "ai", "o", "au",
]))
IAST_VOWEL_SIGNS = dict(zip(VOWEL_SIGNS, [
    "ā", "i", "ī", "u", "ū", "ṛ", "ṝ", "ḷ", "ḹ", "e", "ai", "o", "au",
]))
IAST_CONSONANTS = dict(zip(CONSONANTS, [
    "k", "kh", "g", "gh", "ṅ", "c", "ch", "j", "jh", "ñ",
    "ṭ", "ṭh", "ḍ", "ḍh", "ṇ", "t", "th", "d", "dh", "n",
    "p", "ph", "b", "bh", "m", "y", "r", "l", "ḷ", "v",
    "ś", "ṣ", "s", "h", "ṟ", "ḻ",
]))
IAST_SIGNS = {"anusvara": "ṃ", "visarga": "ḥ", "candrabindu": "m̐", "avagraha": "'",
              "danda": "|", "doubleDanda": "‖"}


def phonemes_to_iast(tokens):
    out = []
    i = 0
    n = len(tokens)
    while i < n:
        kind, key = tokens[i]
        if kind == "consonants":
            out.append(IAST_CONSONANTS[key])
            nxt = tokens[i + 1] if i + 1 < n else (None, None)
            if nxt[0] == "virama":
                i += 2  # virama/conjoiner both just suppress the inherent "a" here
            elif nxt[0] == "vowel_signs":
                out.append(IAST_VOWEL_SIGNS[nxt[1]])
                i += 2
            else:
                out.append("a")  # bare consonant -> inherent vowel, spelled out
                i += 1
            continue
        if kind == "independent_vowels":
            out.append(IAST_INDEPENDENT_VOWELS[key])
        elif kind in IAST_SIGNS:
            out.append(IAST_SIGNS[kind])
        elif kind == "virama":
            raise UnmappedCharacter("unexpected standalone virama token")
        elif kind == "space":
            out.append(key)
        elif kind == "digit":
            out.append(key)
        elif kind == "literal":
            # already known safe to pass through as-is - text_to_phonemes raises
            # before this if it's an unmapped character inside the source script's
            # own block instead of a genuine literal
            out.append(key)
        else:
            raise UnmappedCharacter(f"unhandled token kind {kind!r}")
        i += 1
    return "".join(out)


SCRIPTS = {"devanagari": DEVANAGARI, "kannada": KANNADA, "sharada": SHARADA, "tigalari": TIGALARI}

# Each script's own Unicode block - used to tell "a character this script's table
# doesn't cover" (a real gap, worth surfacing) apart from "a character outside this
# script entirely" (editorial Latin punctuation etc., safe to pass through as-is).
BLOCK_RANGES = {
    "devanagari": (0x0900, 0x097F),
    "kannada": (0x0C80, 0x0CFF),
    "sharada": (0x11180, 0x111DF),
    "tigalari": (0x11380, 0x113FF),
}

# Decorative verse-number digits, mapped to plain ASCII (Tigalari's own digit
# glyphs exist in the UFO but aren't cmap'd yet - see GSUB_TODO.md - so there's no
# real Tigalari digit to map *to* even when a source uses its own script's digits).
DIGIT_BASES = {"devanagari": 0x0966, "kannada": 0x0CE6, "sharada": 0x111D0}


def _build_reverse_table(table):
    """codepoint -> ('kind', phoneme_key) for one script's table. Tigalari's
    conjoiner and virama are different codepoints (see the TIGALARI comment above);
    every other script uses one codepoint for both, so here - on the *parsing* side
    - both always collapse to the single generic 'virama' token kind. Which of a
    target script's own conjoiner/virama codepoints to emit is re-derived from
    context on the *rendering* side (phonemes_to_script's lookahead), exactly the
    same way for all four scripts."""
    rev = {}
    for kind in ("independent_vowels", "vowel_signs", "consonants"):
        for key, cp in table[kind].items():
            rev[cp] = (kind, key)
    for kind in ("virama", "conjoiner", "anusvara", "visarga", "candrabindu", "avagraha", "danda", "doubleDanda"):
        cp = table.get(kind)
        if cp is not None:
            rev.setdefault(cp, ("virama" if kind == "conjoiner" else kind, None))
    return rev


_REVERSE_TABLES = {name: _build_reverse_table(tbl) for name, tbl in SCRIPTS.items()}
for _name, _base in DIGIT_BASES.items():
    for _i in range(10):
        _REVERSE_TABLES[_name][_base + _i] = ("digit", str(_i))


class UnmappedCharacter(Exception):
    pass


def text_to_phonemes(text, source_script):
    """Parses text in any of the four scripts into a flat list of
    ('kind', key_or_None) tokens. A character inside source_script's own Unicode
    block that isn't in our table is a real gap and raises; a character outside
    that block entirely (editorial Latin punctuation, stray marks from other
    scripts) passes through as ('literal', char) for the renderer to copy as-is."""
    rev = _REVERSE_TABLES[source_script]
    lo, hi = BLOCK_RANGES[source_script]
    tokens = []
    for ch in text:
        cp = ord(ch)
        if ch == " " or ch == "\n":
            tokens.append(("space", ch))
            continue
        entry = rev.get(cp)
        if entry is not None:
            tokens.append(entry)
            continue
        if lo <= cp <= hi:
            raise UnmappedCharacter(f"no mapping for {source_script} character {ch!r} (U+{cp:04X})")
        tokens.append(("literal", ch))
    return tokens


def phonemes_to_script(tokens, table):
    """Converts a phoneme token stream (from text_to_phonemes) into codepoints
    for the given script table (KANNADA / TIGALARI / DEVANAGARI / SHARADA)."""
    out = []
    i = 0
    n = len(tokens)
    while i < n:
        kind, key = tokens[i]
        if kind == "consonants":
            out.append(table["consonants"][key])
            nxt = tokens[i + 1] if i + 1 < n else (None, None)
            if nxt[0] == "virama":
                after = tokens[i + 2] if i + 2 < n else (None, None)
                if after[0] == "consonants":
                    out.append(table["conjoiner"])
                else:
                    out.append(table["virama"])
                i += 2
            elif nxt[0] == "vowel_signs":
                out.append(table["vowel_signs"][nxt[1]])
                i += 2
            else:
                i += 1  # bare consonant -> inherent vowel, no sign to emit
            continue
        if kind == "independent_vowels":
            out.append(table["independent_vowels"][key])
        elif kind in ("anusvara", "visarga", "candrabindu", "avagraha", "danda", "doubleDanda"):
            out.append(table[kind])
        elif kind == "virama":
            # stray/unexpected virama not following a consonant - shouldn't happen
            # in well-formed text; surface it rather than silently dropping it.
            raise UnmappedCharacter("unexpected standalone virama token")
        elif kind == "space":
            out.append(ord(key))
        elif kind == "digit":
            out.append(ord(key))  # ASCII digit, same in every script's rendering here
        elif kind == "literal":
            # already known safe to pass through as-is - see text_to_phonemes
            out.append(ord(key))
        else:
            raise UnmappedCharacter(f"unhandled token kind {kind!r}")
        i += 1
    return out


def transliterate(text, source_script, target):
    """target is one of SCRIPTS' keys, or 'iast'. If source_script == target
    (e.g. a passage that's already written in Tigalari), returns text unchanged -
    no round-trip through the phoneme stream, so there's no risk of it lossily
    reconstructing something other than what was actually typed."""
    if source_script == target:
        return text
    tokens = text_to_phonemes(text, source_script)
    if target == "iast":
        return phonemes_to_iast(tokens)
    return "".join(chr(cp) for cp in phonemes_to_script(tokens, SCRIPTS[target]))
