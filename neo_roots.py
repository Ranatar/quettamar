#!/usr/bin/env python3
"""Roots of every Neo-Quenya, Neo-Sindarin and Neo-Primitive vocabulary word of Eldamo.

    python neo_roots.py path/to/eldamo-data.xml [out.json] [nq] [ns] [np]

The word lists are the ones Eldamo prints on vocabulary-words-nq.html and
vocabulary-words-ns.html (vocabulary-index.xq with id=nq / id=ns): words of
nq, q, mq / ns, s, n (eq, en, g are read but filtered out by the page), without
<combine>, <deprecated>, <see>, names, phrases, grammar, phonetics and roots,
not [unglossed], and without '-' or '|' in @mark.

For each word the roots are found by walking Eldamo's links the way its word
pages read them (common.xq c:get-word / c:get-ref, word-page.xq
print-derivations), plus two links a word page does not follow but which
carry the etymology of the same word in another period:

* element   -- <element> of the word itself (a compound or a word + affix);
               when the word has none, the elements written inside one of its
               references (by @source, else by form);
* deriv     -- <deriv l v> of the word (c:get-word) and <deriv source> inside
               its valid references (c:get-ref): a root, or an intermediate form
               (a primitive word, an earlier Quenya word...) followed further;
* combine   -- words merged into this one (<combine l v> pointing here):
               ᴹQ. and ᴱQ. versions of a Q. or NQ. word;
* see       -- a stub that only says "see X";
* cognate   -- words joined by <cognate> (transitively, as the Cognates section
               of a word page), used only when nothing above gives a root, and
               only roots whose consonants are found in the word.

Priority, per word (as quettamin shared/lexicon.py _root_groups):
 1. two or more elements with roots -> the roots by element (compound);
 2. roots named by the word's derivations -> alternatives of one part;
 3. one element with roots -> it, the other elements as gaps;
 4. roots of intermediate forms the word derives from;
 5. roots of words merged into it (combine);
 6. a "see" target;
 7. cognates (checked);
 8. derivations of references Tolkien struck out (mark '-'): Eldamo's page lists
    them too (ᴹQ. Elda < ᴹ√LED, Ety/ELED); the path is marked "struck".
Intermediate forms of different shapes are alternatives of the part with roots
(Q. Elda < ✶elenā = √EL + -ā, and < ✶edelā < √DEL², < ✶edelō < √DEL¹).
Roots found by the lower steps when a higher one already answered are kept
apart in "also" (only those not already among the chosen roots).
The tree of a word whose roots come from steps 2-7 (or that has no roots) still
shows its elements beside the derivation: ᴹQ. mir < ᴹ√MI with the suffix -r².

Standard library only (Python >= 3.6).
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict

SITE = 'https://eldamo.org/content/words/word-{}.html'
# the languages of each vocabulary page (c:lang-words) and the ones the page filters out
GROUPS = {
    'nq': {'langs': ('nq', 'q', 'mq', 'eq'), 'name': 'Neo-Quenya'},
    'ns': {'langs': ('ns', 's', 'n', 'en', 'g'), 'name': 'Neo-Sindarin'},
    'np': {'langs': ('np', 'p', 'mp', 'ep'), 'name': 'Neo-Primitive Elvish'},
}
FILTERED_LANGS = ('eq', 'en', 'g', 'ep')
SINDARIN_LIKE = ('ns', 's', 'n', 'en', 'g', 'on', 'os', 'norths', 'ilk', 'eilk', 'dan', 'nan')
PRIMITIVE = ('p', 'mp', 'ep', 'np')
QUENYA_LIKE = ('nq', 'q', 'mq', 'eq', 'aq', 'maq', 'eaq', 'van', 'mt', 't', 'et')
LANG_NAMES = {'nq': 'Neo-Quenya', 'q': 'Quenya', 'mq': 'Middle Quenya', 'eq': 'Early Quenya',
              'ns': 'Neo-Sindarin', 's': 'Sindarin', 'n': 'Noldorin', 'en': 'Early Noldorin', 'g': 'Gnomish',
              'np': 'Neo-Primitive Elvish', 'p': 'Primitive Elvish', 'mp': 'Middle Primitive Elvish',
              'ep': 'Early Primitive Elvish'}
MAX_DEPTH = 9
WEAK_RULES = ('deprecated', 'cognate', 'struck')


def deleted(mark):
    """Rejected by Tolkien: '-' anywhere in @mark ('|' is a deleted section, not a rejection)."""
    return bool(mark) and '-' in mark


class Data:
    def __init__(self, path):
        self.root = ET.parse(path).getroot()
        self.parent = {}
        for p in self.root.iter():
            for c in p:
                self.parent[c] = p
        self.words = list(self.root.iter('word'))
        self.by_id = {w.get('page-id'): w for w in self.words}
        self.by_v = defaultdict(list)
        self.by_lv = defaultdict(list)
        for w in self.words:
            self.by_v[w.get('v')].append(w)
            self.by_lv[(w.get('l'), w.get('v'))].append(w)
        self.refs = defaultdict(list)
        self.cognate_of_ref = defaultdict(list)    # source -> refs having <cognate source=...>
        self.cognate_of_word = defaultdict(list)   # (l, v) -> words having <cognate l v>
        for w in self.words:
            for r in w.findall('ref'):
                if r.get('source'):
                    self.refs[r.get('source')].append(r)
                for c in r.findall('cognate'):
                    if c.get('source'):
                        self.cognate_of_ref[c.get('source')].append(r)
            for c in w.findall('cognate'):
                self.cognate_of_word[(c.get('l'), c.get('v'))].append(w)
        # words merged into a word: <combine l v> resolved to the target page;
        # words replaced by a word: <deprecated l v>
        self.combined_from = defaultdict(list)
        self.combined_into = {}
        self.deprecated_from = defaultdict(list)
        for w in self.words:
            c = w.find('combine')
            if c is not None:
                for t in self.get_word(c):
                    if t is not w:
                        self.combined_from[t.get('page-id')].append(w)
                        self.combined_into.setdefault(w.get('page-id'), t)
                        break
            for dp in w.findall('deprecated'):
                for t in self.get_word(dp)[:1]:
                    if t is not w:
                        self.deprecated_from[t.get('page-id')].append(w)
        self._cog = {}
        # Elvish languages: those under a Primitive Elvish language in the language tree
        # (Adûnaic, Westron, Khuzdul... have "cognates" by borrowing, not by roots)
        self.elvish = set()
        for lang in self.root.iter('language'):
            p, ids = lang, []
            while p is not None and p.tag == 'language':
                ids.append(p.get('id'))
                p = self.parent.get(p)
            if any(i in PRIMITIVE for i in ids):
                self.elvish.add(lang.get('id'))

    # -- Eldamo's lookups -------------------------------------------------
    def lang(self, el):
        while el is not None:
            if el.get('l'):
                return el.get('l')
            el = self.parent.get(el)
        return None

    def speech(self, el):
        while el is not None:
            if el.get('speech'):
                return el.get('speech')
            el = self.parent.get(el)
        return None

    def get_word(self, el):
        """c:get-word: words of form @v; of language @l when given, else the only such
        word, else those of the language the element inherits."""
        cands = self.by_v.get(el.get('v'), [])
        if el.get('l'):
            return [w for w in cands if w.get('l') == el.get('l')]
        if len(cands) == 1:
            return cands
        lang = self.lang(el)
        return [w for w in cands if w.get('l') == lang]

    def get_ref(self, source):
        """c:get-ref: the one <ref> with this @source, else nothing."""
        hits = self.refs.get(source) if source else None
        return hits[0] if hits and len(hits) == 1 else None

    def word_of(self, el):
        while el is not None and el.tag != 'word':
            el = self.parent.get(el)
        return el

    def is_root(self, w):
        """speech="root", or a primitive form written in capitals: Eldamo 0.8.13 files
        np GAWAK, ᴱ✶ƷAWAKA and ᴱ√OWO as nouns, though they are roots."""
        if self.speech(w) == 'root':
            return True
        letters = re.sub(r'[^\w]|[\d_¹²³⁴⁵⁶⁷⁸⁹⁰]', '', w.get('v') or '')
        return self.lang(w) in PRIMITIVE and bool(letters) and letters.isupper()

    def cognates(self, w):
        """CustomFunctions.allReferenceCognates over the word's valid refs + allWordCognates."""
        pid = w.get('page-id')
        if pid in self._cog:
            return self._cog[pid]
        out = []
        # through references
        todo = [r for r in w.findall('ref') if self.get_ref(r.get('source')) is r]
        seen = set(map(id, todo))
        while todo:
            r = todo.pop()
            nxt = list(self.cognate_of_ref.get(r.get('source'), []))
            for c in r.findall('cognate'):
                nxt += self.refs.get(c.get('source'), [])
            for x in nxt:
                if id(x) not in seen:
                    seen.add(id(x))
                    todo.append(x)
                    out.append(self.word_of(x))
        # through the word
        todo, seenw = [w], {id(w)}
        while todo:
            x = todo.pop()
            nxt = list(self.cognate_of_word.get((self.lang(x), x.get('v')), []))
            for c in x.findall('cognate'):
                nxt += self.by_lv.get((c.get('l'), c.get('v')), [])
            for y in nxt:
                if id(y) not in seenw:
                    seenw.add(id(y))
                    todo.append(y)
                    out.append(y)
        lang = w.get('l')
        res, ids = [], set()
        for x in out:
            if x is not None and x.get('l') != lang and x.get('page-id') not in ids:
                ids.add(x.get('page-id'))
                res.append(x)
        self._cog[pid] = res
        return res


