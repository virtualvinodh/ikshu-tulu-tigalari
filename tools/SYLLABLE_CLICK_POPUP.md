# Click-a-Syllable Variant Popup

Reference for the click-a-syllable-for-alternates feature in `glyph_test_page_template.html`,
shared by the **Sample Text** tab (per word) and the **Live Input** tab (the whole typed
text at once) via `renderSyllableSpans(container, cps)`. Built up incrementally over one
long session (2026-07-23/24) - this doc collects the final design in one place instead of
leaving it scattered across commit messages.

## What it does

Every akshara (syllable cluster) in the rendered text becomes its own clickable `<span>`.
Clicking one that has real alternatives opens a small popup of glyph previews - pick one
and just that occurrence re-renders with the alternate codepoint sequence, leaving
everything else in the passage untouched.

```
segmentSyllables(cps)              - split a word's cps into aksharas
  -> resolveSyllableAlternatives(segment)   - build every CANDIDATE option (sync, cheap)
       -> openSyllablePopup(span, segment)  - shape each candidate through the real font,
                                              collapse visually-identical ones, render the grid
```

## Segmentation - `segmentSyllables(cps)`

Walks a word's codepoints left to right. A segment starts at either:

- **A consonant** - optionally chaining `conjoiner + consonant` further (a multi-consonant
  cluster), then absorbing trailing non-base codepoints (vowel signs, VS selectors, marks).
- **A lone independent vowel** (`a-tutg`, `aa-tutg`, ...) - no chaining, but same trailing
  absorption.

Anything else (space, punctuation, a stray mark with no base before or after it) becomes
its own single-codepoint, non-clickable segment.

**Repha is a special case.** It's typed *before* the consonant it attaches to - the
opposite direction of every other mark handled here - so a Repha immediately followed by a
consonant is recognized as a *prefix* of that consonant's segment, not a segment of its
own. Two bugs had to be fixed to get this right:

1. The original code treated Repha as its own isolated, non-clickable segment, with the
   following consonant starting a separate segment.
2. Even after prefixing Repha onto the *next* segment, the *trailing-absorption* loop
   (which sweeps up "anything that isn't a consonant/vowel" onto the *preceding* segment)
   had no exception for Repha - so `AA + Repha + MA` wrongly absorbed Repha into `AA`'s
   trailing marks instead of leaving it for `MA`. Fixed by making that loop stop before
   swallowing a Repha that has a consonant right after it (Repha never appears without one).

Each segment carries: `cps`, `consonantNames` (stripped, no `-tutg`), `baseName` (stripped
independent-vowel name, or null), `hasRepha`, `conjoinerPositions` (indices *within* `cps`,
right at the conjoiner itself), `consSpanLen` (how many leading cps are the
Repha/base/conjoiner chain, before any trailing vowel-sign/mark codepoints).

## Populating the popup - `resolveSyllableAlternatives(segment)`

Returns `[{label, cps, isDefault}, ...]`. Order, and where each block of options comes from:

1. **Strip an already-applied VS.** If the segment's typed text already contains a
   variation selector (e.g. someone pasted `RA+UU+VS11`, the already-alt1-selected
   `ra_uuMatra-tutg.alt1`), it's removed before anything else runs. Otherwise "Default"
   would just echo the alt-selected form back, and every option below would get a
   *second*, duplicate VS stacked on top of the one already present.
