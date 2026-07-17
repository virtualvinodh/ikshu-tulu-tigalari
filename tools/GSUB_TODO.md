# GSUB rule generation - open items

Superseded by `generate_akhn_feature.py` -> `tutg_akhn.fea` (453 rules, sorted
longest-input-sequence-first, wrapped in a real `feature akhn { script tutg; ... }`
block with `languagesystem tutg dflt;`). `generate_gsub_rules.py` -> `generated_gsub_rules.fea`
was the earlier draft (unsorted, no feature wrapper); keeping both scripts since the
fixes below were only ported into `generate_akhn_feature.py` so far.

## 1 & 2. RESOLVED 2026-07-16 - naming inconsistencies confirmed and fixed

All confirmed by project owner and handled in `generate_akhn_feature.py` as proper
token aliases / decomposition rules (not fuzzy-matching - each is now an explicit,
documented mapping):

- **Chillu-as-conjunct-base** (`ka_kChillu-tutg`, `na_ttChillu-tutg`, etc.) - now
  decomposes `XChillu` into `[consonant X] + loopedvirama-tutg` generically (via
  `CHILLU_ABBREV`), e.g. `ka_kChillu-tutg` -> `ka + conjoiner + ka + loopedvirama`.
  Matches the proposal's documented behavior (§5.4c: Looped-Virama characters can be
  a conjunct base). `ta_taChillu-tutg` still excluded - see item 3.
- `raMatra` -> confirmed alias for consonant `ra` in its combining form (e.g.
  `sa_ta_raMatra-tutg` = SA+TA+RA, "stra"). See `TOKEN_ALIASES`.
- `UuMatra` -> confirmed typo for `uuMatra` (capital U). See `TOKEN_ALIASES`.
- `rvocalicMatra` -> confirmed typo for `rVocalicMatra` (lowercase r). See `TOKEN_ALIASES`.
- `vocalicR` -> confirmed alias for `rVocalicMatra` (different spelling/word-order,
  not just a case typo). See `TOKEN_ALIASES`.
- `na_ta_ra_ya_-tutg` -> confirmed stray trailing underscore typo; parser now drops
  empty segments from a trailing `_` rather than failing the whole name.
- `ha_ra-tutg.below`, `pa_ra-tutg.below` -> **reversed 2026-07-17, see item 12.**
  Originally the parser promoted a lone `.below` variant to serve as its own
  default when no bare sibling glyph existed, so these two got real top-level
  `akhn` rules. Per the flagged caveat at the time ("worth a visual check before
  this ships") - confirmed wrong: these are below-base-only construction pieces,
  not stand-ins for the real bare `ha_ra-tutg`/`pa_ra-tutg` ligatures, which are
  genuinely missing artwork. The promotion mechanism was removed entirely.
- `raMatra_ya-tutg.below` -> resolved automatically by the `raMatra` alias + the
  `.below`-promotion fix together (RA+YA below-base form).
- `ta_taChillu-tutg` -> confirmed 2026-07-16 as **T.T with Looped Virama** (a
  different glyph from the standalone `taChillu-tutg`, which just happens to share
  the token "taChillu"). Verified via components: `_taleftarm`/`_tamiddle` (TA's own
  parts, same ones `tChillu-tutg` uses) + `_loopedviramaCombining.alt1` + a second
  `_tamiddle` - real T.T+Looped-Virama, documented in the proposal §5.4c, nothing
  YA-related. Added `"ta": "ta"` to `CHILLU_ABBREV` to resolve this. Also added an
  explicit `gsub_ignore_list.json` check in the main loop (was loaded but never
  actually applied before) so this can never accidentally resolve the *standalone*
  `taChillu-tutg` too - that one stays excluded regardless of category scoping.

**At the time: all 543 conjunct + vowel-sign ligature names parsed - zero skipped.**
No longer current - see item 12 (2026-07-17): removing the `.below`-promotion
mechanism put `ha_ra-tutg.below`/`pa_ra-tutg.below` back into the skipped list,
on purpose. 450 rules, 3 skipped as of that change.

## 3. Still open

- `taChillu-tutg` (and by extension `ta_taChillu-tutg`) - **confirmed wrong**,
  excluded via `gsub_ignore_list.json` (component check showed it's built from
  `ya-tutg.below`, not any TA part - name/artwork mismatch). Still the only
  confirmed-bad *existing* glyph found in this whole audit. Needs a content
  decision (redraw from TA parts / reassign / delete) before it can be renamed or
  given a real rule.
- ~~`nChillu-tutg`, `nnChillu-tutg`, `llChillu-tutg`, `rrChillu-tutg`,
  `bhChillu-tutg`~~ - **resolved 2026-07-16, confirmed correct by project owner.**
  (Structurally these are built from generic Looped-Virama pieces with no
  consonant-specific sub-part to cross-check against, unlike `kChillu`/`tChillu`/
  `ttChillu.alt1`, and LLA/RRA/BHA aren't in the proposal's documented K/G/TT/T/N
  list - so this couldn't be verified from the file alone, but is confirmed
  intentional. No longer blocking the rename batch.)
- `rVocalic_repha-tutg`, `virama_dotrepha-tutg`, `virama_virama-tutg`,
  `rephajoiner_dottedCircle-tutg`, `pluta_pluta-tutg`, `ramatra_uumatra-tutg.below`,
  `lVocalicMatra_tall-tutg.alt2` - don't fit the consonant/vowel-sign decomposition
  pattern at all; need hand-written rules, not auto-generation.
- **Missing artwork, confirmed 2026-07-17 (see item 12):** the real bare
  `ha_ra-tutg` and `pa_ra-tutg` conjunct ligatures don't exist - only the
  below-base-only `ha_ra-tutg.below`/`pa_ra-tutg.below` pieces do. These need to
  be drawn before HA+RA / PA+RA can get a proper top-level `akhn` rule; until
  then they correctly fall back to `blwf`'s generic below-base stacking (RA's
  own below-form) instead of a dedicated ligature.