# -- root resolution -----------------------------------------------------
# A result is a list of parts; a part is a list of alternatives; an alternative is
# {'id': page-id, 'via': [step, ...]} for a root, or {'gap': page-id, 'via': [...]}
# for an element without a root.  A step is (relation, page-id of the word passed).

class Resolver:
    def __init__(self, d: Data):
        self.d = d
        self.memo = {}
        self.path = set()
        self.cuts = 0

    def live(self, el, w):
        return not deleted(el.get('mark')) or deleted(w.get('mark'))

    def valid_refs(self, w):
        return [r for r in w.findall('ref') if self.d.get_ref(r.get('source')) is r and self.live(r, w)]

    def elements(self, w):
        """Element words in order: the word's own <element>, else those of one of its
        references (among those with the word's own form, else among all: the one with the
        most elements)."""
        d = self.d
        out = []
        for el in w.findall('element'):
            if el.get('v') in (None, '?') or not self.live(el, w):
                continue
            hit = self._pick(d.get_word(el))
            out.append(hit if hit is not None else ('missing', el))
        if out:
            return out, 'word'
        # a reference whose elements include the word itself analyses a form of it (ᴹ✶apparkā, the
        # intensive of ᴹ✶parkā = ᴹ√A + parkā): its other elements are that form's affixes, not the word's
        refs = [r for r in self.valid_refs(w) if r.findall('element') and not self.names_itself(r, w)]
        if not refs:
            return [], None
        own = [r for r in refs if _loose(r.get('v')) == _loose(w.get('v'))]
        # the fullest analysis: the reference with the most elements (G. Tol Erethrin: tol + erethrin
        # in LT1A, tol alone in GL), the first of those
        pool = own or refs
        most = max(len(r.findall('element')) for r in pool)
        for el in next(r for r in pool if len(r.findall('element')) == most).findall('element'):
            if el.get('v') in (None, '?') or not self.live(el, w):
                continue
            r = d.get_ref(el.get('source'))
            hit = d.word_of(r) if r is not None else self._pick(d.get_word(el))
            out.append(hit if hit is not None else ('missing', el))
        return out, 'ref'

    def names_itself(self, r, w):
        """A reference of w names w among its elements (by @source or by form)."""
        d = self.d
        for el in r.findall('element'):
            hit = d.get_ref(el.get('source')) if el.get('source') else None
            if hit is not None and d.word_of(hit) is w:
                return True
            if hit is None and any(x is w for x in d.get_word(el)):
                return True
        return False

    def _pick(self, ws):
        if not ws:
            return None
        live = [x for x in ws if not deleted(x.get('mark'))]
        return (live or ws)[0]

    def struck_from(self, w):
        """Words the word derives from by its references that Tolkien struck out (mark '-'):
        Eldamo's page lists their derivations too (ᴹQ. Elda < ᴹ√LED, 'departed', Ety/ELED); only
        those not reached by a live reference."""
        d = self.d
        live = {x.get('page-id') for x in self.derived_from(w)}
        out, seen = [], set()
        for r in w.findall('ref'):
            if d.get_ref(r.get('source')) is not r or self.live(r, w):
                continue
            for dv in r.findall('deriv'):
                hit = d.get_ref(dv.get('source'))
                x = d.word_of(hit) if hit is not None else None
                if x is None or x is w:
                    continue
                i = x.get('page-id')
                if i not in live and i not in seen:
                    seen.add(i)
                    out.append(x)
        return out

    def derived_from(self, w):
        """Words the word derives from: its <deriv> (c:get-word) and the words whose
        reference a <deriv source> of its valid references names (c:get-ref); plus
        roots named as elements inside its references (Q. firya: PHIR)."""
        d = self.d
        out = []
        for dv in w.findall('deriv'):
            if self.live(dv, w):
                out += d.get_word(dv)
        for r in self.valid_refs(w):
            for dv in r.findall('deriv'):
                if not self.live(dv, w):
                    continue
                hit = d.get_ref(dv.get('source'))
                if hit is not None:
                    out.append(d.word_of(hit))
                elif dv.get('v'):
                    # a written primitive form without a reference: a root of that form
                    for code in ('p', 'mp', 'ep', 'np'):
                        rs = [x for x in d.by_lv.get((code, dv.get('v')), []) if d.is_root(x)]
                        if rs:
                            out.append(rs[0])
                            break
            for el in r.findall('element') if not self.names_itself(r, w) else ():
                hit = d.get_ref(el.get('source')) if self.live(el, w) else None
                if hit is not None and d.is_root(d.word_of(hit)):
                    out.append(d.word_of(hit))
        res, seen = [], set()
        for x in out:
            if x is not None and x is not w and x.get('page-id') not in seen:
                seen.add(x.get('page-id'))
                res.append(x)
        return res

    def roots(self, w, depth=MAX_DEPTH, cognates=True):
        """(parts, rule): the chosen roots of a word and the rule that gave them."""
        pid = w.get('page-id')
        if pid in self.path:
            self.cuts += 1
            return [], None                  # a cycle (Q. nelquë ~ quainel) gives nothing
        key = (pid, depth, cognates)
        if key in self.memo:
            return self.memo[key]
        cuts = self.cuts
        self.path.add(pid)
        try:
            res = self._roots(w, depth, cognates)
        finally:
            self.path.discard(pid)
        if self.cuts == cuts:
            # a result cut short by a cycle depends on the path that led here: not cached
            self.memo[key] = res
        return res

    def candidates(self, w, depth, cognates):
        """Every rule's answer for a word: [(rule, parts)] in priority order."""
        d = self.d
        out = []
        if d.is_root(w):
            return [('self', [[{'id': w.get('page-id'), 'via': []}]])]
        if depth <= 0:
            return out
        pid = w.get('page-id')
        parts = self.element_parts(w, depth)
        real = [g for g in parts if _real(g)]
        derived = self.derived_from(w)
        direct = [{'id': x.get('page-id'), 'rel': 'deriv', 'via': []} for x in derived if d.is_root(x)]
        return self._candidates(w, depth, cognates, pid, parts, real, derived, direct)

    def element_parts(self, w, depth):
        """The word's elements as parts: each with its roots (through the element), a root
        named as an element, or a gap (an element without roots, or with no page)."""
        d = self.d
        parts = []
        els, where = self.elements(w)
        for e in els:
            if isinstance(e, tuple):
                parts.append([{'gap': None, 'rel': 'element', 'form': e[1].get('v'), 'lang': e[1].get('l') or d.lang(e[1]), 'via': []}])
                continue
            step = ('element', e.get('page-id'))
            if d.is_root(e):
                parts.append([{'id': e.get('page-id'), 'rel': 'element', 'via': [], 'named': True}])
                continue
            # no cognates below the word itself: a chain through a cognate of an element
            # (Q. -on² ~ S. -on²...) is too loose to name a root
            sub, _ = self.roots(e, depth - 1, cognates=False)
            if any(_real(g) for g in sub):
                for g in sub:
                    parts.append([dict(a, via=[step] + a['via']) for a in g])
            else:
                parts.append([{'gap': e.get('page-id'), 'rel': 'element', 'via': []}])
        return parts

    def _candidates(self, w, depth, cognates, pid, parts, real, derived, direct):
        d = self.d
        out = []
        # intermediate forms
        found = []
        for x in derived:
            if d.is_root(x):
                continue
            sub, _ = self.roots(x, depth - 1, cognates=False)
            if any(_real(g) for g in sub):
                step = ('deriv', x.get('page-id'))
                found.append([[dict(a, via=[step] + a['via']) for a in g] for g in sub])
        inter_all = _merge_all(found) if found else []
        inter = inter_all[0] if inter_all else []
        if len(real) == 1 and direct and len(parts) > 1:
            # a root the word's derivations or references name may stand for an element
            # without a root (S. huorn = hû¹ + orn, where a reference names KHUG for hû):
            # it fills that gap when it begins with the same consonant
            filled = []
            used = {a['id'] for g in real for a in _real(g)}
            for g in parts:
                if _real(g) or not g[0].get('gap'):
                    filled.append(g)
                    continue
                form = d.by_id[g[0]['gap']].get('v') or ''
                if form.startswith('-') or form.endswith('-') and d.speech(d.by_id[g[0]['gap']]) in ('pref', 'suf'):
                    filled.append(g)             # an affix is not a root's stand-in
                    continue
                fit = [a for a in direct if a['id'] not in used
                       and same_first_consonant(form, d.by_id[a['id']].get('v'))]
                filled.append([dict(a, via=[('element', g[0]['gap'])]) for a in fit] or g)
            if sum(1 for g in filled if _real(g)) >= 2:
                parts, real = filled, [g for g in filled if _real(g)]
        if len(real) >= 2:
            out.append(('elements', parts))
        if direct:
            # a root named by one derivation and a root reached through an intermediate
            # form of another are alternatives of the same word (Q. alda < √GAL², and
            # < ✶galadā < √GALAD); a compound intermediate form stays apart
            alts = list(direct)
            if len(inter) == 1:
                # the same root through the intermediate form stays as a second path
                # (Q. -(n)dur < √(N)DUR and < ✶-ndūr < √(N)DUR): the tree marks the
                # direct one as a shortcut
                alts += [a for a in _real(inter[0]) if all(_path_key(a) != _path_key(b) for b in alts)]
            out.append(('deriv', [alts]))
        if len(real) == 1:
            out.append(('element', parts))
        for x in inter_all:
            out.append(('intermediate', x))
        # words merged into this one
        found = []
        for x in d.combined_from.get(pid, []):
            sub, _ = self.roots(x, depth - 1, cognates=False)
            if any(_real(g) for g in sub):
                step = ('combine', x.get('page-id'))
                found.append([[dict(a, via=[step] + a['via']) for a in g] for g in sub])
        if found:
            out.append(('combine', _merge(found)))
        # see
        found = []
        for s in w.findall('see'):
            for x in d.get_word(s)[:1]:
                if x is w:
                    continue
                sub, _ = self.roots(x, depth - 1, cognates=False)
                if any(_real(g) for g in sub):
                    step = ('see', x.get('page-id'))
                    found.append([[dict(a, via=[step] + a['via']) for a in g] for g in sub])
        if found:
            out.append(('see', _merge(found)))
        # a word this one replaced (<deprecated>): sometimes an earlier form of the same
        # word (ᴱQ. milt > NQ. miltë), sometimes another word (ᴱQ. nardilea > NQ.
        # nisilëa); taken only when the consonants of every part are found in this word
        found = []
        for x in d.deprecated_from.get(pid, []):
            # the replaced word must look like an earlier form of this one: the same
            # beginning (NQ. sin > latúcen "tin", Q. engë > né "was" are other words)
            if not same_onset(x.get('v'), w.get('v')):
                continue
            # a root replaced by a word ("use this word instead of the root's words")
            # is not its etymology unless the word begins with the root's consonant
            if d.is_root(x) and not same_first_consonant(x.get('v'), w.get('v')):
                continue
            sub, _ = self.roots(x, depth - 1, cognates=False)
            checked = self.checked(w, sub, ('deprecated', x.get('page-id')), strict=True)
            if checked:
                found.append(checked)
        if found:
            out.append(('deprecated', _merge(found)))
        # derivations of references Tolkien struck out: the lowest rank, and only through
        # derivations (a root, or an intermediate form with roots)
        found = []
        for x in self.struck_from(w):
            if d.is_root(x):
                found.append([[{'id': x.get('page-id'), 'rel': 'deriv', 'via': [], 'struck': [(x.get('page-id'), pid)]}]])
                continue
            sub, _ = self.roots(x, depth - 1, cognates=False)
            if any(_real(g) for g in sub):
                step = ('deriv', x.get('page-id'))
                # 'struck': the links (from, to) of the path that only a struck reference gives
                found.append([[dict(a, via=[step] + a['via'], struck=a.get('struck', []) + [(x.get('page-id'), pid)])
                               for a in g] for g in sub])
        struck = _merge_all(found) if found else []
        # cognates: the parts whose consonants are found in this word; a part of the
        # cognate that is not found here is a gap (S. suilanna- = suil + anna-)
        if cognates:
            found = []
            for x in d.cognates(w):
                if d.lang(x) in PRIMITIVE or d.lang(x) not in d.elvish:
                    continue
                sub, _ = self.roots(x, depth - 1, cognates=False)
                checked = self.checked(w, sub, ('cognate', x.get('page-id')), strict=False)
                if checked:
                    if len(sub) > 1:
                        # a compound cognate (N. anrand = ann + rand for ᴹQ. randa) may
                        # share only a part with this word: its roots are not offered
                        # as alternatives ("also") to roots found otherwise
                        checked = [[dict(a, partial=True) for a in g] for g in checked]
                    found.append(checked)
            if found:
                # the cognate with most parts found, then fewest gaps
                found.sort(key=lambda g: (-sum(1 for x in g if _real(x)), sum(1 for x in g if not _real(x))))
                best = [g for g in found
                        if [bool(_real(x)) for x in g] == [bool(_real(x)) for x in found[0]]]
                out.append(('cognate', _merge(best)))
        for x in struck:
            out.append(('struck', x))
        return out

    def checked(self, w, parts, step, strict):
        """parts of another word kept for this one: alternatives whose consonants are
        found in this word; a part with none becomes a gap (strict: the whole is refused)."""
        if not any(_real(g) for g in parts):
            return None
        res = []
        for g in parts:
            real = _real(g)
            sind = is_sindarin(self.d.lang(w))
            if step[0] == 'cognate':
                # a cognate's root reached through yet another loose link is too far
                real = [a for a in real if not any(r in WEAK_RULES for r, _ in a['via'])]
            ok = [a for a in real if consonants_match(w.get('v'), self.d.by_id[a['id']].get('v'), sind)]
            if ok:
                res.append([dict(a, via=[step] + a['via']) for a in ok])
            elif real and strict:
                return None
            elif real:
                # the part's roots stay in their place, marked as not found in this word
                res.append([{'gap': a['id'], 'rel': a.get('rel', 'deriv'), 'via': [step] + a['via'],
                             'unmatched': [a['id']]} for a in real])
            elif strict:
                res.append([dict(a, via=[step] + a['via']) for a in g])
            # a cognate's own rootless parts (S. estolad: -ad) say nothing about this word
        return res if any(_real(g) for g in res) else None

    def _roots(self, w, depth, cognates):
        cands = self.candidates(w, depth, cognates)
        if not cands:
            return [], None
        rule, parts = cands[0]
        return parts, rule


