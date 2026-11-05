# Roots of Neo-Quenya, Neo-Sindarin and Neo-Primitive Elvish words from Eldamo

*Русская версия: [README.md](README.md).*

`neo-roots.json` gives every word of the lists
[vocabulary-words-nq](https://eldamo.org/content/vocabulary-indexes/vocabulary-words-nq.html),
[vocabulary-words-ns](https://eldamo.org/content/vocabulary-indexes/vocabulary-words-ns.html) and
[vocabulary-words-np](https://eldamo.org/content/vocabulary-indexes/vocabulary-words-np.html) (Eldamo 0.8.13)
its root or set of roots:

| group | words | of which | with roots | through `deprecated`/cognate/struck |
|---|---|---|---|---|
| `nq` Neo-Quenya | 6060 | NQ. 2961, Q. 2058, ᴹQ. 1041 | 5530 | 70 |
| `ns` Neo-Sindarin | 3209 | NS. 1474, S. 1160, N. 575 | 2932 | 128 |
| `np` Neo-Primitive | 1571 | ✶ 969, ᴹ✶ 594, N✶ 8 | 1250 | 9 |

Besides the words of the lists, `words` holds four more kinds of entries, with the same root resolution and trees:

- **deprecated words** (`deprecated: true`) — what Eldamo shows on deprecations-nq/ns/np (`deprecation-index.xq`:
  words of the group's languages with `<deprecated>`, not names, phrases, grammar or phonetics; roots are in the
  root index): 3305 + 3021 + 31, with roots found for 5496. `see_instead` is what Eldamo suggests instead;
- **forms of other conceptions** (`merged_into`) — entries nested in a word's page and merged into it by
  `<combine>` (in Q. cala: ᴹQ. kala and ᴱQ. kala¹; Eldamo shows them on the word's page, under it): 1663 + 940 + 54,
  with roots for 2183;
- **other ⚠️ words outside the lists** (`outside_lists: true`) — words of the group's languages that Eldamo marks ⚠️
  and puts neither in a vocabulary list nor among the deprecated words: early (G. caineglad, ᴱQ., ᴱN., ᴱ✶),
  rejected, deleted, unglossed (the reason is in `warnings`). Not names, phrases, grammar, phonetics, roots or `<see>`
  stubs (those are only other spellings of words present anyway): 630 + 831 + 429, with roots for 1064. On the graph
  they are hidden until their switch is on — except 470 that someone's tree of origin passes through: those always
  show, as before;
- **names** (`name: true`) — names of the group's languages (speech ending in `-name`: 1394 place names, 1247
  masculine, 371 feminine, 851 other proper names, 211 collective ones like Q. Tareldar = tar-¹ + Elda). Eldamo keeps
  them out of its lists, but their elements and derivations are those of words: 1548 + 2370 + 156, with roots for
  3357. On the graph they are hidden until the “names” switch is on (except 388 on someone's way to a root);
  switching it on also brings in the names around the focus — Elda gains Tareldar, Eldarion, Elendil and others.

The counts in `groups` (`count`, `with_roots`, `by_rule`) and the root index are for the words of the lists; the
four other kinds have their own `deprecated`, `merged_forms`, `outside_lists` and `names` in `groups`. Primitive forms written in capitals
(ᴱ√ƷAWAKA) are not among them — they are roots.

It builds in a few seconds with the Python standard library only (Python 3.8 on Windows 7 will do):

```
python neo_roots.py data/eldamo-data.xml neo-roots.json          # all three groups
python neo_roots.py data/eldamo-data.xml ns-roots.json ns        # one group
python show.py --en neo-roots.json palantír huorn miltë          # entries, one line per root
python show.py --en --tree neo-roots.json palantír               # the derivation tree
python show.py --en --root neo-roots.json LUP LAS¹               # an entry of the root index
```

`data/eldamo-data.xml` is the Eldamo 0.8.13 data model from [pfstrack/eldamo](https://github.com/pfstrack/eldamo)
(`src/data/eldamo-data.xml`), © Paul Strack, CC BY 4.0. Any later version of the same file will do.

## The word lists

The same selection as `vocabulary-index.xq` with `id=nq`, `id=ns` and `id=np`: words of nq, q, mq / ns, s, n /
np, p, mp (the page drops eq, en, g and ep), without `<combine>`, `<deprecated>` or `<see>`, without names,
phrases, grammar, phonetics and roots themselves, not `[unglossed]`, and without `-` or `|` in `@mark`. `spelling`
is the form as the list shows it: normalized for NQ (`c:normalize-spelling`: q → qu, k → c, final -e → -ë), as in
the database for NS and NP.

The NP list holds Primitive Elvish *words* (✶galadā, ✶lassē, ✶-i(n)ki); roots are not part of it, they are the
answer. These words also appear in the NQ and NS trees as primitive forms, but only 716 of the 1571 lie on
someone's path to a root. N√GAWAK (a root Eldamo 0.8.13 marks as a noun, and so lists) gets the rule `self`:
it is its own root.

## The file

```json
{
 "source": {"eldamo_version": "0.8.13", "site": "https://eldamo.org"},
 "groups": {"nq": {"count": 6060, "with_roots": 5530, "by_rule": {…}, "uncertain": 70, …}, "ns": {…}},
 "words": [
  {
   "group": "nq", "word": "tyallas", "spelling": "tyallas", "lang": "nq", "lang_name": "Neo-Quenya",
   "speech": "n", "gloss": "(playing) card", "url": "https://eldamo.org/content/words/word-1340155721.html",
   "rule": "elements",
   "roots": [
    {"form": "TYAL", "lang": "mp", "url": "…", "gloss": "play", "part": 0,
     "via": [{"rel": "element", "lang": "q", "form": "tyal-", "url": "…"},
             {"rel": "combine", "lang": "mq", "form": "tyal-", "url": "…"}]},
    {"form": "LAS¹", "lang": "p", "url": "…", "part": 1, "via": […]}
   ]
  }
 ],
 "roots": [ … ]
}
```

- `roots` — the chosen roots. When a word has several parts (a compound), each root has a `part`: roots with
  different `part` add up (√PAL + √TIR, S. huorn = ᴹ√KHUG + √ORO), roots with the same `part` are alternatives
  (Q. alda: √GAL² / ᴹ√GALAD). Without `part`, all roots are alternatives of one part.
- `via` — the chain from the word to the root: `element`, `deriv` (an intermediate form), `combine` (the same word
  in another conception, merged by Eldamo), `see`, `deprecated`, `cognate`. An empty chain means the word itself
  names the root.
- `same_as` — where Eldamo merges the root itself: the chain of its `<combine>` links and the Neo-Primitive root
  it is filed under (ᴹ√LUB² ≡ √LUB³ ≡ N√LUP). The last item is handy for matching roots of different periods.
- `gaps` — parts without a root, in their place (Q. firya = √PHIR + -ya; suffixes, words without an etymology).
- `also` — roots from lower-ranked sources that are not among the chosen ones; each has a `rule` saying where it
  comes from.
- `rule` — the rule that chose the roots; `uncertain` — the chain goes through `deprecated`, `cognate` or a struck
  reference (`struck`; such a root and tree node also carry `struck: true`).
- `cognates` — the Cognates section of Eldamo's page (`allReferenceCognates` + `allWordCognates`: words of other
  languages joined by `<cognate>` through the word's references and the word itself, transitively): S. Edhelharn ~
  Q. Elessar. A comparison, not origin; roots via a cognate are still taken by rule 8 only. 7486 entries have such
  lists. On the graph — a “cognate” link without an arrow (5189 pairs; 682 nodes are known only as someone's cognate —
  T., Ilk. and others — and stay off the origins map); the focus's cognates show at once, and the card has a
  “Cognates” section. The “+N” counters by a label do not count them, a double-click expands them too; in the path
  search a cognate is a loose link (weight 2) and a change of branch. Before, the graph showed a cognate only when a
  way to a root went through it, so S. Edhelharn (its roots by the elements Edhel + sarn) had no Q. Elessar.
- `warnings` — why Eldamo puts ⚠️ before the word on its vocabulary and deprecation pages: `deprecated` (its own
  `<deprecated>`, or that of the word its `<see>` names), `deleted` (`|`), `rejected` (`-`), `doubtful` (`‽`),
  `unglossed`, `early` (ᴱ✶, ᴱN., ᴱQ., G.). Words of the three lists have none (the lists leave such words out);
  deprecated words always have `deprecated`; forms of other conceptions mostly `early`, 72 also `deprecated`.
  `see_instead` can be on forms of other conceptions too (ᴱQ. anda, referring to the deprecated ᴱQ. ande(a), →
  Q. anda). Only two deprecated words have no replacement: ᴹQ. áratenkele and S. dha (`<deprecated/>` without a
  form). On the graph such words carry ⚠ before the label (except forms whose only warning is `early`), and the card
  names the reason and tells “deprecated” from “deprecated, no replacement”.
- `alt_lang` — the language Eldamo prints in brackets after the word's own (`c:alt-lang`): ᴺQ. [ᴱQ.] ulumpë. For a
  neo word marked `^` it is the language of the nested entry merged into it by `<combine>`; for a word without
  references of its own, that of its first nested entry with references in another language. 678 words are
  ᴺQ.[ᴱQ.], 420 ᴺS.[G.], 156 ᴺS.[N.], and so on. Roots of the index follow the rule of `root-index.xq` (a root
  without references: the language of its first nested entry, ᴺ√ [√] LUP).
- `alt_source` — that word itself, the base of the neo word: `{"form", "id"}` (ᴱQ. aiko for ᴺQ.[ᴱQ.] aico). On the
  graph the base comes with the neo word, whatever its kind, and goes with it: often it is the word the neo one
  replaces (685 of 1479), which the “deprecated words” switch alone would hide (ᴱQ. eldasilqe by ᴺQ.[ᴱQ.]
  eldafindë). A base of another form (1057 words) also shows in the path results: “base: ᴱQ. eldasilquë” under
  ᴺQ.[ᴱQ.] eldafindë, unless the path passes through it.

### The derivation tree (`tree`)

The same chosen roots and gaps as nested blocks: a word's block holds its parts (`parts`, one block per element,
in order) or its alternatives (`from`, different derivations); an element's block holds what it comes from, and
so on down to the root: intermediate form → primitive form → root. An element may have elements of its own.

When a word's roots are not chosen by its elements (but by a derivation, an intermediate form and so on) or it has
none, its block still holds its elements (`parts`) beside the derivations (`from`): ᴹQ. mir < ᴹ√MĪ/IMI with the
suffix -r², Q. calima < √KAL with the elements cal- (< √KAL) and -ima, NQ. aialca = ai(a)- + -lka (both rootless).
This does not change the choice of roots (`roots`, `gaps`, `also`); 812 trees are completed this way.

```
python show.py --en --tree neo-roots.json alda estolië
```
```
q alda (n) 'tree'  rule=deriv
   | deriv: p √GAL²  (direct; the same root also through the primitive form)
   | deriv: p ✶galadā
         written PE17/135.4516: galadā > ʒalaðā > ʒalðā > alda
      | deriv: mp √GALAD
      | deriv: p √GAL²
nq estolië (n) 'camp'  rule=cognate ['cognate']
   cognate: s estolad
      [0] element: s estola-
         [0] element: p √ET  — no root  ✗ not matched: ET
         [1] element: p √TOL
```

A node has `rel` — how it links to the block above (`element`, `deriv`, `combine`, `see`, `deprecated`,
`cognate`); `kind` — `root`, `protoform` (a word of a Primitive Elvish language) or `form` (a word or intermediate
form of another language); `form`, `lang`, `url`, `gloss`; a root also has `same_as`. A gap is `"gap": true`; the
root of a part of a partial cognate whose consonants are not found in the word stays in its place with `gap` and
`not_matched`.

`shortcut: true` marks a root the word names directly when, beside it, a derivation reaches the same root through
an intermediate form. Eldamo often records both paths: Q. ‑(n)dur comes from ✶‑ndūr < √(N)DUR (its own `<deriv>`),
while the reference PE17/152 derives *ndur* straight from DUR. Both paths are kept and the direct one is marked as
a shortcut; 1007 words have one (Q. alda: √GAL² directly and through ✶galadā). The flat `roots` list still has
the root once.

`written` — how the word's own references (not those of its inflected forms) write the link to this node: the form
in the source's spelling (`form`), the place (`source`), the form of the reference (`ref`) and the written
intermediate forms that have no pages of their own (`intermediate`, from the primitive form towards the word, as
Eldamo prints ✶v > i1 > i2 > i3 > word). It is given only when it differs from the node's headword by more than
case, √ or a homonym number.

The root's language is always given (`p` — late √, `mp` — ᴹ√ of the Etymologies, `np` — neo, `ep` — ᴱ√): Eldamo
itself links many late words to ᴹ√ roots (Q. lár < ᴹ√DAR), so filter by it if you want late roots only.

## The root index (`roots`)

The roots of the [roots-np](https://eldamo.org/content/root-indexes/roots-np.html) list — the same selection as
`root-index.xq` with `id=np`: roots of np, p, mp and ep without `<combine>` (1932). Eldamo does not separate the
unrecommended roots in that list; it marks them ⚠️. Here that is `recommended: false` plus `warnings` with Eldamo's
reasons: `deprecated` (replaced, itself or the root its `<see>` names; the replacement is in `see_instead`),
`deleted` (`|`), `rejected` (`-`), `doubtful` (`‽`), `unglossed`, `early` (ᴱ√). 1034 roots are recommended.

```
python show.py --en --root neo-roots.json LUP
np LUP 'hump, lump, fat'  recommended
   filed under it: p LUB³, ep ULUN(T), ep ULUMP
   derives from: np PUL
   nq (3): filiculumpe, ulumpë, ulumpembë
   ns (1): lûb
```

An entry has `form`, `lang`, `url`, `gloss` (and `ngloss` if different), `mark`, the status, and also
`merged` (roots of other conceptions merged into this one by `<combine>`: √LAS¹ holds ᴹ√LAS¹ and ᴱ√LASA),
`filed_under` / `filed_here` (the Neo-Primitive root it is filed under, and the roots filed under it), `see`,
`derives_from` (roots the root itself derives from: ᴹ√GALAD < √GAL²) and `derivatives` — the words of the three
lists that have this root among their chosen roots, by group, as links to their entries (`through` when the word
names a root merged into this one: √LAS¹ also gets the words of ᴹ√LAS¹). Trees and glosses of the words are not
repeated; they are in the word entries by `url`. Roots in `also` do not count as derivations.

1072 roots of the list have derivatives; 107 recommended roots have none (no `derivatives` field) — a ready list
for coining new words.

Six roots the words rely on are not in Eldamo's list; they are added with `in_list: false` and a reason in
`not_listed_because`, so that the index covers every word: `merged_into_word` — Eldamo merged the root not into a
root but into a Primitive Elvish word (ᴹ√LŌ → ✶lō¹, ᴱ√SA → ✶sa, ᴱ√LĒ → ✶dē, ᴹ√AKLA(R) → ✶aklar(a));
`combined_with_itself` — its `<combine>` points to itself (ᴹ√LA), and Eldamo's list loses it;
`not_marked_root` — a root marked as a noun (N√GAWAK).

## The graph (`neo-roots-graph.html`)

An interactive d3 page: nodes are roots, primitive forms and words; arrows go from the source to what derives
from it; colour and line pattern show the kind of link (derivation, element, merged form, stub, replacement, root
via a cognate, and for roots — merging, filing under another root, derivation from a root; and cognates — without an
arrow, a comparison rather than origin). The whole graph — 29,249 nodes and 48,684 links, nearly all in one component — is not drawn at once: that would be slow and unreadable.
The page shows a neighbourhood: the chosen word with its tree down to the roots and its nearest derivatives, or a
root with its derivatives two steps deep; double-clicking a node expands its neighbours; “+N” right of a label is
the number of the node's derivatives still hidden, left of it its sources. Shortcuts (`shortcut`) are hidden by default so that the path runs
through the intermediate form; a switch in the legend shows them, and the word's card always lists them, marked
“direct”. Each kind of link can be switched off in the legend. The address `#n-<Eldamo page id>` opens a node
directly; when the page is not on the graph (a phrase, grammar), a note at the bottom says so.

Double-clicking an expanded node again collapses it. There is no ambiguity in what goes: every node on screen
remembers what keeps it — the focus with its tree, or the nodes whose expansion brought it in. Collapsing removes
only what this one node kept, together with whatever those removed nodes had expanded; a node something else
still keeps (the focus, its tree, another expanded node) stays.

The bracketed language (`alt_lang`) shows as on Eldamo: ᴺQ.[ᴱQ.] ulumpë; for roots, only when it differs from the
root's own language (ᴺ√[√]LUP, but not ᴹ√[ᴹ√]DIM).

The “Origins map” view (address `#all-roots`) shows everything the chains of origin start from, with three
independent checkboxes: the roots of the roots-np list (1932), primitive forms without a root (324) and other
words without a root (890). “Without a root” means the node cannot be reached from any root along the links of
origin (an unmatched part of a partial cognate does not count); these are the list words that have no
roots in the JSON and 80 elements outside the lists (suffixes like ᴹQ. -r²). Circles are grouped by kind and first letter; a circle's area is the number of list words
derived from it (for a root, from the index; for the others, how many list words come from it: Q. ‑itë — 76,
✶‑mā — 103). Recommended roots are filled, roots with ⚠ dashed; primitive forms and words take the colour of their
list. Root filters: conception (late √, ᴹ√, ᴱ√, ᴺ√) and “recommended only”; “without derivatives only” applies to
all three kinds (recommended roots without derivatives are the 107 roots nothing has been coined from yet).
Labels appear as you zoom in; a click opens the card, a double-click the node's graph. All origins at once on the
force graph would be a scatter of three thousand unconnected dots, so they are gathered into a map. The map is drawn
on a canvas, only what is on screen: as svg, thousands of circles with labels laid out their text anew at every
step of the zoom, and a frame took tens of milliseconds.

In the graph's legend:

- **deprecated words** — hidden by default; switched on, they show faded, and an “instead” link runs from such a
  word to what Eldamo suggests instead (the card has “Eldamo suggests instead” and “Replaces”). This link is not one
  of origin and is not part of the trees;
- **other ⚠️ words outside the lists** — hidden by default (except those on someone's way to a root); switched on,
  they show faded, with a dashed outline and a ⚠;
- **forms of other conceptions** — a word and the forms nested in it (for roots, the roots merged into it and filed
  under it): the way they are laid out is described below;
- **languages** — by branch (Quenya, Sindarin, Primitive Elvish, other Elvish) with node counts. A hidden language does
  not break chains: a path through hidden nodes shows as one dotted link “through hidden nodes”. The filter also
  applies to the origins map (roots are the languages √, ᴹ√, ᴱ√, ᴺ√). The focus node always shows.

Language markers on the graph are coloured: the hue is the branch (Quenya teal, Sindarin green, Primitive Elvish
violet, other Elvish orange, roots gold), saturation and strength the language's newness: early faintest, neo
deepest on a light page and brightest on a dark one. Arrowheads sit on the node's edge on the side the link comes
from (for a selected node, on its ring).

The layout is computed, not settled by springs. Columns from left to right are stages: root, primitive form, ancient
language (Ancient Quenya, Ancient Telerin, Old Sindarin, Old Noldorin), language (Quenya, Sindarin, Telerin, Noldorin,
neo…); a node stands no further left than its stage and right of all its sources, so a primitive form derived from
the same root as a word is always left of the word. The order within a column is chosen in the legend: **by source**
(the default) — the derivatives of one source together, among them Quenya on top, then Sindarin, other Elvish,
Primitive Elvish; **by branch** — first all Quenya words of the column, then all Sindarin ones and so on, by source
within a branch; **alphabetical**. Each node is put as near its sources as its neighbours allow (three passes: by
sources, by derivatives, by sources again). Only links of origin order the columns: “instead” (a deprecated word and
its replacement) does not, and cycles — 241 in the data, nearly all through “instead”, and two real ones (S. lhaw ~
N. lhewig, Q. tyelpë ~ telpë) — are cut by a depth-first walk. Before, a cycle pushed its nodes 40 columns away: Q.
telpë made a graph 9000 px wide, its derivatives split into two distant columns. Nodes and their labels push each other apart as boxes so as not to
overlap.

Forms of other conceptions are laid out in one of three ways (chosen in the legend): **in bands** (the default) — a
word and its forms of other conceptions share a column, and the conceptions run in horizontal bands: Neo-Eldarin, late,
middle (Etymologies), early. Neo has a band of its own: its words and roots were made by its compilers, not by
Tolkien, and it differs from the late conception as Tolkien's conceptions differ from each other; the bands share
their columns, so a neologism stands above its source (ᴺQ.[ᴱQ.] eldafindë in the column after Q. Elda). A band is as high as its fullest column, and a node never leaves its band, neither in
the layout nor when dragged, so bands do not overlap; **under their word**, as on Eldamo's page; **apart** — as ordinary arrows.

Clicks: one opens the card; two expand the neighbours, two again collapse what that node expanded; three (or the
“Fold derivatives” button) remove everything derived from the node except the focus and its tree of origin — so the
derivatives of the focus word, shown from the start, can be folded too. Dragging moves a node together with what
hangs on it alone (derivatives with no other parent on the graph), with Shift the node alone; what is moved stays
put (thicker outline), and “Re-layout” frees it. There are no springs between nodes, so a moved node is not pulled
back and the others do not shift.

A node's label has two counters of links not shown yet: “+N” on the right counts derivatives (later forms and words
the node is an element of), “+N” on the left sources (earlier forms, elements, forms merged into it, cognates, the
root it is filed under) — the same sides the layout puts them on. A double-click with Shift expands the derivatives
only, with Ctrl (or Alt, ⌥) the sources only; with nothing to expand on that side it collapses what the node
expanded. The card has the same as the “← Sources” and “Derivatives →” buttons. Cognate links need no special
handling: on the graph a cognate stands only on the way to a root, so it is always a source.

Links go around nodes and their labels (their own ends' labels too). A link is drawn as a plain S-curve as long as it
misses every node on its way. Where it would cross one, a passage is found first: through a stretch (a column of
nodes) by one point at the free height nearest its course, or, failing that, level; at its own ends the link eases
into the gap around their height. Once the graph settles, the smoothest curve is drawn along that passage: the taut
string through the corridor between the nodes (it goes round only the corners it must), and through its bends a
cubic with the slope of the side the node stands on, so the turn begins only past it; if that curve clips anything,
the passage stays. Besides, the gap between two columns widens with the steepest drop of a link across it (a link over
several columns shares its drop among them): on √ET the descent from Q. et to its derivatives used to be squeezed into
a narrow gap and turned sharply right before the node. While the nodes move (layout, dragging) links are
plain S-curves; the routes and their smoothing are computed when the graph comes to rest: on every frame they took
nearly all of a layout's time (168 nodes: 4.9 of 6 s of script, now 0.6 s). The corridor of a long link takes only
the nodes near its course, not every node of its columns, and the nodes are pushed apart by a sweep along x, not by
comparing all pairs: a view of 1719 nodes stalls 0.27 s after it comes to rest instead of 3 s.

The graph, like the origins map, is drawn on a canvas; the svg over it is empty and takes the pointer (zoom, pan,
picking a node or a link by its geometry, dragging). As svg, each step of a zoom and each frame of a layout laid out
the text of every label anew: a view of 871 nodes laid out at about 30 frames a second, zoomed at about 11 and
stalled 0.64 s after it came to rest; on the canvas, 60 frames, half the work per zoom step and 61 ms. Labels smaller
than 3 pixels on screen are left out (but the focus's and the selected node's), and far out a dashed line is drawn
whole and fainter: dashes shorter than a pixel cannot be seen yet cost thousands of pieces per line. Tips (what the
svg's `<title>` said) show in a small box. A drag begins with the first move: a click no longer pins a node.

A click on a link picks it and both its ends (the rest fades); the card shows the relation, the source, the
derivative and how the link is written in the sources; a click on an empty spot or Esc clears it.

**Vocabulary** (a switch in the legend): “Neo-Eldarin” is like Eldamo's pages with `?neo`: neologisms ᴺQ., ᴺS., ᴺ✶,
ᴺ√, the ⚠ mark, deprecated words and their “instead” replacements; “Tolkien only” is like Eldamo without `?neo` (which
hides everything of class `neo`, `c:is-neo`): neologisms are hidden, and the words Eldamo advises against for
Neo-Eldarin and the other ⚠️ words become ordinary words of their languages — no ⚠, not faded, no “instead” links;
their switches do not apply then. So are the words merged (`<combine>`) into another for Neo-Eldarin: with `?neo`
Eldamo sends their page on to that word (ᴱQ. aiko → ᴺQ.[ᴱQ.] aico), without it each is a word of its own
language. In “Tolkien only” the “merged form” links are not shown and not used by the path search, such words (855
merged into neologisms, the rest into Tolkien's words of the lists) are drawn as ordinary words, not hollow, without
the “form of another conception” mark, the card names neither their merge nor neologisms, and on the origins map
they stand on their own. The marker ᴺQ.[ᴱQ.] belongs to the neologism and is hidden with it. The choice is remembered
in the browser.

**Path between words** (a panel under the search; the ends are picked in the fields or with “path from here” / “path
to here” in a card; address `#path-<A>-<B>-<kind>-<crossings>`). Three kinds:

- **kinship** — the nearest common source: a search up the links of origin from both ends, the source with the least
  sum of the two chains (Q. telpë and S. celeb — ✶kyelepē; Q. Elda and S. Edhel — ✶edelā);
- **origin** — whether one comes from the other, along the links (√GAL² → ✶galadā → alda → aldarembina), either
  way round;
- **any connection** — the shortest chain over all links, both ways.

A step **crossing conceptions** (a merged form, a root of another period, a replacement, a derivation across periods;
a pure neologism ᴺQ., ᴺS., ᴺ✶, ᴺ√ is a conception of its own, Neo-Eldarin, and a word taken into neo from Tolkien,
ᴺQ.[ᴱQ.] aico, has the conception of the language in brackets: ᴱQ. aiko → ᴺQ.[ᴱQ.] aico is no crossing, a ᴺQ. from a
late √ is one) or **branches** (a cognate, a borrowing, “see” between the Quenya and Sindarin
branches; the way through a primitive form does not change the branch: Primitive Elvish is shared by both) is marked
on the graph (dashed) and in the list of steps (“↕ conception changes”, “↔ branch changes”). Crossings: as few as
possible (compared in order: crossings of conceptions, then of branches, then length), none, between branches only,
between conceptions only, or ignored. Link weights: derivation and element 1, merged form 0.5, “see”, cognate and
replacement 2, “instead” 3, struck reference +2; “consonants do not match” is not passable; loose links can be left
out with a switch. The languages and kinds of words chosen in the legend apply. Besides the best path up to two more
are shown (found with extra weight on the links already used), and, when forbidding crossings made the path clearly
longer, the shortest path with crossings too. The path is added to the graph and the rest fades; the search over the
whole graph (28 thousand nodes) is Dijkstra's, milliseconds.

“Export”: the graph on screen as SVG (built from the same data by the same rules of look as the canvas; the file
stands alone), PNG (the canvas painter, at twice the size; a system font stands in when the web font is unavailable) and JSON (nodes with id, form, language,
gloss and Eldamo address, links with relation, marks and written forms); on the origins map, a PNG of the whole map
at 4000×4000. In the artifact the file goes through the host's save (with a confirmation), in the standalone page
as an ordinary download.

The “consonants do not match” mark (`nm`) is put on a graph link only if it fails to match in every tree it
appears in: √MEL → ✶melnā does not match in the tree of S. edhelvein (through the partial cognate Q. vanimelda),
but in the tree of Q. melda it is a real derivation.

```
python make_graph.py neo-roots.json graph_template.html neo-roots-graph.html --standalone
```

`graph_template.html` is the page itself with the placeholders `/*GRAPH*/` and `/*MESSAGES*/`, where
`make_graph.py` writes the graph (4.4 MB) and the interface catalog; without `--standalone` it produces a page
body for a host that adds its own `<head>`. For GitHub Pages the page is built with `--standalone` into `index.html` at the
root of the repository (or in `docs/`, if Pages are set to that folder): the data are inside the page, nothing else
is needed; outside Claude the export saves files as ordinary downloads.

The theme follows the system (or the window the page is open in); the ◐/☀/☾ button by the language button cycles
“auto → light → dark”, and the choice is kept in the browser.

The interface is bilingual, Russian and English, as in Quettamin: the catalog `graph_messages.json`
(`key → {ru, en}`, placeholders `{name}`), static markup marked with `data-i18n` and `data-i18n-attr`, everything
else built through `t(key)`. The language is the one last chosen with the button (kept in the browser), else the
browser's language; switching redraws the page in place and keeps the open graph. Eldamo's data (forms, glosses)
are not translated. A new language is one more field in each catalog entry and in the switch.

d3 7.8.5 loads from cdnjs and the fonts from Google Fonts, so the file needs a network connection.

## Rules, by rank

1. **elements** — two or more elements with roots: the roots by part. Elements come from the entry, or, if it has
   none, from one of its references: among those with the same form (else among all), the one with the most
   elements (G. Tol Erethrin: tol + erethrin from LT1A, not tol alone from GL). A reference whose elements name the
   word itself analyses a form of it (ᴹ✶apparkā, the intensive of ᴹ✶parkā = ᴹ√A + parkā): its other elements are
   that form's affixes, not parts of the word, and are not counted as its roots. A root a reference names in
   place of an element without an etymology takes that element's place if it begins with the same consonant
   (S. huorn: hû¹ → KHUG); affixes are not filled this way.
2. **deriv** — roots named by the word's derivations: the entry's `<deriv>` and `<deriv source>` inside its
   references (by `@source`, as `c:get-ref`). Roots an intermediate form leads to (✶galadā < ᴹ√GALAD) are added as
   alternatives.
3. **element** — one element with a root, the others are gaps.
4. **intermediate** — only through intermediate forms (Q. lassë < ✶lassē < √LAS¹). Intermediate forms of different
   shapes are alternatives of the part with roots: Q. Elda < ✶elenā (= ✶elen < √EL + ✶-ā), and also
   < ✶eledā < √EL, < ✶edelā < √DEL², < ✶edelō < √DEL¹ — √EL, √DEL², √DEL¹ are roots of one part. (Before
   2026-11-01 the form with more parts pushed the others out, and Elda kept only √EL.)
5. **combine** — through words merged into this one (NQ. hlöa ← Q. hlöa < ✶(s)loga < √LOG).
6. **see** — through a stub reference.
7. **deprecated** — through a word this one replaced. Accepted only if it begins with the same consonant
   (b~v~w, k~c~g~h, p~f, t~d~th, n~ñ, rh~r, lh~l) or both forms begin with a vowel, and the consonants of all its
   roots are found in the word. Older forms of the same word pass (ᴱQ. milt → NQ. miltë; N. lhoch → NS. loch,
   N. rhand → NS. rand, N. tofn → NS. tovn), other words do not (NQ. sin → latúcen, Q. engë → né,
   ᴱQ. wara- → psar-, G. cwiliog → S. calen). A root replaced by a word counts as that word's root only if the word
   begins with the same consonant (ᴱ√SINI → ✶sinki — yes, ᴱ√GWAṘA → psar- — no).
8. **cognate** — through cognates (transitively, as the Cognates section); Elvish languages only, and only roots
   whose consonants (at least two) are found in the word; a part of a compound cognate not found in the word is a
   gap with `not_matched`.
9. **struck** — through the derivations of references Tolkien struck out (`-` in the reference's `@mark`). Eldamo's
   word page lists them among Derivations (`word-page.xq` takes all references there, not only valid ones):
   ᴹQ. Elda < ᴹ√LED (the “departed” Elf, Ety/ELED) and < ᴹ✶edēlā < ᴹ√EDE(L) (EtyAC). Only forms that no valid
   reference leads to are taken; when another rule gave the roots, such paths go into `also` (`rule: struck`) and
   into the tree marked `struck`, and on the graph they are dash-dotted and marked “struck out”. A word whose roots
   go through such a path gets `uncertain: struck`.

The consonant check follows the word's branch: for Sindarin, ch, dh, lh, rh, mh are single sounds, m matches the
labials (lenition m > v), and a velar or y of the root may be missing (medial g, y > i); for Quenya, ngw = ŋg and
gw > w.

To stay careful:

- cognates are not used below the word itself (for elements and intermediate forms), and a cognate's roots found
  through `deprecated` or another cognate do not count;
- a cognate's root goes into `also` only if neither the word nor the cognate is a compound: N. anrand
  (= ann + rand) does not give ᴹQ. randa the root ᴹ√ANAD, S. dagnir does not give Q. nehtar the root √N(D)ER;
- what Tolkien rejected (`-` in `@mark`) does not count unless the word itself is rejected — except the
  derivations of struck references (rule 9), and those only at the lowest rank;
- primitive forms written in capitals count as roots: in 0.8.13 N√GAWAK, ᴱ√ƷAWAKA and ᴱ√OWO are marked as nouns;
- cycles (Q. nelquë ↔ quainel) are cut; the result is deterministic.

## Comparison with Quettamin

Up to version 3.10, root resolution in `quettamin/shared/lexicon.py` agreed with this one for 5588 of 6060 NQ
words and 2914 of 3209 NS words (there were no words where only Quettamin found a root). In 3.10 Quettamin adopted
these rules (9696 matches of 9709 by its changelog), and in 3.11 it took the root index and the tree of origin.
Shortcuts (`shortcut`) appeared here later: Quettamin still merges the alternatives of one part by root
(`shared/lexicon.py`, `alts` and the merge in `_root_groups`), so it loses the path through the primitive form
when the root is the same.

Checked against Quettamin 3.20 (2026-11-01, its `_resolve_roots` on the same pages): the roots agree for 25,669 of
25,818 entries. The differences: Quettamin lacks the roots that intermediate forms of another shape give here (Q.
Elda and its derivatives: √DEL², √DEL¹ through ✶edelā, ✶edelō — its `_merge_groups` drops them, as this one used to)
and the derivations of struck references (rule 9: ᴹQ. alwa < ᴹ√GAL², ᴹQ. alla¹). Two points where Quettamin was more
accurate were taken over here: elements from the reference with the fullest analysis (G. Tol Erethrin, ᴱQ.
Meril-i-Turinqi — some 50 more roots for early names) and leaving out a reference that analyses a form of the word
itself (ᴹ✶parkā no longer derives from ᴹ√A; Quettamin itself still has ᴹ✶parkā < ᴹ√A).

Words left without a root are mostly suffixes, pronouns, particles and words for which Eldamo gives no etymology,
neither of their own nor through merged forms (S. rhîw “winter”, Q. fúmë “breath”; the primitive forms ✶tulku,
✶dankĭnā, ✶stama- have only a reference to a source — the root is obvious from the form, but Eldamo does not link
it, and it is not guessed here).