## 4. `oMatra-tutg` / `ooMatra-tutg` naming vs. cmap mismatch (found 2026-07-16)

While auditing the full Tulu-Tigalari block for missing cmap entries (all 80 real
code points do resolve to a non-empty glyph - nothing is actually missing), found
that `U+113C7` VOWEL SIGN OO is correctly mapped and has real artwork (15 contours,
2 components) - but under the name `oMatra-tutg` (one "o"), not `ooMatra-tutg` (two
"o"s, the name that matches the font's own convention - c.f. `oo-tutg` for the
independent OO letter). Meanwhile `ooMatra-tutg` is a dead, empty stub (0 contours,
0 components, no unicode) that was apparently created but never used.

Compare the parallel E-family, where this did NOT happen: `eeMatra-tutg` (correctly
named) carries the real mapped artwork for `U+113C2`, and `eMatra-tutg` (the
unencoded reference stub, same as `e-tutg`/`o-tutg`) is correctly the empty one. The
O-family is inverted from that pattern - `oMatra-tutg` looks like it should be the
unencoded/reference glyph by naming convention, but it's actually the real,
production, correctly-cmapped OO vowel sign.

**Not urgent** - `U+113C7` renders correctly today, nothing is broken. **Fix
whenever the naming-convention rename batch happens**: move the artwork + `unicode`
value from `oMatra-tutg` to `ooMatra-tutg`, retire the `oMatra-tutg` name (or repoint
it to actually be the unencoded-reference short-O vowel-sign stub, matching how
`eMatra-tutg` is used).

## 5. Bugs found during the first real `fontmake` compile (2026-07-16)

`tutg_akhn.fea` parsed 543/543 names cleanly (section 1&2 above), but two of the
*generated rules themselves* were still wrong - fontmake's compiler caught both
immediately, before any visual testing was needed.

### 5a. Duplicate substitution: `raMatra_ya-tutg.below` vs `ra_ya-tutg`

fontmake error: `Already defined substitution for "ra-tutg, conjoiner-tutg, ya-tutg"`.

**Root cause.** `ra_ya-tutg` (a real, bare, top-level RA+YA ligature) is filed under
`conjunct_ligature` by the classifier, while `raMatra_ya-tutg.below` is filed under
`vowel_sign_ligature` (the classifier didn't recognize `raMatra` as a consonant
token, back when `glyph_classification.json` was first built). Both resolve to the
*identical* input sequence (`ra-tutg conjoiner-tutg ya-tutg`) once the `raMatra`
alias is applied.

Before the fix, `generate_akhn_feature.py` processed categories in a loop, with a
**fresh `by_base = {}` dict created per category**:

```python
for category in ("conjunct_ligature", "vowel_sign_ligature"):
    by_base = {}          # <- reset every iteration
    for gname in d[category]:
        ...                # group by base_key into by_base
    for base_key, info in by_base.items():
        ...                # emit a rule per base_key
```