def _real(group):
    return [a for a in group if 'id' in a]


def _merge(found):
    """Several sources of the same rank: the one with the most parts; one of the same
    shape adds its roots as alternatives part by part, and so does one of another shape
    when both have a single part with roots (Q. Elda < ✶elenā = √EL + -ā, and < ✶eledā < √EL,
    < ✶edelā < √DEL², < ✶edelō < √DEL¹: the roots are alternatives of the part with roots).
    Sources that fit neither way are dropped (see _merge_all)."""
    return _merge_all(found)[0]


def _merge_all(found):
    """_merge, and the sources it could not place merged the same way: [first, second...]."""
    found = sorted(found, key=lambda g: -len(g))
    out = [list(x) for x in found[0]]
    rest = []

    def add(k, x):
        # the same root by another path stays: the tree shows every path to it (the flat list
        # of roots keeps it once)
        out[k] += [a for a in x if 'id' not in a or all(_path_key(a) != _path_key(y) for y in out[k])]

    real_out = [k for k, x in enumerate(out) if _real(x)]
    for g in found[1:]:
        if len(g) == len(out):
            for k, x in enumerate(g):
                add(k, x)
            continue
        real_g = [x for x in g if _real(x)]
        if len(real_out) == 1 and len(real_g) == 1:
            add(real_out[0], _real(real_g[0]))
        else:
            rest.append(g)
    return [out] + (_merge_all(rest) if rest else [])


