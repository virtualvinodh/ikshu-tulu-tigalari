# Below-base ("miniature") glyph scale research

**Question:** are the `.below` glyphs (the below-base conjunct forms every consonant
needs for vertical stacking, per the shaping model) simple scaled-down copies of
their own base glyph, or independently drawn shapes? This matters for any GPOS/
anchor-scaling logic that assumes a uniform shrink factor across the below-base set.

**Method:** for each of the 36 consonants, read its `X-tutg.below` glyph's `.glif`
file directly and check whether it's built from a single component referencing its
own base glyph (`<component base="X-tutg" xScale="..." yScale="..."/>`) versus
having independently drawn contours of its own. Verified 2026-07-17 against the
live `Ikshu-Regular.ufo` (re-checked, not just recalled from an earlier pass - see
counts below for the one correction over an earlier informal tally).

## Result: most are scaled-down copies, four are not

**31 of 36** consonants use a literal scale-down component reference to their own
base glyph - genuinely shrunk, clustered tightly around **~86%**, not full size:

| Scale factor | Count | Consonants |
|---|---|---|
| 0.8630 | 26 | KA, KHA, GHA, NGA, TTA, TTHA, DDA, DDHA, NNA, TA, THA, DA, DHA, NA, PHA, BA, BHA, MA, LA, VA, SSA, SA, HA, LLA, RRA, LLLA |
| 0.8585 | 4 | CA, CHA, JHA, NYA |
| 0.8621 | 1 | JA |

**1 consonant (PA)** has a single self-referencing component too, but at
`xScale="1.0"` - genuinely **unscaled**, full size, not a miniature at all.

**3 consonants (GA, YA, SHA)** are independently drawn - their `.below` glyphs have
their own contours, not a scaled component reference to the base:
- **GA** and **SHA** still land close to the ~86% norm by eye, just not built as a
  literal scaled copy.
- **YA**'s below-form is a genuinely different allograph - taller/narrower than its
  base, not a miniature of it.

**1 consonant (RA)** has **no `.below` glyph at all** - it uses `raMatra-tutg`
instead (RA's dedicated final/combining form), which is wider/shorter than RA's
independent letterform - again a different allograph, not a miniature.

## Tally

- 36 consonants total
- 35 have a `.below` glyph (RA doesn't)
- Of those 35: 32 are built from a single self-referencing component (31 shrunk to
  ~86%, 1 - PA - left at 100%), 3 (GA/YA/SHA) are independently drawn

## Why this matters

Any future GPOS anchor placement or automated scaling logic for below-base stacking
that assumes "every `.below` glyph is its base at a fixed ~86%" would be wrong for
4 of 36 consonants (GA, YA, SHA, RA) - those need their own anchor positions checked
individually rather than derived by applying a uniform scale factor to the base
glyph's anchors.

## Verification tooling

`tools/_selfcheck_render.py` renders a side-by-side comparison strip (full
consonant, its below-base miniature, and a conjunct using it, e.g. `ka-tutg` /
`ka-tutg.below` / `ka_ka-tutg`) under a shared frame, for visual sanity-checking
alongside the numeric component-scale data above.