2. **Default** - the (now VS-stripped) segment as-is.
3. **Whole-cluster registered alt** - looks up `variant_lookup[consonantNames.join('_') +
   '-tutg']`. When `hasRepha`, the name is prefixed with `ra_` instead (Repha+consonant(s)
   is really `RA+conjoiner+consonant(s)` under the hood - that's what `akhn` actually forms,
   e.g. `sub repha-tutg.alt1 ma-tutg by ra_ma-tutg;`) - this is how `ra_ma-tutg.alt1`,
   `ra_va-tutg.alt1` etc. get found for a typed Repha syllable. A `ra_`-prefixed entry's own
   `cps` already starts with the Repha codepoint itself (the registry records "what you'd
   actually type"), so it must *not* also get the Repha prefix re-added, or Repha would be
   duplicated.
4. **`Repha=RA+conjoiner`** (only when `hasRepha`) - reverts just this one syllable to its
   raw, non-Repha form. An instance-level override, independent of the passage-wide
   Repha On/Off toggle.
5. **Vowel-sign-ligature fold (whole-cluster only)** - when the trailing marks start with a
   real vowel sign (U, UU, ...), looks up `variant_lookup[consonantNames.join('_') + '_' +
   vsToken + '-tutg']` (e.g. `sa_ta_uMatra-tutg` - a dedicated shape for that specific
   2-consonant cluster taking U). Pushed here as a standalone option, unconditionally.

   The OTHER naming pattern - the **last consonant alone** folded with the vowel sign
   (e.g. `sha_uMatra-tutg` - SHA's own U-compound, independent of whatever precedes it) -
   is deliberately *not* pushed here; it's folded into the cross product below instead
   (see point 6). Missing this pattern entirely silently drops real registered alts -
   confirmed for `KA+SHA+U` (`sha_uMatra-tutg.alt1` exists but was only findable this way).
6. **Full cross product** - for clusters of 2+ consonants, or any Repha syllable (even a
   single consonant, since Repha now contributes its own dimension): every independent
   per-consonant variant choice **crossed with** every independent per-conjoiner
   forced-subjoin choice **crossed with** Repha's own variant **crossed with** the last
   consonant's own vowel-sign-ligature-fold alt (see below). Each dimension is `[{no
   change}, {choice A}, {choice B}, ...]`; the Cartesian product across all dimensions is
   generated, and each non-all-default combo becomes one option (labeled with the
   comma-joined list of non-default choices, e.g. `"da=da-tutg.alt2, ra=ra-tutg.alt1,
   conj1=sub"`). This replaced an earlier version that only ever offered one change from
   Default at a time - confirmed missing both "subjoin every conjoiner at
   once" and "combine multiple consonants' variants simultaneously".

   Repha's own dimension is narrowed to *just* its VS2 alt, not the full `{default, alt1,
   alt2}` set: Default and an explicit VS1 both already resolve to `alt1` via `akhn`'s
   unconditional `REPHA_FIRST_RULE`, so a VS1 dimension value would be pure redundancy with
   Default. VS2 is the only state actually worth offering as a combinable choice.

   The last-consonant vowel-sign-ligature-fold dimension (e.g. `ta_uMatra-tutg.alt1`,
   `sha_uMatra-tutg.alt1`) has to live here, combinable with subjoin-force, rather than as
   its own standalone option - confirmed for `NA+conj+TA+U`: `ta_uMatra-tutg.alt1` (VS11) is
   a complete no-op *on its own*, because `na_ta-tutg` is one of the 167 ligatures
   `TutgBlwfDecompose` unships back to raw consonants whenever a vowel sign follows (it has
   no dedicated `na_ta_uMatra-tutg` compound of its own) - `TA+U` then re-ligates *directly*
   to its below-form via the 3-glyph compound rule, so `ta_uMatra-tutg` never exists as its
   own plain glyph at any point for `TutgConjunctVariantSelect` (which runs earlier, in
   `akhn`) to select an alternate of. The alt only actually renders (via the alt-aware
   subjoiner rules in `generate_blwf_feature.py` - see below) when **combined** with a
   forced subjoin: `NA+conj+VS1+TA+U+VS11` → `ta_uMatratutg.alt1.below.auto`. Generating it
   standalone would have been dead weight in exactly the cases that need it most - and it
   turned out this affected `KA+SHA+U` too (an earlier "fix" for that case was verified only
   by checking the JS constructed the right input codepoints, not by actually shaping it -
   `sha_uMatra-tutg.alt1` was *never* reachable standalone there either).

   Building this dimension surfaced a real bug worth calling out: `alt.cps[1]` (used to
   pull the VS codepoint out of a registered alt) assumed a 2-element array (`[baseCp,
   vsCp]`), true for a single-consonant entry, but a multi-glyph compound's `alt.cps` is
   longer (`ta_uMatra-tutg.alt1`'s is `[TA, U, VS11]`) - `[1]` silently grabbed `U` itself
   instead of the VS, duplicating U rather than inserting a selector. Fixed to
   `alt.cps[alt.cps.length - 1]` everywhere - the VS is always the last element, regardless
   of how many base glyphs precede it.

   Combinatorics matter here: a 3-consonant cluster with 2 conjoiners, where all 3
   consonants each have 2 registered variants, is `2² (conjoiner states) × 3³ (per-consonant
   default+2 choices) = 108` raw candidates. Real text rarely stacks that many variant-bearing
   consonants in one cluster, but it's not bounded - see Collapsing below for why this is
   still tractable.

`renderSyllableSpans` calls this same function synchronously (cheap - no shaping) just to
decide whether a syllable gets the `.has-alts` dotted-underline affordance
(`resolveSyllableAlternatives(segment).length > 1`) - single source of truth shared with the
popup itself, so the two can never disagree about *which* options exist (only about which
of them turn out to be visually distinct - see the sync/async gap noted below).

## Collapsing - HarfBuzz-wasm shape-and-dedupe

The cross product above generates *typeable sequences*, not *distinct renderings* - plenty
of raw candidates turn out to be no-ops (forcing a subjoin the font already applies by
default, or a VS that has nothing left to select once some other rule already consumed its
target). `openSyllablePopup` shapes every candidate through the actual compiled font and
keeps only one representative per distinct visual result before rendering the grid.

### Getting HarfBuzz into the page

`tools/harfbuzzjs_vendor/` holds an unmodified copy of `harfbuzzjs`
(github.com/harfbuzz/harfbuzzjs, MIT) - `harfbuzz.wasm`, `harfbuzz.js`, `index.mjs`.
`compile_test_page.py` embeds all three (`harfbuzz.wasm` as base64, the two JS files as raw
source) as `<script type="text/plain">` blocks, alongside a duplicate of the font's own
base64 (already embedded for `@font-face`) so JS can get at the raw font bytes too. Nothing
is fetched over the network at runtime - the whole page stays a single, offline-capable file.

`index.mjs` is a normal ES module: `import createHarfBuzz from "./harfbuzz.js"`, and at its
own top level, `init(await createHarfBuzz())` with no options. Neither resolves correctly
when loaded from a Blob URL instead of a real file - the relative import has nothing to
resolve against, and a no-args `createHarfBuzz()` would try to `fetch("harfbuzz.wasm")`
relative to *its own* blob URL and fail. `initHarfBuzz()` patches both at load time (string
substitution on the source text, not by editing the vendored files):

- the import is repointed at `harfbuzz.js`'s own Blob URL, and
- `createHarfBuzz()` is called with emscripten's official `instantiateWasm` hook, which
  bypasses every internal fetch/`locateFile` code path entirely and just instantiates the
  wasm bytes already sitting in memory (via `window.__HB_WASM_BYTES__`).

The result is cached (`hbReadyPromise`) - only initialized once per page load, then reused
for every popup open.

### `shapeSignature(cps)`

Shapes `cps` and returns a compact string built from each output glyph's outline + advances
+ offsets. Two cps sequences with the same signature render identically, regardless of how
different their *input* codepoints were. Two refinements on top of the naive version:

- **Drop zero-footprint glyphs.** An unconsumed Unicode variation selector
  (`Default_Ignorable_Code_Point`) doesn't vanish from the shaped output - HarfBuzz
  substitutes the font's own `space` glyph as its "render nothing" placeholder rather than
  omitting a glyph entry. Confirmed comparing `DA+conj+RA+UU` against `DA+conj+RA+UU+VS11`
  (a VS11 with nothing left to select, since `RA` already ligated into `da_ra-tutg` before
  the vowel-sign compound it would have modified could ever form): identical real glyphs,
  plus one extra trailing `(space, 0, 0, 0, 0)` in the second - invisible, but different
  enough to block collapsing without this filter. A glyph with `x/y advance` **and** `x/y
  offset` all zero is dropped before building the signature; a real mark glyph essentially
  never lands at `(0,0,0,0)` simultaneously (GPOS positions it somewhere specific relative
  to its base), so this is a narrow, safe filter.
- **Compare by outline, not glyph ID.** Two *different* glyph IDs with byte-identical drawn
  outlines (e.g. `repha-tutg.alt1`/`.alt2`, currently an exact duplicate - see
  `duplicate_glyph.py`) count as the same glyph. Each glyph's outline path
  (`font.glyphToPath(glyphId)`, cached per ID) is used in the signature instead of the raw
  numeric ID. This is deliberately general, not a hardcoded repha-specific exception -
  it'll catch any future glyph that's a genuine visual duplicate of another, and stops
  collapsing on its own the moment someone gives `alt2` its own real artwork (its path will
  then legitimately differ).

### Collapse to nothing

If every candidate (including all cross-product combos) shapes identically to Default,
`deduped.length <= 1` and the popup is hidden entirely rather than shown with one pointless
cell.

### Async races

Shaping is async (`await Promise.all(...)`), so a user clicking a different syllable (or
the same one again) while a previous shape-and-dedupe run is still in flight must not let
that stale run overwrite whatever the panel is showing by the time it resolves.
`syllablePopupToken` is bumped on every open; each run captures its own token and bails if
a newer one has since started.

## UI

- One shared floating panel (not one per syllable - some passages run to 1000+ words),
  repositioned via `getBoundingClientRect()` of whichever span was clicked.
- Fixed 5-per-row CSS grid (`grid-template-columns: repeat(5, auto)`), not `flex-wrap`'s
  "however many fit" - added specifically to gauge, visually, how large the full
  combinatorial cross product actually gets in practice before deciding whether a flat list
  even scales (it mostly does: real text rarely stacks enough variant-bearing consonants in
  one cluster to matter, and the shape-and-dedupe step above trims a lot of the raw count
  anyway).
- **No visible text label** under each glyph option - removed per project owner request;
  each option's label is kept as a native `title` hover tooltip instead, so the grid stays
  glyph-preview-only.
- `panel.style.display` must literally match the CSS rule's `display` value (currently
  `grid`) - an inline style always wins over a stylesheet rule, and this bit twice already
  (once shipping `'block'` while the CSS said `flex`, later while it said `grid`).

## Known limitations

- **The `.has-alts` affordance is a sync guess; the real answer is async.** A syllable
  whose *only* extra option is a subjoin-force that happens to be a no-op will still show
  the dotted underline (decided cheaply, before shaping), but clicking it produces no popup
  once HarfBuzz confirms everything collapses to Default. Making the underline itself
  accurate would mean shaping every candidate for every syllable in a passage up front -
  not worth it for a cosmetic mismatch that only shows up in this one narrow case.
- **A VS11/VS12 selecting an alt of a compound that never forms in its plain/default form is
  a silent no-op standalone, not an error - but it may still be reachable combined with a
  forced subjoin.** Two different reasons a compound like `ta_uMatra-tutg` or
  `ra_uuMatra-tutg` might never exist as its own plain glyph for `TutgConjunctVariantSelect`
  (which runs early, in `akhn`) to select an alternate of:
  - The trailing consonant's cluster-partner has its own dedicated ligature that's in
    `TutgBlwfDecompose`'s trigger list (e.g. `na_ta-tutg`, `ka_sha-tutg` - no dedicated
    compound of their own for U/UU/Vocalic-R/Vocalic-RR) - decomposed back to raw
    consonants and re-ligated *straight* to the compound's below-form, bypassing the
    plain-name step entirely. **This case is now reachable** - see the last-consonant
    vowel-sign-ligature-fold cross-product dimension above, plus the alt-aware subjoiner
    rules in `generate_blwf_feature.py` - combining a forced subjoin with the VS selector
    (e.g. `NA+conj+VS1+TA+U+VS11`) correctly produces `ta_uMatratutg.alt1.below.auto`.
  - The trailing consonant's cluster-partner has a dedicated ligature that's *excluded* from
    `TutgBlwfDecompose` entirely (e.g. any `..._ra-tutg`/`..._ya-tutg` conjunct - RA/YA rely
    on their own `bottomright`/`_bottomright` GPOS anchors for a following vowel sign, not
    GSUB compound formation, per `DECOMPOSE_EXCLUDE_LAST`). **This case has no fix** - the
    compound genuinely never forms via any GSUB path, forced-subjoin or not, so the VS
    selector has nothing to ever attach to. Shape-and-dedupe correctly collapses it into
    Default regardless (see the zero-footprint filter above), but the option is still
    *generated* as a raw candidate first, since `resolveSyllableAlternatives` can't know in
    advance which of these two buckets a given cluster falls into.
- **Selecting Repha's VS2 (`alt2`) can break ligature formation.** The `akhn` rule forming
  e.g. `ra_ma-tutg` only matches `repha-tutg.alt1` specifically (`sub repha-tutg.alt1
  ma-tutg by ra_ma-tutg;`) - if Repha resolves to `alt2` instead, that rule simply doesn't
  fire, and the consonant renders unligated next to a bare `repha-tutg.alt2` glyph. Not a
  bug in the popup - it's shaping the request faithfully - but worth knowing before
  treating `alt2` as a drop-in cosmetic swap for `alt1`: right now it only behaves that way
  where no dedicated Repha-ligature exists for that consonant in the first place.