def _path_key(a):
    return (a.get('id'), tuple(pid for _, pid in a.get('via', ())))


# -- consonant check for cognates ------------------------------------------
# Classes of consonants as Quenya keeps them: þ/th > s, w > v, kh > h, ñ > n, mb > m,
# nd > n, initial g- lost. A root's classes must appear in order in the word's.
_CLS = [
    set('kgcqxhɣ'), set('tdθþðs'), set('pbfvwɸβ'), set('m'), set('nñŋ'),
    set('l'), set('r'), set('yj'),
]


def _norm(s):
    s = unicodedata.normalize('NFD', (s or '').lower())
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r'[¹²³⁴⁵⁶⁷⁸⁹⁰√✶*!^#†()\-\s]', '', s)
    return s


def _classes(s, sindarin=False):
    """Consonant classes of a form, a repeated class once. Sindarin (sindarin=True):
    ch, dh, lh, rh, mh are single sounds, and m joins the labials (lenition m > v)."""
    s = _norm(s)
    if sindarin:
        s = s.replace('ch', 'x').replace('dh', 'ð').replace('lh', 'l').replace('rh', 'r').replace('mh', 'v')
    # Q. ngw is ŋgw (ungwë < √UÑG): its g is kept as a velar, other gw > w (Q. vendë < GWEN)
    s = s.replace('ngw', 'ŋg').replace('kh', 'x').replace('th', 'θ').replace('ph', 'f').replace('qu', 'q') \
        .replace('kw', 'q').replace('gw', 'w').replace('ng', 'ŋ').replace('hy', 'h').replace('hl', 'l').replace('hr', 'r')
    out = []
    for ch in s:
        k = next((i for i, c in enumerate(_CLS) if ch in c), None)
        if k == 3 and sindarin:
            k = 2
        if k is not None and (not out or out[-1] != k):
            out.append(k)
    return out


def is_sindarin(lang):
    return lang in SINDARIN_LIKE


def same_onset(a, b):
    """Two forms begin alike (the replaced word looks like an earlier form of this one):
    both with a vowel; or the same first consonant up to b~v~w, k~c~g~h (not kw), p~f,
    t~d~th, n~ñ (ᴱQ. milt ~ NQ. miltë, N. rhand ~ NS. rand, ᴱ√VĪ ~ ✶bē; not ᴱQ. wara- ~
    Q. psar-, NQ. sin ~ latúcen); or a lost initial g-/w- before a vowel."""
    va = not _first(a)
    vb = not _first(b)
    if va and vb:
        return True
    if not va and not vb:
        return same_first_consonant(a, b)
    return (_first(a) or _first(b)) in ('g', 'w')


_ONSET = [set('bvwβ'), set('kcgxh'), set('pfɸ'), set('tdθþð'), set('s'), set('nñŋ')]


def _first(x):
    """First consonant of a form ('' if it begins with a vowel), digraphs as one sound."""
    x = _norm(x)
    for a, b in (('gw', 'w'), ('th', 'θ'), ('ph', 'f'), ('kh', 'x'), ('ch', 'x'), ('dh', 'ð'),
                 ('hl', 'l'), ('lh', 'l'), ('hr', 'r'), ('rh', 'r'), ('hw', 'w'), ('hy', 'h'),
                 ('ng', 'ñ'), ('qu', 'q'), ('kw', 'q')):
        if x.startswith(a):
            x = b + x[len(a):]
            break
    m = re.match(r'[^aeiouyáéíóúâêîôûäëïöü]', x)
    return m.group(0) if m else ''


def same_first_consonant(a, b):
    """The first consonant of two forms is the same sound up to b~v~w, k~c~g~h (not kw),
    p~f, t~d~th (ᴱ√SINI ~ ✶sinki, ᴱ√VĪ ~ ✶bē; not ᴱ√GWAṘA ~ Q. psar-)."""
    fa, fb = _first(a), _first(b)
    if not fa or not fb:
        return not fa and not fb
    return fa == fb or any(fa in g and fb in g for g in _ONSET)


def _found(r, wc, skippable):
    """How many classes of r are found in order in wc when the classes in `skippable`
    may be missing from the word; None if some other class is not found."""
    best = None

    def go(i, j, n):
        nonlocal best
        if i == len(r):
            best = n if best is None else max(best, n)
            return
        for k in range(j, len(wc)):
            if wc[k] == r[i]:
                go(i + 1, k + 1, n + 1)
                break
        if r[i] in skippable:
            go(i + 1, j, n)
    go(0, 0, 0)
    return best


def consonants_match(word, root_form, sindarin=False):
    """The consonants of the root, in order, among the word's. At least two must be
    found, unless root and word both have a single consonant (Q. se < √S); a lost
    initial g-/w- of the root is allowed when the word begins with a vowel. In
    Sindarin a velar or y of the root may be missing anywhere (medial g lost, y > i),
    but the two consonants found are still required."""
    wc = _classes(word, sindarin)
    initial_vowel = bool(re.match(r'[aeiouáéíóúâêîôûäëïöüy]', _norm(word)))
    skippable = {0, 7} if sindarin else set()
    for variant in (root_form or '').split('/'):
        rc = _classes(variant, sindarin)
        if not rc:
            continue
        tries = [rc]
        if initial_vowel and rc[0] in (0, 2) and len(rc) > 1:
            tries.append(rc[1:])
        for r in tries:
            n = _found(r, wc, skippable)
            if n is None:
                continue
            if n >= 2 or (len(rc) == 1 and len(wc) == 1 and n == 1):
                return True
    return False


