#!/usr/bin/env python3
"""The graph of neo-roots.json for the interactive page.

    python make_graph.py neo-roots.json graph_template.html neo-roots-graph.html [--standalone]

--standalone wraps the page in its own <!doctype html>, <head> and <body>, for opening the
file straight in a browser (the template itself is a page body, as the artifact host
expects). The page loads d3 from cdnjs and the fonts from Google Fonts.

Nodes are Eldamo pages (words, primitive forms, roots), keyed by page id; edges go from
the origin to what comes from it (root -> primitive form -> word), with the relation:
deriv, element, combine, see, deprecated, cognate (from the trees of the words) and
merged, filed, rootderiv (from the index of roots). The graph is written as compact JSON
into the template, at the /*GRAPH*/ placeholder, and the interface catalog graph_messages.json
(key -> {ru, en}, next to the template) at /*MESSAGES*/, so the page is one self-contained file.
"""
import json
import os
import sys

# 'instead': a deprecated word -> what Eldamo suggests instead (not a link of origin)
# 'cognates': the Cognates section of a word's page (comparison, not origin; one link per pair)
RELS = ['deriv', 'element', 'combine', 'see', 'deprecated', 'cognate', 'merged', 'filed', 'rootderiv', 'instead', 'cognates']
KINDS = ['word', 'form', 'protoform', 'root']
WARN = ['deprecated', 'deleted', 'rejected', 'doubtful', 'unglossed', 'early']


def pid(url):
    return url.split('word-')[1].split('.')[0] if url else None


