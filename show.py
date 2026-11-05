"""Compact view of entries of neo-roots.json:

    python show.py neo-roots.json form [form...]          roots, gaps, also
    python show.py --tree neo-roots.json form [form...]   the derivation tree
    python show.py --root neo-roots.json ROOT [ROOT...]   a root of the root index

--en prints the labels in English (Russian by default).
"""
import json
import sys

LABELS = {
    'ru': {
        'shortcut': '(напрямую; тот же корень и через праформу)', 'gap': '— без корня', 'nm': '✗ не сошлись:',
        'written': 'записано', 'recommended': 'рекомендован', 'not_listed': 'вне перечня Eldamo',
        'see_instead': 'вместо него', 'see': 'см.', 'merged': 'слиты в него', 'merged_into': 'слит в',
        'filed_under': 'записан под', 'filed_here': 'под ним записаны', 'derives_from': 'выводится из',
        'through': 'через',
        'struck': '(по зачёркнутой Толкином ссылке)',
    },
    'en': {
        'shortcut': '(direct; the same root also through the primitive form)', 'gap': '— no root', 'nm': '✗ not matched:',
        'written': 'written', 'recommended': 'recommended', 'not_listed': 'not in the Eldamo list',
        'see_instead': 'instead', 'see': 'see', 'merged': 'merged into it', 'merged_into': 'merged into',
        'filed_under': 'filed under', 'filed_here': 'filed under it', 'derives_from': 'derives from',
        'through': 'through',
        'struck': '(by a reference Tolkien struck out)',
    },
}
L = LABELS['en' if '--en' in sys.argv else 'ru']

KIND = {'root': '√', 'protoform': '✶', 'form': ''}


def fmt_root(r):
    s = f"{r['lang']} {r['form']}"
    if 'part' in r:
        s = f"[{r['part']}] " + s
    if r.get('via'):
        s += '  ⟵ ' + ' ⟵ '.join(f"{v['rel']}:{v['lang']} {v['form']}" for v in r['via'])
    if r.get('same_as'):
        s += '  ≡ ' + ' ≡ '.join(f"{x['lang']} {x['form']}" for x in r['same_as'])
    if r.get('not_matched'):
        s += '  ✗ ' + ', '.join(x['form'] for x in r['not_matched'])
    if r.get('rule'):
        s += f"  ({r['rule']})"
    return s


def head(e):
    kind = ''
    if e.get('deprecated'):
        kind = '  [deprecated → ' + ', '.join(f"{x['lang']} {x['form']}" for x in e.get('see_instead', [])) + ']'
    elif e.get('merged_into'):
        kind = f"  [merged into {e['merged_into']['lang']} {e['merged_into']['form']}]"
    return f"{e['lang']} {e['word']} ({e['speech']}) '{e['gloss']}'  rule={e['rule']} {e.get('uncertain', '')} {e['url']}{kind}"


def show(e):
    print(head(e))
    for r in e['roots']:
        print('   root', fmt_root(r))
    for r in e.get('gaps', []):
        print('   gap ', fmt_root(r))
    for r in e.get('also', []):
        print('   also', fmt_root(r))


def show_tree(e):
    print(head(e))

    def node(n, depth, mark):
        pad = '   ' * depth
        s = f"{pad}{mark}{n['rel']}: {n['lang']} {KIND.get(n['kind'], '')}{n['form']}"
        if n.get('shortcut'):
            s += '  ' + L['shortcut']
        if n.get('gap'):
            s += '  ' + L['gap']
        if n.get('struck'):
            s += '  ' + L['struck']
        if n.get('not_matched'):
            s += f"  {L['nm']} " + ', '.join(x['form'] for x in n['not_matched'])
        if n.get('same_as'):
            s += '  ≡ ' + ' ≡ '.join(f"{x['lang']} {x['form']}" for x in n['same_as'])
        print(s)
        for w in n.get('written', []):
            chain = ' > '.join([w['form']] + w.get('intermediate', []))
            print(f"{pad}      {L['written']} {w['source']}: {chain} > {w['ref']}")
        block(n, depth + 1)

    def block(n, depth):
        for k, p in enumerate(n.get('parts', [])):
            node(p, depth, f"[{k}] ")
        alts = n.get('from', [])
        for a in alts:
            node(a, depth, '| ' if len(alts) > 1 else '')

    block(e.get('tree', {}), 1)


def show_root(r):
    w = lambda x: f"{x['lang']} {x['form']}"
    status = L['recommended'] if r['recommended'] else '⚠️ ' + ', '.join(r.get('warnings', []))
    if r.get('in_list') is False:
        status += f"; {L['not_listed']} ({r['not_listed_because']})"
    print(f"{w(r)} '{r.get('gloss', '')}'  {status}  {r['url']}")
    for key in ('see_instead', 'see', 'merged', 'merged_into', 'filed_under', 'filed_here', 'derives_from'):
        label = L[key]
        if r.get(key):
            print(f"   {label}: " + ', '.join(w(x) for x in r[key]))
    for g, us in r.get('derivatives', {}).items():
        items = [u['word'] + (f" ({L['through']} {u['through']['form']})" if 'through' in u else '') for u in us]
        print(f"   {g} ({len(us)}): " + ', '.join(items))


if __name__ == '__main__':
    args = sys.argv[1:]
    tree = '--tree' in args
    root = '--root' in args
    args = [a for a in args if a not in ('--tree', '--root', '--en')]
    doc = json.load(open(args[0], encoding='utf-8'))
    want = set(args[1:])
    if root:
        for r in doc.get('roots', []):
            if r['form'] in want:
                show_root(r)
        sys.exit(0)
    for e in doc['words']:
        if e['word'] in want or e['spelling'] in want:
            (show_tree if tree else show)(e)