# -- the word list and the output --------------------------------------------

def group_words(d: Data, group: str):
    """The words vocabulary-index.xq lists for a group (id=nq or id=ns)."""
    langs = GROUPS[group]['langs']
    out = []
    for w in d.words:
        lang = d.lang(w)
        if lang not in langs or w.find('combine') is not None:
            continue
        sp = d.speech(w) or ''
        if sp.endswith('-name') or sp in ('text', 'phrase', 'grammar', 'root') or sp.startswith('phone'):
            continue
        if w.find('deprecated') is not None or w.find('see') is not None:
            continue
        if w.get('gloss') == '[unglossed]' or lang in FILTERED_LANGS:
            continue
        m = w.get('mark') or ''
        if '-' in m or '|' in m:
            continue
        out.append(w)
    return out


def deprecated_words(d: Data, group: str):
    """The words Eldamo lists on deprecations-<group>.html (deprecation-index.xq): words of the
    group's languages (c:lang-words: without <combine>) with <deprecated>, not names, phrases,
    texts, grammar or phonetics; roots, deprecated or not, are in the index of roots."""
    langs = GROUPS[group]['langs']
    out = []
    for w in d.words:
        if d.lang(w) not in langs or w.find('combine') is not None or w.find('deprecated') is None:
            continue
        if d.is_root(w):
            continue                     # a primitive form in capitals marked as a noun (ᴱ√ƷAWAKA)
        sp = d.speech(w) or ''
        if sp.endswith('-name') or sp in ('text', 'phrase', 'grammar', 'root') or sp.startswith('phone'):
            continue
        out.append(w)
    return out


def other_words(d: Data, group: str, taken: set):
    """The other words of the group's languages (c:lang-words) that Eldamo marks ⚠️ and keeps
    out of both the vocabulary and the deprecation pages: early ones (G. caineglad, ᴱQ., ᴱN.,
    ᴱ✶), rejected, deleted, unglossed. Not names, phrases, texts, grammar, phonetics or roots;
    not the stubs that only point elsewhere (<see>: a spelling of a word shown anyway)."""
    langs = GROUPS[group]['langs']
    out = []
    for w in d.words:
        if d.lang(w) not in langs or w.find('combine') is not None or w.find('deprecated') is not None:
            continue
        if w.find('see') is not None or d.is_root(w) or w.get('page-id') in taken:
            continue
        sp = d.speech(w) or ''
        if sp.endswith('-name') or sp in ('text', 'phrase', 'grammar', 'root') or sp.startswith('phone'):
            continue
        if word_warnings(d, w):
            out.append(w)
    return out


def name_words(d: Data, group: str, taken: set):
    """Names of the group's languages (speech ...-name: places, persons, peoples like Q. Tareldar
    = tar-¹ + Elda): Eldamo keeps them out of its vocabulary pages, but their elements and
    derivations are the same as those of words. Not roots, not the <see> stubs, not merged forms."""
    langs = GROUPS[group]['langs']
    out = []
    for w in d.words:
        if d.lang(w) not in langs or w.find('combine') is not None or w.find('see') is not None:
            continue
        if d.is_root(w) or w.get('page-id') in taken:
            continue
        if (d.speech(w) or '').endswith('-name'):
            out.append(w)
    return out


def merged_forms(d: Data, heads: set):
    """The words of other conceptions merged by <combine> into the given pages, transitively
    (Q. cala holds ᴹQ. kala and ᴱQ. kala¹), that are not such pages themselves."""
    out, seen, todo = [], set(heads), list(heads)
    while todo:
        for x in d.combined_from.get(todo.pop(), []):
            pid = x.get('page-id')
            if pid not in seen:
                seen.add(pid)
                todo.append(pid)
                if not d.is_root(x):     # roots merged into a word stay in the index of roots
                    out.append(x)
    return out


def alt_word(d: Data, w):
    """c:alt-lang (common.xq): the word whose language Eldamo's indexes print in brackets after a
    word's own (ᴺQ. [ᴱQ.] ulumpë). A neo word marked ^ takes the nested word merged into it by
    <combine>; a word without references of its own (not marked !, not phonetics, grammar or
    text), its first nested word with references in another language ($word//word[ref][1]
    [@l != $word/@l], the first in document order). That word is the Tolkien's form the neo word
    is made from."""
    lang, mark = w.get('l'), w.get('mark')
    if mark == '^':
        for x in w.iter('word'):
            c = x.find('combine') if x is not w else None
            if c is not None and c.get('l') == lang and c.get('v') == w.get('v'):
                return x
    sp = w.get('speech') or ''
    if mark != '!' and w.find('ref') is None and not (sp.startswith('phon') or sp in ('grammar', 'text')):
        # //word[ref][1]: under every element, its first child word with references
        for p in w.iter():
            first = next((c for c in p if c.tag == 'word' and c.find('ref') is not None), None)
            if first is not None and first.get('l') and first.get('l') != lang:
                return first
    return None


def alt_lang(d: Data, w):
    """The language in brackets (see alt_word)."""
    x = alt_word(d, w)
    return x.get('l') if x is not None else None


def root_alt_lang(d: Data, w):
    """root-index.xq: a root without references of its own shows in brackets the language
    of its first nested word (N√LUP [√] — the late root LUB³ filed under it)."""
    if w.find('ref') is not None:
        return None
    first = next((c for c in w if c.tag == 'word'), None)
    return first.get('l') if first is not None and first.get('l') else None


def normalize_spelling(v):
    """c:normalize-spelling (common.xq): the spelling of the Neo-Quenya list."""
    v1 = v.replace('q', 'qu').replace('quu', 'qu').replace('ks', 'x').replace('k', 'c')
    v2 = v1.replace('oa', 'öa').replace('ea', 'ëa')
    if v2 in ('nye', 'lye', 'tye') or len(re.sub('[¹²³⁴]', '', v2)) < 3:
        return v2
    m = re.match(r'^(.*)e(\)|¹|²|³|⁴)?$', v2)
    if m:
        return m.group(1) + 'ë' + (m.group(2) or '')
    return v2


class Out:
    def __init__(self, d: Data):
        self.d = d

    def word(self, pid):
        w = self.d.by_id[pid]
        rec = {'form': w.get('v'), 'lang': w.get('l'), 'url': SITE.format(pid)}
        if w.get('gloss'):
            rec['gloss'] = w.get('gloss')
        return rec

    def path(self, via):
        return [dict(self.word(pid), rel=rel) for rel, pid in via]

    def canonical(self, pid):
        """Where Eldamo merges a root: <combine> links followed to the end, then the
        Neo-Primitive root it is filed under, if any."""
        d = self.d
        chain, seen = [], {pid}
        cur = pid
        while cur in d.combined_into:
            nxt = d.combined_into[cur].get('page-id')
            if nxt in seen:
                break
            seen.add(nxt)
            chain.append(nxt)
            cur = nxt
        p = d.parent.get(d.by_id[cur])
        while p is not None and p.tag == 'word':
            if p.get('l') == 'np' and d.is_root(p) and p.get('page-id') not in seen:
                chain.append(p.get('page-id'))
                break
            p = d.parent.get(p)
        return chain

    def alt(self, a, part, several):
        if 'id' in a:
            rec = self.word(a['id'])
        elif a.get('gap'):
            rec = self.word(a['gap'])
        else:
            rec = {'form': a.get('form'), 'lang': a.get('lang'), 'url': None}
        if several:
            rec['part'] = part
        if a.get('via'):
            rec['via'] = self.path(a['via'])
        if a.get('partial'):
            rec['compound_cognate'] = True
        if a.get('struck'):
            rec['struck'] = True        # the path goes through a reference Tolkien struck out
        if a.get('unmatched'):
            # roots of a cognate's part whose consonants are not found in the word
            rec['not_matched'] = [self.word(x) for x in a['unmatched']]
        if 'id' in a:
            canon = self.canonical(a['id'])
            if canon:
                rec['same_as'] = [self.word(x) for x in canon]
        return rec