So `ra_ya-tutg` got grouped (and emitted as a rule) while processing
`conjunct_ligature`, using a `by_base` dict that gets thrown away before
`vowel_sign_ligature` is even looked at. Then `raMatra_ya-tutg.below` got grouped
into a *brand new, empty* `by_base` dict while processing `vowel_sign_ligature` -
which has no record that `ra_ya-tutg` already claimed that exact input sequence, so
it had no bare/default glyph to attach to and got promoted to its own default via
the `.below`-only-promotion rule (section 1&2's `ha_ra-tutg.below` fix) - correct
logic, wrong scope. Both glyphs ended up as separate top-level rules for the same
input sequence, which fontmake's compiler rejects outright as an unresolvable
ambiguity (it can't know which one you meant).

**Fix.** Moved the `by_base = {}` dict creation to *before* the category loop, so
both categories accumulate into the same dict:

```python
by_base = {}
for category in ("conjunct_ligature", "vowel_sign_ligature"):
    for gname in d[category]:
        ...                # now shares state across both categories
for base_key, info in by_base.items():
    ...                    # single emission pass, after both categories are seen
```

With shared state, `ra_ya-tutg` (no suffix) becomes the recognized default for that
`base_key`, and `raMatra_ya-tutg.below` (has a `.below` suffix) correctly falls into
the `alts` list *of that same entry* - resolved as a stylistic-alternate candidate
of `ra_ya-tutg`, not a competing rule. Also added a guard for the remaining
edge case: if two different *bare* (non-suffixed) glyphs ever claim the same
`base_key`, that's a genuine, unresolvable naming conflict - now caught explicitly
and routed to `skipped_unparsed` rather than silently overwriting one with the other.

Net effect: 452 top-level rules (down from 453) and 85 alternate-candidate groups
(up from 84) - one rule removed, one alternate gained, nothing lost.

### 5b. `ka_iMatra_dotreph-tutg` ("vowel matra" + Repha compound) - stale bad token

fontmake error: glyph `dotreph-tutg` "referenced but missing from the glyph set"
(at the line for `ka_iMatra_dotreph-tutg`'s rule).

**Root cause.** `VOWEL_SIGN_ROOTS` (carried over from the earlier
`generate_gsub_rules.py` draft) incorrectly included `"dotreph"` as if it were a
normal vowel-sign token mapping to a real glyph `dotreph-tutg` - but **neither
`dotreph-tutg` nor `dotrepha-tutg` actually exist anywhere in the font.**

Before the fix, `split_name()` processed `"ka_iMatra_dotreph-tutg"` by splitting it
into `["ka", "iMatra", "dotreph"]` and checking each token: `ka` matched
`CONSONANTS`, `iMatra` matched `VOWEL_SIGN_ROOTS`, and `dotreph` *also* matched
`VOWEL_SIGN_ROOTS` (wrongly). All three tokens "resolved," so the parser confidently
emitted:

```
sub ka-tutg iMatra-tutg dotreph-tutg by ka_iMatra_dotreph-tutg;
```

- a rule referencing `dotreph-tutg` as if it were real, typeable input. fontmake only
caught this because it validates every glyph name against the actual glyph set at
compile time; the generator itself had no way to know.

Checked what `ka_iMatra_dotreph-tutg` is actually built from: components are
`ka-tutg`, `repha-tutg.alt1`, `iiMatra-tutg` - a Repha-involving compound that
doesn't even match its own name cleanly (name says "iMatra", artwork uses
`iiMatra`). Same family as the other Repha/Virama compounds already listed in
section 3 as needing a hand-written rule, not auto-generation - it should never have
been auto-parseable in the first place.

**Fix: removal, not replacement.** Deleted `"dotreph"` from `VOWEL_SIGN_ROOTS`.
There wasn't an obvious correct token to replace it with - the glyph's real
components don't reduce to a simple consonant+vowel-sign sequence at all. With the
token gone, `split_name()` now hits `else: return None` on `dotreph` (the same
"unknown part, bail" path every other unrecognized token takes), so the *whole* name
`ka_iMatra_dotreph-tutg` fails to parse and lands in `skipped_unparsed`, joining the
other Repha/Virama compounds in section 3 - instead of the parser inventing a
partial, broken rule for it. Same principle as everywhere else in this audit: when
in doubt, surface the gap rather than silently paper over it with a guess.

**After both fixes: 452 rules, 85 alternate-candidate groups, 1 skip
(`ka_iMatra_dotreph-tutg`, belongs with section 3's compound list).**

### 5c. Two unrelated, pre-existing compile blockers (not GSUB/akhn issues)

Found and fixed while getting `fontmake` to run at all - documented in their own
scripts, not repeated in full here:

- **`guillemotleft`/`guillemetleft` (and `-right`) both mapped to the same cmap
  codepoint** (`U+00AB`/`U+00BB`) - fontmake refuses to build with an ambiguous
  cmap. `guillemotleft`/`guillemotright` is the standard AGL name (and the one
  `features.fea`'s own kerning classes already reference) - cleared the unicode
  mapping from the `guillemet*` duplicates instead. See
  `fix_guillemet_duplicate_cmap.py`.
- **`numr`/`dnom`/`frac` features reference glyphs that don't exist** (`zero.numr`,
  `oneeighth`, etc. - confirmed 100% missing, not partially). Pre-existing incomplete
  stub features left over from whatever template this font was bootstrapped from
  (same category as the dead Malayalam scaffold). Removed those three feature
  blocks (and their `aalt` references) to get a compilable build; `lnum`/`onum`/
  `zero` were checked and are fully complete, left untouched. See
  `remove_stub_numeral_features.py`.

## 6. Standard Conjunct List tab (2026-07-16)

Added a "Standard Conjunct List" tab to `glyph_test_page.html`, modeled on
satisarsharada's `Text-Conjuncts` tab (`conjuncts_Sharada_*.json` - one file per
trailing vowel, each with `conjuncts2S1`/`3S1`/`4S1`/`5S1` arrays of real Unicode
text). Sharada's lists are a hand-curated corpus of attested Sanskrit consonant
clusters, independent of what the font draws - there's no equivalent corpus for
Tulu-Tigalari, so this tab instead re-flattens our own 452 `akhn` GSUB rules
(already grouped in the Conjuncts & Vowel Signs tab) into the same shape: category
buttons (Plain conjunct / +U / +UU / +Vocalic R / +Vocalic RR / +Vocalic L) each
showing copy-pasteable blocks of text grouped by consonant-stack count (2/3/4).
Built by `build_test_page_data.py` (new `conjunctLists` key) and rendered by
`glyph_test_page_template.html`'s `renderConjList()`.

**Bug found and fixed while verifying this via Playwright screenshot:** the first
render showed a jumble of unrelated Latin/diacritic glyphs instead of Tigalari
script - classic mojibake, not a font or GSUB problem. Root cause: every other tab
stores test sequences as **codepoint integers** (`"cps": [4500, ...]`) and builds the
display string client-side with `String.fromCodePoint`, which is encoding-agnostic.
The new conjunct-list code took a shortcut and pre-joined the literal Unicode
characters into a string server-side (`"".join(chr(cp) for cp in cps)`) and wrote
that straight into the JSON/HTML. The page had **no `<meta charset="utf-8">`**, so
for a local `file://` load Chromium fell back to guessing an encoding, misread the
UTF-8 bytes as Latin-1, and the `Ikshu Test` font (which has no glyphs for those
wrong codepoints) fell back to the system font for the resulting mojibake
characters. Fixed both the immediate bug and the underlying gap: added
`<meta charset="utf-8">` to the template, and changed `conjunctLists` items back to
`"cps": [...]` (matching the pattern everywhere else on the page) so the string is
built client-side via `String.fromCodePoint` instead of embedded pre-formed.
Re-verified with Playwright: 0 console errors across all 7 tabs, screenshot confirms
correct Tigalari rendering.

## 7. Sample Texts tab: real Sanskrit passages via Brahmic transliteration (2026-07-16)

Added a "Sample Texts" tab with 7 real Sanskrit Buddhist/Vedic passages (Heart Sutra,
Ushnisha Vijaya Dharani, Nilakantha Dharani, Lotus Sutra ch. 25, a Lalitavistara
excerpt, the Dhammacakkappavattana Sutta, a Vedic passage) - the same texts
satisarsharada's test page uses. Unlike the Standard Conjunct List (section 6),
there's no way to *derive* real prose from this font's own glyph inventory, and no
independent Tulu-Tigalari corpus of these texts exists - so instead of fabricating
content, the actual Sharada-script text was pulled from satisarsharada's
`testing.html` and mechanically transliterated into Tigalari, using Devanagari as
the verified intermediate/pivot representation (per user request, to also get a
Kannada rendering for cross-checking).

**`brahmic_translit.py`**: a phoneme-keyed table (independent vowels, consonants,
dependent vowel signs, virama, anusvara, visarga, candrabindu, avagraha, danda) with
one entry per script - Devanagari, Kannada, and Sharada codepoints were verified
directly against the Unicode 17.0 code charts (unicode.org/charts/PDF/U0900.pdf,
U0C80.pdf, U11180.pdf), not from memory; Tigalari codepoints reuse this project's
own already-verified glyph/cmap data. All four scripts lay out independent vowels,
then consonants in varga order, then dependent vowel signs, in the same relative
order - by Unicode design - so one shared phoneme list drives every column of the
table. `sharada_to_phonemes()` parses Sharada text into a token stream;
`phonemes_to_script()` walks it, distinguishing (critically) Tigalari's two
*different* codepoints for what Devanagari/Kannada/Sharada each cover with a single
virama: `conjoiner-tutg` (U+113D0, medial, joins two consonants into an `akhn`
conjunct) vs. `virama-tutg` (U+113CE, word-final, shaped as a Bindu-like mark per
the Universal Shaping Engine override - see the tulu-tigalari-shaping-model memory).
Getting this backwards silently produces a wrong glyph, so the lookahead explicitly
picks one or the other rather than reusing a single constant.

**Validation before scaling to all 7 texts:** ran the engine on just the Heart
Sutra's closing line first. The Devanagari output it produced -
"इति प्रज्ञापारमिताहृदयसूत्रं समाप्तम्" ("thus the Prajnaparamita-hridaya-sutra is
completed") - is the well-known, correct canonical colophon of the Heart Sutra,
confirming the table and the conjunct/virama-vs-conjoiner logic are right before
generating anything from it. The Tigalari output was then screenshotted through the
real compiled font: it rendered as clean, correctly-formed Tigalari (including
already-verified conjunct ligatures like `pa_ra-tutg.below` for "प्र"), not tofu or
mojibake.

**Extraction and remaining gaps:** `build_sample_texts.py` pulls each passage's raw
text out of satisarsharada's `testing.html` by div id, strips markup, and
transliterates word-by-word into Tigalari (main text) and Kannada (ruby annotation)
codepoint arrays - stored as `"cps": [...]` arrays rather than pre-joined strings,
same reasoning as section 6's mojibake fix. Three categories of leftover characters
needed explicit handling rather than silently crashing or guessing: editorial Latin
punctuation from the source markup (commas, dashes, quotes - pass through
unchanged), Sharada digits used only as decorative verse numbers (Tigalari's own
digit glyphs exist in the UFO but aren't cmap'd yet, so these render as plain ASCII
digits instead), and a handful (12 total, out of ~2870 words) of rare Kashmiri-only
Vedic accent-transliteration marks (U+A8F3/A8F4) that are genuinely outside both
Sanskrit-in-Sharada's core inventory and this font's scope - left as visible tofu
rather than dropped, since that's honest about the gap. All 2870 words across all 7
passages convert with zero unmapped-and-hidden failures.

## 8. IAST annotation, checkbox/tab UI, and a generic {text, sourceScript} pipeline (2026-07-16/17)

Three follow-up requests turned the Sample Texts tab from a fixed Sharada-only
pipeline into a general one:

**IAST.** Added `phonemes_to_iast()` to `brahmic_translit.py` - same token stream as
the Brahmic-script renderer, but IAST is alphabetic, so a consonant's inherent "a"
has to be spelled out explicitly rather than being implicit. A virama or conjoiner
token (either one - IAST doesn't distinguish "medial conjunct" from "word-final",
unlike Tigalari) just means "don't add the a". Validated against the Heart Sutra's
well-known colophon (`iti prajñāpāramitāhṛdayasūtraṃ samāptam`) before trusting it
on the rest.

**UI.** The passage selector was pill/chip buttons ("tags") - changed to an actual
tab bar (bottom-border active indicator: `.text-tab-bar`/`.text-tab`). The
Kannada/IAST annotation choice was an exclusive two-chip toggle - changed to two
independent checkboxes (`sampleAnnModes`, a JS `Set`), so both can show at once
(stacked, IAST above Kannada above the Tigalari word), one, or neither.

**Generic pipeline.** The transliteration engine was Sharada-only in and
Tigalari/Kannada/Devanagari-out. Generalized both directions:
`_build_reverse_table()` builds a codepoint->phoneme reverse lookup for *any* of
the four scripts (previously only `_SHARADA_REV` existed), and
`text_to_phonemes(text, source_script)` replaces the old `sharada_to_phonemes()`.
The one real subtlety: Tigalari is the only one of the four where conjoiner and
virama are *different* codepoints (see section 7's note) - on the parsing side both
collapse to one generic `"virama"` token regardless of source script, and which of
a target script's own conjoiner/virama codepoints to emit is re-derived from
lookahead context on the rendering side, exactly the same way for all four. Verified
with round-trips (`sharada->tigalari->kannada` and `sharada->kannada` agree;
`devanagari->tigalari` matches `sharada->tigalari` bit-for-bit; `tigalari->tigalari`
is a no-op passthrough, not a lossy round-trip) before wiring it in.

`transliterate(text, source_script, target)` now takes an explicit source script
(previously assumed Sharada), and short-circuits to `text` unchanged when
`source_script == target` - the actual mechanism behind "if it's already Tulu, just
display it as such".

**Data pipeline.** `sample_texts_source.json` (new) is now the actual source of
truth: a plain list of `{id, label, sourceScript, text}`. `extract_source_texts.py`
(one-time migration) pulled the existing 7 passages out of satisarsharada's
`testing.html` into this format, tagged `sourceScript: "sharada"` - after this,
satisarsharada is no longer a build dependency at all. `build_sample_texts.py` was
rewritten to read this generic file and dispatch per passage's `sourceScript`
instead of hardcoding Sharada; adding a new passage (in any of the four scripts,
including text that's already Tigalari) means adding one entry to
`sample_texts_source.json`, no script changes needed. Re-ran the full pipeline
after the rewrite and confirmed byte-identical output to the previous hardcoded
version; all 8 tabs re-verified with Playwright, 0 console errors.

Rendered as `<ruby>` markup: Tigalari main text with a small Kannada annotation
above each word, via the browser's own Kannada font fallback (expected and correct -
unlike the mojibake bug, this is a *different* script the `Ikshu Test` font was
never meant to cover). Verified with Playwright across three passages (Hridaya,
Nilakantha, Lotus): 0 console errors, correct rendering.

## 9. Glyph naming discrepancy: "sha_ra_iiMatra-tutg" is actually SHRII PUSHPIKA (2026-07-17)

Found while adding an "Under symbols" section to the Basic tab (Pluta/Danda/Double
Danda/Om Pushpika + this one). The UFO's glyph name for U+113D8 -
`sha_ra_iiMatra-tutg` - describes what the glyph's component shapes visually
resemble (sha + ra + ii-matra), not its actual Unicode identity. Checked against
the Unicode 17.0 code chart (unicode.org/charts/PDF/U11380.pdf, page 1358):
U+113D8 is **TULU-TIGALARI SIGN SHRII PUSHPIKA** - a decorative auspicious-word
punctuation mark, the same kind of thing as U+113D7 OM PUSHPIKA right next to it
(and structurally analogous to Kannada's own "ARCHAIC SHRII" at U+0CDC, also a
non-compositional auspicious-word ligature-turned-single-character). It is not a
sha+ra+ii-matra conjunct at all, despite the glyph name.

Not fixed in the UFO (out of scope here - purely a test-page label fix): the test
page's "Under symbols" section now hardcodes the real Unicode name ("Shrii
Pushpika") instead of deriving a label from the glyph name, so the display is
correct regardless of what the underlying glyph is called. Renaming the actual
UFO glyph (`sha_ra_iiMatra-tutg` -> something like `shriiPushpika-tutg`) is a
separate, still-open cleanup item - flagged here rather than done silently, same
principle as every other naming issue in this doc.

## 10. `blwf` feature added: generic below-base fallback for all 36 consonants (2026-07-17)

Added `generate_blwf_feature.py` -> `tutg_blwf.fea`, merged into
`Ikshu-Regular.ufo/features.fea` right after `akhn`. Per the standard Indic/USE
feature order, `akhn` runs first and claims whatever specific conjunct it
recognizes (452 hand-drawn ligatures); any "conjoiner + consonant" pair `akhn`
doesn't touch reaches `blwf`, which substitutes the consonant for its below-base
("Adi Vottu") allograph - so every one of the 36*36 possible consonant pairs
renders as a shaped stack, not just the ~small fraction with a bespoke ligature.

All 36 consonants have a below-base glyph: 35 via the `{consonant}.below` naming
convention, RA via a documented override (`raMatra-tutg` - a different glyph
entirely, the same fact `generate_akhn_feature.py`'s `TOKEN_ALIASES` already
relies on). Coverage report (regenerated by the script every run): `BLWF_TODO.md`.

**Bug found and fixed before merging:** the first version used a chaining-
contextual single substitution (`sub conjoiner-tutg ka-tutg' by ka-tutg.below;`),
which only replaces the marked glyph and leaves `conjoiner-tutg` itself sitting in
the glyph stream afterward. `conjoiner-tutg` turns out to have real, visible
dotted-circle-style artwork (the intended USE fallback appearance for an
Invisible_Stacker that's never consumed) - so every below-base conjunct rendered
with a dotted circle glaring out of it, confirmed both via `uharfbuzz` (shaped
glyph list still contained `u113D0`, the conjoiner) and visually (screenshot of
the "Ye Dharma Hetu" verse's `mahāśramaṇaḥ`, and the full Conjunct Matrix grid).
Fixed by switching to a real ligature substitution (`sub conjoiner-tutg ka-tutg by
ka-tutg.below;`, both inputs consumed into one output glyph) - same rule shape
`akhn`'s own ligatures already use. Re-verified with `uharfbuzz` (conjoiner no
longer appears in the shaped output for any tested pair, dedicated `akhn`
ligatures like KA+KA still correctly take priority over the fallback) and
Playwright screenshots (dotted circle gone from both the sample verse and the
full 36x36 Conjunct Matrix).

**Made reproducible for a from-scratch build (2026-07-17):** `blwf` had only been
hand-merged into the already-built `Ikshu-Regular.ufo/features.fea`, not wired into
`build_ufo.py`'s pipeline - a from-scratch rebuild off a fresh/raw UFO would have
silently produced a font missing `blwf` entirely. Added `generate_blwf_feature.py`
and `merge_blwf_feature.py` as real pipeline steps. Also renamed `merge_features.py`
-> `merge_akhn_feature.py` for symmetry (it had been the generic name back when
`akhn` was the only merge step; keeping one generic and one feature-specific name
once a second merge script existed was an inconsistency, not a deliberate choice).
Smoke-tested the full 9-step pipeline end to end - both merge guards correctly
skipped (already merged, no duplication), UFO still compiles.

## 11. `.below` glyphs needed GDEF Mark classification + a `_bottom` anchor (2026-07-17)

Found by inspecting the compiled font's actual GPOS/GDEF tables (fontTools +
`uharfbuzz`) after a request to verify GPOS was really working: `blwf`'s rule is a
plain ligature substitution (`conjoiner + consonant -> consonant.below`) - it swaps
in the below-base glyph but does no positioning. Without a `_bottom` anchor pairing
to the preceding base's own `bottom` anchor (added by `generate_anchors.py`),
HarfBuzz had no attachment point to snap it to, so every `blwf`-substituted
below-base form was rendering at normal advance-width position (`x_advance` = its
own natural width) instead of stacking under the previous consonant like every
other mark on this font.

Confirmed via `uharfbuzz` before the fix: shaping KHA+conjoiner+PA (no dedicated
`akhn` ligature, falls through to `blwf`) showed `pa-tutg.below` was not GDEF-
classified as Mark. After: `classify_blwf_marks.py` sets `public.openTypeCategory =
"mark"` and a `_bottom` anchor (x = own bbox center, y = own bbox **top** edge - the
same "Lego block" fit already used by every other `_bottom`-anchored mark on this
font, e.g. `anudatta-tutg`) on every glyph in `consonant_below_base` (60 of 61,
excluding `ya-tutg.below` per project owner - it's a ligature-only construction
piece, not meant to independently attach as a generic fallback target). Re-verified:
`pa-tutg.below` now GDEF-classified Mark, `x_advance` is `0`, and shaping produces a
real non-zero attachment offset (`x=-695, y=39`) instead of sitting at default
position - confirmed both via `uharfbuzz` and Playwright screenshots of the full
Conjunct Matrix (below-base forms now visibly tucked under the preceding consonant
across the whole 36x36 grid, not just adjacent at normal spacing).

Added as its own `build_ufo.py` pipeline step (`classify_blwf_marks.py`, right
after `generate_anchors.py`), not folded into `generate_anchors.py` itself - keeps
this below-base-specific concern separately reviewable/revertable from the main
anchor plan.

**Other things checked at the same time, found NOT to be problems:** anchor naming
convention (mark anchors ARE correctly `_`-prefixed to pair with their base's plain
name everywhere an anchor exists - `_bottom`/`_top`/`_topright`/`_bottomright` on
marks, `bottom`/`top`/`topright`/`bottomright` on bases) and anchor Y-placement
"Lego fit" (every existing `_bottom`/`_top`-anchored mark already sits at the
correct edge of its own bounding box, confirmed by checking every underscore-
anchored glyph in the font against its own bbox) were both already correct before
this fix - the real gap was specifically the missing classification + anchor on
`.below` glyphs, not a systemic naming or placement bug.

## 12. `akhn`'s below-only promotion reversed: `ha_ra-tutg`/`pa_ra-tutg` are genuinely missing (2026-07-17)

Followed up on section 1&2's own flagged-but-unverified caveat about the
`.below`-promotion mechanism. Project owner confirmed it's wrong: `ha_ra-tutg.below`
and `pa_ra-tutg.below` are below-base-only construction pieces (they're classified
`conjunct_ligature`, not `consonant_below_base` - not touched by item 11's fix),
not stand-ins for the real bare `ha_ra-tutg`/`pa_ra-tutg` ligatures. Those two
bare glyphs simply don't exist yet and need to be drawn.

**First confirmed there were no OTHER cases of this pattern** (asked, before
changing anything): scanned all 452 `akhn` rules for outputs ending in `.below` -
found exactly these same 2, nothing new. Also confirmed no cross-contamination
with item 11's fix (`classify_blwf_marks.py` only reads `consonant_below_base`;
these two are `conjunct_ligature`) and that both compile as GDEF `Base` (correct
for a ligature output), not `Mark`.

**Fix:** removed the below-only-promotion branch from `generate_akhn_feature.py`
entirely (previously: a lone `.below` alt with no bare sibling got silently
promoted to serve as the default). Now falls through to the same
"no default exists, skip and report" path every other unparseable name already
takes. Result: 450 rules (down from 452), 3 skipped (`ka_iMatra_dotreph-tutg` plus
these two, up from 1).

**Gotcha found while verifying the fix actually took effect, then fixed
properly:** regenerating `tutg_akhn.fea` alone did nothing to the real font -
`merge_akhn_feature.py`'s idempotency guard only checked whether `features.fea`
had ever been merged before (`"languagesystem tutg dflt" in features`), not
whether the merged content was *stale* relative to a changed generator output.
The two obsolete rules were still sitting in the already-merged
`Ikshu-Regular.ufo/features.fea` until removed by hand this one time. Since this
would silently bite again on any future edit to `generate_akhn_feature.py` or
`generate_blwf_feature.py` that changes existing rules (not just adds new ones),
rewrote both `merge_akhn_feature.py` and `merge_blwf_feature.py`: instead of
skip-if-a-block-already-exists, they now detect an existing block and *replace*
it in place with whatever the generator currently outputs (byte-comparing first
so an unchanged run is still a no-op, not a needless rewrite). Verified three
ways: (1) both scripts report "already matches - nothing to do" against the
current, already-correct UFO; (2) a synthetic test - hand-injected one of the
just-removed stale rules back into the merged `features.fea`, reran
`merge_akhn_feature.py`, confirmed it detected the mismatch, replaced the whole
block, and produced output byte-identical (`md5sum` match) to the pre-test
correct state; (3) the full 10-step `build_ufo.py` pipeline and `compile_font.py`
still run clean end to end.

Re-verified via `uharfbuzz` after removing the stale rules by hand and
recompiling: HA+conjoiner+RA and PA+conjoiner+RA now correctly fall through to
`blwf`'s generic RA fallback (`raMatra-tutg`) instead of the removed ligatures.

**One more gap surfaced in the process, NOT fixed (flagging, not silently
patching):** `raMatra-tutg` itself has zero anchors and isn't GDEF-Mark-classified
- shaping HA+RA now shows it at `x_offset=0, y_offset=0, x_advance=50` (sitting at
normal inline position with its own small advance width, not snapped under HA via
GPOS). It's the same category of problem item 11 just fixed for `consonant_below_base`
glyphs, but `raMatra-tutg` lives in a different classification bucket
(`vowel_sign_component`) that `classify_blwf_marks.py` doesn't touch. Since RA is
the only consonant using this naming pattern instead of `.below` (see
`generate_blwf_feature.py`'s `BELOW_FORM_OVERRIDES`), this is a single-glyph fix if
wanted - not addressed here since it wasn't what was asked.
