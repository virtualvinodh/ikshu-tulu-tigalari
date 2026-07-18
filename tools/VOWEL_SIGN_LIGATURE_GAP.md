# Conjunct ligature + U/UU/Vocalic-R/Vocalic-RR gap

**Bug, confirmed 2026-07-17 via `uharfbuzz`:** typing a 2+ consonant conjunct that
has its own dedicated `akhn` ligature, followed by U/UU/Vocalic R/Vocalic RR,
produces a bare/default vowel-sign glyph instead of the per-consonant ligating
form these 4 vowel signs are supposed to use (per the shaping model - "Below +
ligating right" category, shape changes per host consonant).

Example: `KA + conjoiner + KA + U` (U+11392 U+113D0 U+11392 U+113BB) shapes to
`['ka_katutg', 'u113BB']` - `ka_ka-tutg` forms correctly, but `U` is left as its
own untouched, unattached glyph.

## Root cause

`akhn`'s lookup is sorted longest-input-first and applied in one pass, so
`KA+conjoiner+KA` (3 glyphs) collapses into `ka_ka-tutg` before there's any
chance to check for a 4-glyph `KA+conjoiner+KA+U -> some-compound-glyph` rule -
and no such compound glyph exists anyway. Checked systematically:

- **250** default-form `conjunct_ligature` glyphs total.
- **235 of 250** have no dedicated `<ligature>_uMatra-tutg` / `_uuMatra-tutg` /
  `_rVocalicMatra-tutg` / `_rrVocalicMatra-tutg` compound glyph at all (accounting
  for known naming aliases, e.g. `UuMatra` for `uuMatra`) - this isn't a rare
  edge case, it's the overwhelming majority.

## Proposed fix (not yet implemented) - decompose, re-ligate, re-shrink

Since every consonant (except one exception, see below) already has its OWN
dedicated `<consonant>_uMatra-tutg` etc. ligature, the fix doesn't need new
artwork - it needs to get the vowel sign to "see" the *last* consonant of the
conjunct again after `akhn` has already merged it away:

1. **New contextual decompose lookup**, applied after `akhn`'s main ligature
   lookup: `sub ka_ka-tutg' lookup Decompose_ka_ka U/UU/VocR/VocRR;` - only when
   immediately followed by one of the 4 vowel signs, decompose `ka_ka-tutg` back
   into its raw `ka-tutg conjoiner-tutg ka-tutg` sequence (reusing each
   ligature's own akhn input sequence from `tutg_akhn_rules.json` - already have
   this data, same source used for the `blwf` ligature rules).
2. **Re-ligation lookup**, applied right after the decompose, that re-runs just
   the "consonant + vowel sign -> compound ligature" substitutions (a subset of
   `akhn`'s own rules) - so the now-exposed last consonant + the vowel sign
   ligate into `<last-consonant>_uMatra-tutg` etc., same as if it had been typed
   alone.
3. **Already built and working**: `blwf`'s existing per-ligature rule
   (`conjoiner + <ligature> -> <ligature>.below[.auto]`) then picks up
   `conjoiner + <last-consonant>_uMatra-tutg` and shrinks it into its below-base
   miniature, stacking below the earlier (unchanged) part of the conjunct.

End-to-end for the example: `ka_ka-tutg + U` -> decompose -> `ka-tutg conjoiner-tutg
ka-tutg + U` -> re-ligate -> `ka-tutg conjoiner-tutg ka_uMatra-tutg` -> blwf ->
`ka-tutg conjoiner-tutg ka_uMatra-tutg.below[.auto]` (final: KA full-size, the
second KA+U shrunk and stacked below it) - correctly shaped, matching what a
single `KA+U` (no conjunct) already looks like today, just shrunk.

## Verified before proposing this

Checked whether decompose+re-ligate would actually fully resolve every affected
case, not just the example - corrected 2026-07-18: the first pass of this check
wrongly reported NYA as missing its UU compound because it checked for
`nya_uuMatra-tutg` (lowercase) - the real glyph is `nya_UuMatra-tutg` (capital U,
the exact same typo `names_override.json`'s `token_aliases` already documents as
an alias for `uuMatra`). Re-checked accounting for that alias (and any other
known token alias that resolves to one of the 4 vowel-sign roots):

- **All 36 consonants** have all 4 compounds (`uMatra`/`uuMatra`/`rVocalicMatra`/
  `rrVocalicMatra`, allowing for known naming aliases) - zero gaps.
- **All 235** affected conjunct ligatures would be fully fixed by decompose +
  re-ligate - no exceptions.

## Not yet implemented

This needs: a new script (or extension to `generate_akhn_feature.py`) to build
the decompose lookup + contextual invocation + re-ligation lookup, correct
insertion into `features.fea` relative to the existing `akhn`/`blwf` blocks
(decompose+re-ligate must run between them), and end-to-end `uharfbuzz`
verification across all 234 fixable ligatures before merging.