# -- the derivation tree ---------------------------------------------------------
# The chosen roots and gaps of a word as nested blocks: the word's parts (elements,
# each its own block) or its alternatives (derivations), each block holding what it
# comes from in turn -- an intermediate form, then a primitive form, then the root.
# Built from the via paths of the chosen alternatives: shared beginnings merge.

class Tree:
    def __init__(self, d: Data, R: Resolver, o: Out):
        self.d, self.R, self.o = d, R, o

    def kind(self, pid):
        w = self.d.by_id[pid]
        if self.d.is_root(w):
            return 'root'
        return 'protoform' if self.d.lang(w) in PRIMITIVE else 'form'

    def written(self, parent, child, rel):
        """How the word's references write the link to `child`: the form as the source
        gives it and the intermediate forms between (<deriv v i1 i2 i3>, i1 nearest the
        primitive form), or an element in the source's spelling."""
        d, R = self.d, self.R
        pw = d.by_id.get(parent)
        cw = d.by_id.get(child)
        if pw is None or cw is None:
            return []
        out = []
        same_form = lambda x, y: _norm(x).lower() == _norm(y).lower()
        # references of inflected forms (plurals, cases: lassī for lassē) derive those forms
        for r in [x for x in R.valid_refs(pw) if x.find('inflect') is None]:
            for dv in r.findall('deriv') if rel == 'deriv' else ():
                if not R.live(dv, pw):
                    continue
                hit = d.get_ref(dv.get('source'))
                same = (hit is not None and d.word_of(hit) is cw) or \
                    (hit is None and dv.get('v') == cw.get('v'))
                if not same:
                    continue
                inter = [dv.get(k) for k in ('i1', 'i2', 'i3') if dv.get(k)]
                if not same_form(dv.get('v'), cw.get('v')) or inter:
                    rec = {'source': r.get('source'), 'ref': r.get('v'), 'form': dv.get('v')}
                    if inter:
                        rec['intermediate'] = inter
                    out.append(rec)
            for el in r.findall('element') if rel == 'element' else ():
                hit = d.get_ref(el.get('source'))
                if hit is not None and d.word_of(hit) is cw and not same_form(el.get('v'), cw.get('v')):
                    out.append({'source': r.get('source'), 'ref': r.get('v'), 'form': el.get('v')})
        return out

    def build(self, word_pid, parts):
        top = {'children': {}}
        for k, g in enumerate(parts):
            for a in g:
                path = list(a.get('via', ()))
                if 'id' in a:
                    if path and path[-1][1] == a['id']:
                        last = path.pop()          # a merged word that is itself a root
                        end = (last[0], a['id'])
                    else:
                        end = (a.get('rel', 'deriv'), a['id'])
                    leaf = {}
                else:
                    end = (a.get('rel', 'element'), a.get('gap'))
                    leaf = {'gap': True}
                    if a.get('unmatched'):
                        leaf['not_matched'] = a['unmatched']
                    if a.get('gap') is None:
                        leaf['form'], leaf['lang'] = a.get('form'), a.get('lang')
                node, parent = top, word_pid
                for i, (rel, pid) in enumerate(path + [end]):
                    key = (rel, pid)
                    if i == len(path) and leaf.get('form'):
                        key = key + (leaf['form'],)
                    nxt = node['children'].get(key)
                    if nxt is None:
                        nxt = node['children'][key] = {'rel': rel, 'pid': pid, 'parent': parent, 'children': {}}
                        if (pid, parent) in a.get('struck', ()):
                            nxt['struck'] = True     # a link only a struck reference gives
                    node, parent = nxt, pid
                node.update(leaf)
        return self._out_children(top)

    def _out_children(self, node):
        kids = [self._out(c) for c in node['children'].values()]
        res = {}
        parts = [c for c in kids if c['rel'] == 'element']
        alts = [c for c in kids if c['rel'] != 'element']
        # a root named directly beside a derivation that reaches the same root through an
        # intermediate form: the direct link is a shortcut of the longer path (Eldamo records
        # both: Q. -(n)dur < √(N)DUR in PE17/152, and < ✶-ndūr < √(N)DUR)
        for c in alts:
            if c['kind'] != 'root' or c.get('parts') or c.get('from'):
                continue
            if any(o is not c and o['rel'] == 'deriv' and _reaches(o, c['url']) for o in alts):
                c['shortcut'] = True
        if parts:
            res['parts'] = parts
        if alts:
            res['from'] = alts
        return res

    def _out(self, n):
        pid = n['pid']
        if pid is None:
            rec = {'rel': n['rel'], 'kind': 'form', 'form': n.get('form'), 'lang': n.get('lang'), 'url': None}
        else:
            rec = dict({'rel': n['rel'], 'kind': self.kind(pid)}, **self.o.word(pid))
            wr = self.written(n['parent'], pid, n['rel'])
            if wr:
                rec['written'] = wr
            if rec['kind'] == 'root':
                canon = self.o.canonical(pid)
                if canon:
                    rec['same_as'] = [self.o.word(x) for x in canon]
        if n.get('gap'):
            rec['gap'] = True
        if n.get('struck'):
            rec['struck'] = True
        if n.get('not_matched'):
            rec['not_matched'] = [self.o.word(x) for x in n['not_matched']]
        rec.update(self._out_children(n))
        return rec


def _reaches(n, url):
    """A tree block holds the page `url` below it, through derivations and merged forms."""
    for c in n.get('from', []):
        if c.get('url') == url or _reaches(c, url):
            return True
    return False


def canon_key(o: Out, pid):
    c = o.canonical(pid)
    return c[-1] if c else pid