HEAD = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>html{color-scheme:light}body{margin:0;font:14px system-ui,sans-serif}[hidden]{display:none!important}</style>
</head>
<body>
"""


def main(src, template, out, standalone=False):
    doc = json.load(open(src, encoding='utf-8'))
    nodes = {}          # id -> record
    edges = {}          # (from, to, rel) -> record

    def node(i, form, lang, kind, gloss=None):
        n = nodes.get(i)
        if n is None:
            n = nodes[i] = {'f': form, 'l': lang, 'k': kind}
        if gloss and not n.get('g'):
            n['g'] = gloss
        # a page met as a word of the lists stays a word; a root stays a root
        if KINDS.index(kind) > KINDS.index(n['k']) and n['k'] != 'word':
            n['k'] = kind
        return n

    shortcut = {}       # (from, to, rel) -> True while every occurrence is a shortcut
    unmatched = {}      # (from, to, rel) -> True while every occurrence is not matched (a partial cognate)
    struck = {}         # (from, to, rel) -> True while every occurrence comes from a struck reference

    def edge(a, b, rel, written=None, nm=False, sc=False, st=False):
        key = (a, b, rel)
        struck[key] = struck.get(key, True) and st
        shortcut[key] = shortcut.get(key, True) and sc
        unmatched[key] = unmatched.get(key, True) and nm
        e = edges.get(key)
        if e is None:
            e = edges[key] = {}
        if written:
            e.setdefault('w', [])
            for w in written:
                chain = [w['form']] + w.get('intermediate', []) + [w['ref']]
                rec = [w['source'], chain]
                if rec not in e['w']:
                    e['w'].append(rec)
        return e

    # the words of the three lists
    for e in doc['words']:
        i = pid(e['url'])
        if e.get('outside_lists'):
            # not a word of a list: drawn as the form or primitive form it is
            n = node(i, e['word'], e['lang'], 'protoform' if e['lang'] in ('p', 'mp', 'ep', 'np') else 'form', e['gloss'])
        else:
            n = node(i, e['word'], e['lang'], 'word', e['gloss'])
            n['k'] = 'word'
        n['grp'] = e['group']
        # x: absent for a word of the list, 'd' for a deprecated word, 'm' for a form of another
        # conception merged into a word (shown under it on Eldamo's page), 'o' for another word
        # Eldamo marks ⚠️ and lists nowhere (G. caineglad), 'n' for a name (Q. Tareldar)
        if e.get('deprecated'):
            n['x'] = 'd'
        elif e.get('merged_into'):
            n['x'] = 'm'
        elif e.get('outside_lists'):
            n['x'] = 'o'        # outside Eldamo's vocabulary and deprecation pages (⚠️ there)
        elif e.get('name'):
            n['x'] = 'n'        # a name (Q. Tareldar): on no vocabulary page
        n['s'] = e['speech']
        if e.get('rule'):
            n['r'] = e['rule']
        if e.get('uncertain'):
            n['u'] = 1
        if e['group'] == 'nq' and e['spelling'] != e['word']:
            n['sp'] = e['spelling']
        if e.get('alt_lang'):
            n['al'] = e['alt_lang']      # Eldamo prints it in brackets: ᴺQ. [ᴱQ.] ulumpë
        src = e.get('alt_source')
        if src:
            n['as'] = [src.get('id') or '', src['form']]   # its base: ᴱQ. aiko for ᴺQ.[ᴱQ.] aico
        if e.get('warnings'):
            n['wn'] = [WARN.index(x) for x in e['warnings']]   # Eldamo's ⚠️ and why

    gap_seq = [0]
    in_tree = set()     # nodes some word's tree passes through

    def walk(parent_id, t):
        for c in t.get('parts', []) + t.get('from', []):
            ci = pid(c.get('url'))
            if ci is not None:
                in_tree.add(ci)
            if ci is None:                       # an element Eldamo has no page for
                gap_seq[0] += 1
                ci = f"x{gap_seq[0]}"
            node(ci, c['form'], c['lang'], c['kind'], c.get('gloss'))
            edge(ci, parent_id, c['rel'], c.get('written'), nm=bool(c.get('not_matched')),
                 sc=bool(c.get('shortcut')), st=bool(c.get('struck')))
            walk(ci, c)

    for e in doc['words']:
        walk(pid(e['url']), e.get('tree', {}))
    # cognates: one link per pair, from the smaller page id; not where a cognate already gives a root
    before_cognates = set(nodes)
    for e in doc['words']:
        i = pid(e['url'])
        for x in e.get('cognates', []):
            xi = pid(x['url'])
            if xi is None or xi == i:
                continue
            node(xi, x['form'], x['lang'], 'word', x.get('gloss'))
            if (xi, i, 'cognate') in edges or (i, xi, 'cognate') in edges:
                continue
            a, b = sorted((i, xi), key=lambda v: (len(v), v))
            edge(a, b, 'cognates')
    # nodes known only as someone's cognate (T., Ilk. words...): they start no chain here
    for v in set(nodes) - before_cognates:
        nodes[v]['cg'] = 1
    for i in in_tree:
        if nodes[i].get('x') in ('o', 'n'):
            nodes[i]['iv'] = 1  # an outside word or a name on another's way to a root: shown without its switch
    for e in doc['words']:
        i = pid(e['url'])
        if e.get('merged_into'):
            edge(i, pid(e['merged_into']['url']), 'combine')
        for x in e.get('see_instead', []):
            xi = pid(x['url'])
            node(xi, x['form'], x['lang'], 'word', x.get('gloss'))
            nodes[i].setdefault('ins', []).append(xi)
            # a form merged into the very word suggested instead is already linked to it
            if not (e.get('merged_into') and pid(e['merged_into']['url']) == xi):
                edge(i, xi, 'instead')

    # the index of roots
    for r in doc['roots']:
        i = pid(r['url'])
        n = node(i, r['form'], r['lang'], 'root', r.get('gloss'))
        n['k'] = 'root'
        n['rec'] = 1 if r['recommended'] else 0
        if r.get('warnings'):
            n['wn'] = [WARN.index(x) for x in r['warnings']]
        if r.get('alt_lang'):
            n['al'] = r['alt_lang']
        if r.get('in_list') is False:
            n['nl'] = 1
        if r.get('see_instead'):
            n['ins'] = [pid(x['url']) for x in r['see_instead']]
        for x in r.get('merged', []):
            xi = pid(x['url'])
            node(xi, x['form'], x['lang'], 'root', x.get('gloss'))
            edge(xi, i, 'merged')
        for x in r.get('filed_here', []):
            xi = pid(x['url'])
            node(xi, x['form'], x['lang'], 'root', x.get('gloss'))
            edge(xi, i, 'filed')
        for x in r.get('derives_from', []):
            xi = pid(x['url'])
            node(xi, x['form'], x['lang'], 'root', x.get('gloss'))
            edge(xi, i, 'rootderiv')
        if r.get('derivative_count'):
            n['dc'] = r['derivative_count']

    for key, e in edges.items():
        if unmatched.get(key):
            # not matched in every tree it appears in: the same link elsewhere is a real one
            e['nm'] = 1
        if shortcut.get(key):
            e['sc'] = 1     # the root named directly beside a path through an intermediate form
        if struck.get(key):
            e['st'] = 1     # given only by references Tolkien struck out (Eldamo lists them)
    # nodes that do not go back to a root: not reached from any root along the links of origin
    # (a partial cognate's unmatched link does not count); `nr` marks them, `ds` is the number of
    # words of the three lists that come from such a node
    origin = {'deriv', 'element', 'combine', 'see', 'deprecated', 'cognate'}
    down = {}
    for (a, b, rel), e in edges.items():
        if rel in origin and not e.get('nm'):
            down.setdefault(a, []).append(b)
    reached = {i for i, n in nodes.items() if n['k'] == 'root'}
    todo = list(reached)
    while todo:
        for y in down.get(todo.pop(), ()):
            if y not in reached:
                reached.add(y)
                todo.append(y)
    # a word with an entry of its own goes back to a root exactly when its entry has roots (the
    # rules limit some paths -- a cognate counts for the word itself only, so G. laboth's root
    # through a cognate does not pass on to NS. laboth); other nodes by the walk above
    has_entry = {}
    for e in doc['words']:
        has_entry[pid(e['url'])] = bool(e['roots'])
    for i, n in nodes.items():
        if n['k'] == 'root':
            continue
        if has_entry.get(i, i in reached):
            continue
        n['nr'] = 1
        seen, todo = {i}, [i]
        while todo:
            for y in down.get(todo.pop(), ()):
                if y not in seen:
                    seen.add(y)
                    todo.append(y)
        ds = sum(1 for y in seen if y != i and nodes[y].get('grp') and not nodes[y].get('x'))
        if ds:
            n['ds'] = ds
    ids = list(nodes)
    index = {x: k for k, x in enumerate(ids)}
    graph = {
        'version': doc['source']['eldamo_version'],
        'rels': RELS,
        'kinds': KINDS,
        'warn': WARN,
        'ids': ids,
        'nodes': [nodes[x] for x in ids],
        'edges': [[index[a], index[b], RELS.index(rel)] + ([e] if e else [])
                  for (a, b, rel), e in edges.items()],
    }
    data = json.dumps(graph, ensure_ascii=False, separators=(',', ':'))
    data = data.replace('</', '<\\/')
    page = open(template, encoding='utf-8').read()
    assert '/*GRAPH*/' in page and '/*MESSAGES*/' in page
    # the interface catalog (key -> {ru, en}) lies next to the template
    messages = os.path.join(os.path.dirname(os.path.abspath(template)), 'graph_messages.json')
    catalog = json.load(open(messages, encoding='utf-8'))
    page = page.replace('/*MESSAGES*/', json.dumps(catalog, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'), 1)
    page = page.replace('/*GRAPH*/', data, 1)
    if standalone:
        page = HEAD + page + '\n</body>\n</html>\n'
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(page)
    from collections import Counter
    print(len(ids), 'nodes', dict(Counter(n['k'] for n in nodes.values())),
          len(edges), 'edges', dict(Counter(r for _, _, r in edges)), f'{len(data) / 1e6:.1f} MB of data')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--standalone']
    if len(args) < 3:
        print(__doc__)
        sys.exit(2)
    main(*args[:3], standalone='--standalone' in sys.argv)