def build(d: Data, group: str, R=None):
    R = R or Resolver(d)
    o = Out(d)
    T = Tree(d, R, o)
    entries = []
    listed = group_words(d, group)
    deprecated = deprecated_words(d, group)
    other = other_words(d, group, {w.get('page-id') for w in listed + deprecated})
    names = name_words(d, group, {w.get('page-id') for w in listed + deprecated + other})
    heads = {w.get('page-id') for w in listed + deprecated + other + names}
    merged = merged_forms(d, heads)
    kinds = [(w, 'listed') for w in listed] + [(w, 'deprecated') for w in deprecated] + \
        [(w, 'other') for w in other] + [(w, 'name') for w in names] + [(w, 'merged') for w in merged]
    for w, kind in kinds:
        pid = w.get('page-id')
        R.path.add(pid)
        cands = R.candidates(w, MAX_DEPTH, True)
        rule, parts = cands[0] if cands else (None, [])
        # the word's elements, when its roots come from another rule (ᴹQ. mir < ᴹ√MI, with
        # the element -r²; Q. calima < √KAL, with cal- and -ima) or when it has none
        # (NQ. aialca = ai(a)- + -lka): the tree shows them beside its derivation
        extra = []
        if rule not in ('elements', 'element', 'self'):
            named = {a['id'] for g in parts for a in g if 'id' in a and not a.get('via')}
            for g in R.element_parts(w, MAX_DEPTH):
                if all('id' in a and not a.get('via') and a['id'] in named for a in g):
                    continue                 # a root named both as an element and a derivation
                extra.append(g)
        # derivations of struck references (Eldamo's page lists them): in the tree beside the rest,
        # when the roots come from another rule
        if rule != 'struck':
            have = {_path_key(a) for g in parts for a in g if 'id' in a}
            for r2, p2 in cands[1:]:
                if r2 != 'struck':
                    continue
                for g in p2:
                    g = [a for a in g if 'id' in a and _path_key(a) not in have]
                    if g:
                        extra.append(g)
        R.path.discard(pid)
        several = len(parts) > 1
        roots, gaps, seen = [], [], set()
        for k, g in enumerate(parts):
            for a in g:
                rec = o.alt(a, k, several)
                key = (k, rec.get('url'), rec.get('form'), 'id' in a)
                if key in seen:
                    continue
                seen.add(key)
                (roots if 'id' in a else gaps).append(rec)
        chosen = {canon_key(o, a['id']) for g in parts for a in g if 'id' in a}
        also = []
        for r2, p2 in cands[1:]:
            if r2 == 'cognate' and len(parts) > 1:
                continue            # a compound word: a cognate's root cannot be placed
            # the part is given when the other source has the same parts as the chosen one
            same_shape = several and len(p2) == len(parts)
            for k, g in enumerate(p2):
                for a in _real(g):
                    if a.get('partial'):
                        continue
                    ck = canon_key(o, a['id'])
                    if ck in chosen:
                        continue
                    chosen.add(ck)
                    rec = o.alt(a, k, same_shape)
                    rec['rule'] = r2
                    also.append(rec)
        lang = w.get('l')
        e = {
            'group': group,
            'word': w.get('v'),
            # the Neo-Quenya page normalizes the spelling (c:normalize-spelling), the Neo-Sindarin one does not
            'spelling': normalize_spelling(w.get('v')) if group == 'nq' and kind != 'merged' else w.get('v'),
            'lang': lang,
            'lang_name': LANG_NAMES.get(lang, lang),
            'speech': w.get('speech') or d.speech(w),
            'gloss': w.get('gloss') or w.get('ngloss') or '',
            'url': SITE.format(pid),
        }
        if w.get('mark'):
            e['mark'] = w.get('mark')
        # see_instead -- what Eldamo suggests instead (its <deprecated l v>); a form of another
        # conception merged into a word can carry it too (ᴹQ. ... inside a Q. word)
        # (as deprecation-index.xq: the word's own <deprecated>, else that of the word its <see> names:
        # ᴱQ. anda, see ᴱQ. ande(a), deprecated for Q. anda)
        deps = w.findall('deprecated') or [x for sv in w.findall('see') for t in d.get_word(sv)[:1] for x in t.findall('deprecated')]
        instead = []
        for x in deps:
            for t in d.get_word(x)[:1]:
                rec = o.word(t.get('page-id'))
                if rec not in instead:
                    instead.append(rec)
        if instead:
            e['see_instead'] = instead
        if kind == 'deprecated':
            # Eldamo's deprecated words (deprecations-<group>.html): not recommended for Neo-Eldarin
            e['deprecated'] = True
        elif kind == 'other':
            # outside both of Eldamo's pages (other_words): marked ⚠️, see `warnings`
            e['outside_lists'] = True
        elif kind == 'name':
            # a name (name_words): Eldamo lists names on no vocabulary page
            e['name'] = True
        elif kind == 'merged':
            # a word of another conception nested in a page and merged into it by <combine>
            # (ᴹQ. kala and ᴱQ. kala¹ inside Q. cala): Eldamo shows it on that page, under the word
            target = d.combined_into.get(pid)
            if target is not None:
                e['merged_into'] = o.word(target.get('page-id'))
        aw = alt_word(d, w)
        if aw is not None:
            e['alt_lang'] = aw.get('l')
            # that word itself: the form of Tolkien's a neo word is made from (ᴱQ. aiko for ᴺQ.[ᴱQ.] aico)
            e['alt_source'] = {'form': aw.get('v'), 'id': aw.get('page-id')}
        # the Cognates section of Eldamo's page (allReferenceCognates + allWordCognates): words of
        # other languages, a relation of comparison, not of origin (S. Edhelharn ~ Q. Elessar)
        cogs = [o.word(x.get('page-id')) for x in d.cognates(w) if x.get('page-id')]
        if cogs:
            e['cognates'] = cogs
        warn = word_warnings(d, w)
        if warn:
            # Eldamo's ⚠️: deprecated (with or without a replacement), deleted, rejected,
            # doubtful, unglossed, early
            e['warnings'] = warn
        e['rule'] = rule
        weak = sorted({rel for g in parts for a in g for rel, _ in a.get('via', ()) if rel in WEAK_RULES}
                      | {'struck' for g in parts for a in g if a.get('struck')})
        if rule in WEAK_RULES and rule not in weak:
            weak.insert(0, rule)
        if weak:
            # a root reached through a link that is not a derivation of the same word
            e['uncertain'] = weak
        e['roots'] = roots
        if parts or extra:
            e['tree'] = T.build(pid, parts + extra)
        if gaps:
            e['gaps'] = gaps
        if also:
            e['also'] = also
        entries.append(e)
    entries.sort(key=lambda e: (_sort_key(e['spelling']), e['lang'], e['url']))
    return entries


def _sort_key(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(ch for ch in s if not unicodedata.combining(ch) and ch not in '¹²³⁴-()')


def _loose(form):
    return _norm(form).replace('k', 'c')


# -- the root index -------------------------------------------------------------
# The roots Eldamo lists on roots-np.html (root-index.xq, id=np): roots of np, p, mp,
# ep without <combine>, the unrecommended ones kept and marked (⚠️ there, `warnings`
# here). For each: what is merged into it, what it derives from, and the words of the
# three lists whose chosen roots are it or a root merged into it.

def index_roots(d: Data):
    return [w for w in d.words if d.lang(w) in GROUPS['np']['langs'] and w.find('combine') is None
            and d.speech(w) == 'root']


def root_warnings(d: Data, w, early=('ep',)):
    """root-index.xq marks a Neo-Primitive root ⚠️ when it is deprecated (itself or
    the word its <see> names), deleted (|), rejected (-), doubtful (‽), unglossed or
    early (ᴱ√). The vocabulary and deprecation pages (vocabulary-index.xq,
    deprecation-index.xq) mark a word the same way, early being ᴱ✶, ᴱN., ᴱQ. and G.;
    see word_warnings."""
    out = []
    dep = list(w.findall('deprecated'))
    for sv in w.findall('see'):
        for x in d.get_word(sv):
            dep += x.findall('deprecated')
    if dep:
        out.append('deprecated')
    m = w.get('mark') or ''
    if '|' in m:
        out.append('deleted')
    if '-' in m:
        out.append('rejected')
    if '‽' in m:
        out.append('doubtful')
    if w.get('gloss') == '[unglossed]' and not w.get('ngloss'):
        out.append('unglossed')
    if d.lang(w) in early:
        out.append('early')
    return out, dep


def word_warnings(d: Data, w):
    """Why Eldamo puts ⚠️ before a word on its vocabulary and deprecation pages."""
    return root_warnings(d, w, early=('ep', 'en', 'eq', 'g'))[0]


def build_root_index(d: Data, R: Resolver, entries):
    o = Out(d)
    pid_of = lambda url: url.split('word-')[1].split('.')[0]

    def merged_into(pid):
        """The roots a root is merged into by <combine>, nearest first."""
        out, seen = [], {pid}
        while pid in d.combined_into:
            pid = d.combined_into[pid].get('page-id')
            if pid in seen:
                break
            seen.add(pid)
            out.append(pid)
        return out

    def merged_from(pid):
        """Everything merged into a root by <combine>, transitively."""
        out, todo = [], [pid]
        while todo:
            for x in d.combined_from.get(todo.pop(), []):
                xp = x.get('page-id')
                if xp not in out and xp != pid:
                    out.append(xp)
                    todo.append(xp)
        return out

    # the words that use each root, credited to the root and to the roots it is merged into
    users = defaultdict(list)
    for e in entries:
        seen = set()
        for r in e['roots']:
            rp = pid_of(r['url'])
            # credited to roots only: ᴹ√LŌ is merged into the word ✶lō¹, not into a root
            for target in [rp] + [t for t in merged_into(rp) if d.is_root(d.by_id[t])]:
                if (target, e['url']) in seen:
                    continue
                seen.add((target, e['url']))
                rec = {'word': e['word'], 'lang': e['lang'], 'url': e['url']}
                if target != rp:
                    # the word names a root merged into this one
                    rec['through'] = {'form': d.by_id[rp].get('v'), 'lang': d.by_id[rp].get('l'), 'url': r['url']}
                if 'part' in r:
                    rec['part'] = r['part']
                if e.get('uncertain'):
                    rec['uncertain'] = e['uncertain']
                users[target].append((e['group'], rec))

    roots = index_roots(d)
    listed = {w.get('page-id') for w in roots}
    # roots the words use that reach no listed root: merged by <combine> into a primitive
    # word (ᴹ√LŌ into ✶lō¹), combined with themselves (ᴹ√LA: the Eldamo list leaves it
    # out), or not marked as roots (N√GAWAK)
    extra = []
    for pid in users:
        if pid in listed or any(t in listed for t in merged_into(pid)):
            continue
        w = d.by_id[pid]
        c = w.find('combine')
        if c is not None and any(t is w for t in d.get_word(c)):
            why = 'combined_with_itself'
        elif pid in d.combined_into:
            why = 'merged_into_word'
        elif d.speech(w) != 'root':
            why = 'not_marked_root'
        else:
            why = 'other'
        extra.append((w, why))
    out = []
    for w, why in [(x, None) for x in roots] + extra:
        pid = w.get('page-id')
        warn, dep = root_warnings(d, w)
        rec = {
            'form': w.get('v'), 'lang': w.get('l'), 'lang_name': LANG_NAMES.get(w.get('l'), w.get('l')),
            'url': SITE.format(pid),
        }
        al = root_alt_lang(d, w)
        if al:
            rec['alt_lang'] = al
        if why:
            rec['in_list'] = False
            rec['not_listed_because'] = why
            mi = merged_into(pid)
            if mi:
                rec['merged_into'] = [o.word(x) for x in mi]
        if w.get('gloss'):
            rec['gloss'] = w.get('gloss')
        if w.get('ngloss') and w.get('ngloss') != w.get('gloss'):
            rec['ngloss'] = w.get('ngloss')
        if w.get('mark'):
            rec['mark'] = w.get('mark')
        rec['recommended'] = not warn
        if warn:
            rec['warnings'] = warn
        instead = []
        for x in dep:
            instead += [o.word(t.get('page-id')) for t in d.get_word(x)[:1]]
        if instead:
            rec['see_instead'] = instead
        see = [o.word(t.get('page-id')) for sv in w.findall('see') for t in d.get_word(sv)[:1]]
        if see:
            rec['see'] = see
        mf = merged_from(pid)
        if mf:
            # the roots (and words) of other conceptions Eldamo merged into this one
            rec['merged'] = [o.word(x) for x in mf]
        # a root filed under a Neo-Primitive root (p LUB³ under N√LUP)
        canon = o.canonical(pid)
        filed = [x for x in canon if x not in merged_into(pid)]
        if filed:
            rec['filed_under'] = [o.word(x) for x in filed]
        nested = [x.get('page-id') for x in w.iter('word') if x is not w and d.is_root(x)
                  and x.find('combine') is None and x.get('page-id') in listed]
        if nested:
            rec['filed_here'] = [o.word(x) for x in nested]
        src = [x for x in R.derived_from(w) if d.is_root(x)]
        if src:
            rec['derives_from'] = [o.word(x.get('page-id')) for x in src]
        der = defaultdict(list)
        for g, u in users.get(pid, []):
            der[g].append(u)
        if der:
            rec['derivatives'] = {g: der[g] for g in GROUPS if der.get(g)}
            rec['derivative_count'] = sum(len(v) for v in der.values())
        out.append(rec)
    out.sort(key=lambda r: (_sort_key(r['form']), r['lang'], r['url']))
    return out, extra


def is_listed(e):
    return not e.get('deprecated') and not e.get('merged_into') and not e.get('outside_lists') and not e.get('name')


def stats(entries):
    """Counts for the words of the list; the deprecated words and the merged forms apart."""
    from collections import Counter
    listed = [e for e in entries if is_listed(e)]
    c = Counter(e['rule'] or 'none' for e in listed)
    dep = [e for e in entries if e.get('deprecated')]
    mf = [e for e in entries if e.get('merged_into')]
    ot = [e for e in entries if e.get('outside_lists')]
    nm = [e for e in entries if e.get('name')]
    return {
        'count': len(listed),
        'with_roots': sum(1 for e in listed if e['roots']),
        'by_rule': dict(sorted(c.items(), key=lambda kv: -kv[1])),
        'uncertain': sum(1 for e in listed if e.get('uncertain')),
        'deprecated': {'count': len(dep), 'with_roots': sum(1 for e in dep if e['roots'])},
        'merged_forms': {'count': len(mf), 'with_roots': sum(1 for e in mf if e['roots'])},
        'outside_lists': {'count': len(ot), 'with_roots': sum(1 for e in ot if e['roots'])},
        'names': {'count': len(nm), 'with_roots': sum(1 for e in nm if e['roots'])},
    }


def main(argv):
    """python neo_roots.py eldamo-data.xml [out.json] [nq|ns ...]"""
    if len(argv) < 2:
        print(__doc__)
        return 2
    out = argv[2] if len(argv) > 2 else 'neo-roots.json'
    groups = [g for g in argv[3:] if g in GROUPS] or list(GROUPS)
    d = Data(argv[1])
    R = Resolver(d)
    words, info = [], {}
    for g in groups:
        entries = build(d, g, R)
        info[g] = dict(
            name=GROUPS[g]['name'],
            list=f'https://eldamo.org/content/vocabulary-indexes/vocabulary-words-{g}.html',
            **stats(entries))
        words += entries
        s = info[g]
        print(f"{g}: {s['count']} words, with roots {s['with_roots']}, uncertain {s['uncertain']}, {s['by_rule']};"
              f" deprecated {s['deprecated']}, merged forms {s['merged_forms']}, outside the lists {s['outside_lists']}, names {s['names']}")
    # the index of roots counts the words of the lists only
    roots, unlisted = build_root_index(d, R, [e for e in words if is_listed(e)]) if set(groups) == set(GROUPS) else ([], [])
    if roots:
        info['roots'] = {
            'list': 'https://eldamo.org/content/root-indexes/roots-np.html',
            'count': sum(1 for r in roots if r.get('in_list', True)),
            'recommended': sum(1 for r in roots if r['recommended'] and r.get('in_list', True)),
            'with_derivatives': sum(1 for r in roots if r.get('derivatives') and r.get('in_list', True)),
            'recommended_without_derivatives': sum(1 for r in roots if r['recommended'] and not r.get('derivatives')
                                                   and r.get('in_list', True)),
        }
        info['roots']['not_in_list'] = len(unlisted)
        print('roots:', info['roots'])
    doc = {
        'source': {'eldamo_version': d.root.get('version'), 'site': 'https://eldamo.org'},
        'groups': info,
        'words': words,
        'roots': roots,
    }
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
