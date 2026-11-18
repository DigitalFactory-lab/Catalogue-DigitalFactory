"""Pages intégrées (<x-embed>) de la couverture.

Le lecteur de présentation lit le HTML des diapositives et le reconstruit ; les animations SMIL
des dessins n'y passent pas. Une page intégrée, elle, tourne telle quelle dans un iframe :
Slides ne lit pas son contenu. On y met tout ce qui bouge de façon complexe :
  - l'intro : chaque partie du logo construite par une machine, puis le logo part en haut à gauche ;
  - l'impression du « 6 » par la buse ;
  - la maquette de l'atelier qui se dessine au trait.
Chaque page démarre quand elle devient visible (IntersectionObserver) et repart de zéro
si on revient sur la diapositive. Sans animation (export, capture automatique, Réduire
les animations), la page reste vide : la diapositive montre alors ses propres éléments fixes
(logo, 6, maquette), qui apparaissent aussi en fondu à la fin de chaque séquence.
Contraintes : 16 Ko par page, pas de réseau, pas de SMIL ; noms préfixés « xq » au cas où
une règle s'échapperait de l'iframe.
"""
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = json.load(open(os.path.join(HERE, 'logo_parts.json')))
DARK, BLUE, VIOLET = '#2f3a48', '#5b60a8', '#8c4292'
PINK, WHITE, LIGHT = '#F0268B', '#FFFFFF', '#E1E4EA'
TEAL = LOGO['teal']['color']
LIMIT = 15800


# ---------------------------------------------------------------- tracés compacts
def g(v):
    """Nombre court : 2 décimales au plus, sans zéros inutiles."""
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def join(vals):
    out = ''
    for v in vals:
        s = str(v)
        if out and not s.startswith('-') and out[-1] not in 'MmLlHhVvZz':
            out += ' '
        out += s
    return out


def logo_polys(d):
    out = []
    for sub in d.split('M')[1:]:
        nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', sub)]
        out.append(list(zip(nums[0::2], nums[1::2])))
    return out


def enc(subpaths, k=4, closed=True):
    """Tracé relatif en unités entières (coordonnées × k), segments h/v quand c'est possible."""
    out, cur, start = [], (0, 0), (0, 0)
    first = True
    for pts in subpaths:
        q = []
        for x, y in pts:
            p = (round(x * k), round(y * k))
            if not q or p != q[-1]:
                q.append(p)
        if closed and len(q) > 1 and q[-1] == q[0]:
            q.pop()
        if first:
            out.append('M' + join([q[0][0], q[0][1]]))
            first = False
        else:
            out.append('m' + join([q[0][0] - cur[0], q[0][1] - cur[1]]))
        last = 'M' if len(out) == 1 else 'm'
        start = cur = q[0]
        for p in q[1:]:
            dx, dy = p[0] - cur[0], p[1] - cur[1]
            if dy == 0:
                tok = (('' if last == 'h' else 'h'), [dx]); last = 'h'
            elif dx == 0:
                tok = (('' if last == 'v' else 'v'), [dy]); last = 'v'
            else:
                tok = (('' if last in ('l', 'm') else 'l'), [dx, dy]); last = 'l'
            letter, vals = tok
            seg = join(vals)
            if letter:
                out.append(letter + seg)
            else:
                prev = out[-1]
                out[-1] = prev + ('' if seg.startswith('-') else ' ') + seg
            cur = p
        if closed:
            out.append('z')
            cur = start
    return ''.join(out)


def _dp(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        p = pts[i]
        if a == b:
            d = math.hypot(p[0] - a[0], p[1] - a[1])
        else:
            d = abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1])) / math.hypot(b[0] - a[0], b[1] - a[1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        return _dp(pts[:idx + 1], tol)[:-1] + _dp(pts[idx:], tol)
    return [a, b]


def simplify(pts, tol=0.3):
    """Contour fermé simplifié (écart maximal tol, en px)."""
    far = max(range(len(pts)), key=lambda i: math.hypot(pts[i][0] - pts[0][0], pts[i][1] - pts[0][1]))
    r = pts + [pts[0]]
    return _dp(r[:far + 1], tol)[:-1] + _dp(r[far:], tol)[:-1]


def logo_d(keys, k=4):
    subs = []
    for key in keys:
        subs += logo_polys(LOGO[key]['d'])
    return enc(subs, k)


def poly_len(subpaths, closed=True):
    L = 0.0
    for pts in subpaths:
        p = pts + [pts[0]] if closed else pts
        L += sum(math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1]) for i in range(len(p) - 1))
    return L


# ---------------------------------------------------------------- page commune
def page(w, h, css, body, play=''):
    """Page intégrée : scène à l'échelle de l'iframe, démarrage quand elle est visible.
    play : corps JS exécuté à chaque démarrage (animations Web Animations), en plus des @keyframes CSS."""
    js = ('(function(){var d=document,R=d.documentElement,S=d.getElementById("xq-s"),A=[];'
          f'function f(){{var w=R.clientWidth||innerWidth;if(w)S.style.transform="scale("+w/{w}+")"}}'
          'f();addEventListener("resize",f);if(window.ResizeObserver)new ResizeObserver(f).observe(R);'
          'if(navigator.webdriver)return;'
          f'function play(){{A.forEach(function(a){{a.cancel()}});A=[];{play}}}'
          'var on=0;function go(v){if(v==on)return;on=v;R.classList.remove("xq-go");'
          'if(v){f();void R.offsetWidth;R.classList.add("xq-go");play()}}'
          'if(!window.IntersectionObserver)return go(1);'
          'new IntersectionObserver(function(e){var r=e[e.length-1].intersectionRatio;'
          'if(r>=.5)go(1);else if(r==0)go(0)},{threshold:[0,.5]}).observe(d.getElementById("xq-v"))})()')
    base = (f'#xq-s{{position:absolute;left:0;top:0;width:{w}px;height:{h}px;overflow:hidden;'
            'transform-origin:0 0;visibility:hidden}.xq-go #xq-s{visibility:visible}'
            '#xq-s div,#xq-s svg{position:absolute;left:0;top:0}'
            '#xq-v{position:fixed;left:0;top:0;width:100%;height:100%;visibility:hidden}'
            '@media (prefers-reduced-motion:reduce){#xq-s{display:none}}')
    return (f'<!doctype html><style>{base}{css}</style>'
            f'<i id="xq-v"></i><div id="xq-s">{body}</div><script>{js}</script>')


def n(v):
    """Nombre pour les données JS : sans zéro de tête."""
    s = g(v)
    return s.replace('0.', '.', 1) if s.startswith('0.') else (s.replace('-0.', '-.', 1) if s.startswith('-0.') else s)


# Données d'animation lues par le script : [id, easing, [t, opacité, x, y(, échelle)] ou [t, opacité, haut, droite, bas, gauche]]
WAAPI = ('D.forEach(function(q){var e=d.getElementById(q[0]),f=q.slice(2),t0=f[0][0],T=f[f.length-1][0]-t0||1;'
         'A.push(e.animate(f.map(function(k){var o={offset:(k[0]-t0)/T,opacity:k[1]};'
         'if(k.length>5)o.clipPath="inset("+k[2]+"px "+k[3]+"px "+k[4]+"px "+k[5]+"px)";'
         'else o.transform="translate("+k[2]+"px,"+k[3]+"px)"+(k[4]?" scale("+k[4]+")":"");'
         'if(q[1])o.easing=q[1];return o}),{duration:T*1e3,delay:t0*1e3,fill:"both"}))});')


class Data:
    def __init__(self):
        self.items = []

    def add(self, eid, frames, easing=None):
        """frames : [(t, opacité, valeurs...)] complets (toutes les valeurs à chaque instant)."""
        rows = ','.join('[' + ','.join(n(v) for v in fr) + ']' for fr in frames)
        e = f'"{easing}"' if easing else '0'
        self.items.append(f'["{eid}",{e},{rows}]')

    def js(self):
        return 'var D=[' + ','.join(self.items) + '];'


def track(keys, t):
    """keys : [(t, v)] → valeur interpolée linéairement à l'instant t."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (ta, va), (tb, vb) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            return va if tb == ta else va + (vb - va) * (t - ta) / (tb - ta)
    return keys[-1][1]


def frames(tracks):
    """tracks : liste de pistes [(t, v)] ; renvoie [(t, v1, v2, ...)] aux instants de toutes les pistes."""
    ts = sorted(set(t for tk in tracks for t, _ in tk))
    return [(t,) + tuple(track(tk, t) for tk in tracks) for t in ts]


# ================================================================ 1. intro : le logo construit par les machines
EX, EY, EW, EH = 124, 98, 1296, 542            # zone de la page intégrée, en px de diapositive
VB = (580, 428, 760, 184)                       # cadre du logo pendant la construction
SC = 0.45                                       # taille finale du logo
FIN_X, FIN_Y = 128 - (584 - VB[0]) * SC, 104 - (434 - VB[1]) * SC
T_MOVE = 7.0
LZ0, LZ1 = 0.5, 2.0                             # laser : « digital »
P0, P1 = 2.1, 3.4                               # imprimante 3D : « FACTORY »
C0, C1 = 3.4, 4.1                               # fraiseuse : séparateur
B0, B1 = 4.2, 4.8                               # traceur de découpe : « By »
U0, U1, U2, U3 = 4.8, 5.3, 5.38, 5.88           # impression UV : « forem », deux passages
H0, H1, H2 = 6.3, 6.5, 6.75                     # presse : point turquoise


def x_laser(t):
    return 584 + (1053 - 584) * max(0.0, min(1.0, (t - LZ0) / (LZ1 - LZ0)))


def edge_fdm(t):
    return 598 - 30 * max(0.0, min(1.0, (t - P0) / (P1 - P0)))


def intro_embed():
    K = 2
    fx, fy = VB[0], VB[1]
    R_, B_ = VB[0] + VB[2], VB[1] + VB[3]      # bords droit et bas du cadre du logo
    D = Data()
    css = []

    IDS = {'digital': 'd', 'factory': 'f', 'sep': 's', 'by': 'b', 'forem': 'o'}

    def rel(keys):
        """Tracés du logo, relatifs au cadre, simplifiés à 0,3 px près."""
        subs = []
        for key in keys:
            subs += [simplify([(x - fx, y - fy) for x, y in p]) for p in logo_polys(LOGO[key]['d'])]
        return subs

    defs = ''.join(f'<path id="p{v}" fill-rule="evenodd" transform="scale({g(1 / K)})" d="{enc(rel([k]), K)}"/>'
                   for k, v in IDS.items())
    Lby = poly_len(rel(['by'])) * K

    def part(pid, ref, fill=None):
        f = f' fill="{fill}"' if fill else ''
        return f'<div id="{pid}"><svg><use href="#p{ref}"{f}/></svg></div>'

    def clip(eid, op, top=((0, 0),), right=((0, 0),), bottom=((0, 0),), left=((0, 0),)):
        D.add(eid, frames([op, top, right, bottom, left]))

    # ---- les parties du logo
    clip('dp', [(LZ0 - 0.05, 0), (LZ0, 1), (LZ1 + 0.08, 1), (LZ1 + 0.18, 0)],
         right=[(LZ0 - 0.05, R_ - 584), (LZ0, R_ - 584), (LZ1, R_ - 1053)])
    tb0 = LZ0 + 23 / ((1053 - 584) / (LZ1 - LZ0))
    clip('db', [(tb0, 1)], right=[(tb0, R_ - 583), (LZ1, R_ - 1029), (LZ1 + 0.08, R_ - 1055)])
    clip('fb', [(P0, 1)], top=[(P0, 601 - fy), (P1, edge_fdm(P1) + 6 - fy), (P1 + 0.15, 566 - fy)])
    clip('fu', [(P0 - 0.05, 0), (P0, 1), (P1 + 0.15, 1), (P1 + 0.2, 0)],
         top=[(P0, edge_fdm(P0) - fy), (P1, edge_fdm(P1) - fy)],
         bottom=[(P0, B_ - (edge_fdm(P0) + 6)), (P1, B_ - (edge_fdm(P1) + 6))])
    clip('sp', [(C0, 1)], bottom=[(C0, B_ - 440), (C1, B_ - 601)])
    clip('ft', [(U0, 1)], top=[(U0, 536 - fy)], bottom=[(U0, B_ - 577)], left=[(U0, 760), (U1, 1156 - fx)])
    clip('fo', [(U2, 1)], top=[(U2, 577 - fy)], bottom=[(U2, B_ - 610)], left=[(U2, 1156 - fx)],
         right=[(U2, R_ - 1156), (U3, 0)])
    D.add('bf', frames([[(B1 - 0.05, 0), (B1 + 0.15, 1)], [(0, 0)], [(0, 0)]]))
    D.add('td', frames([[(H1 - 0.1, 0), (H1 + 0.02, 1)], [(0, 0)], [(0, 0)]]))
    lx, ly = fx - EX, fy - EY
    D.add('L', [(T_MOVE, 1, 0, 0, 1), (T_MOVE + 0.8, 1, round(FIN_X - EX - lx, 2), round(FIN_Y - EY - ly, 2), SC)],
          easing='cubic-bezier(.5,0,.3,1)')
    # « By » : la lame trace le contour en rose
    pc = lambda t: g((t - (B0 - 0.05)) / (B1 + 0.3 - (B0 - 0.05)) * 100)
    css.append(f'@keyframes bs{{0%{{opacity:0;stroke-dashoffset:{g(Lby)}}}{pc(B0)}%{{opacity:1;stroke-dashoffset:{g(Lby)}}}'
               f'{pc(B1)}%{{stroke-dashoffset:0}}{pc(B1 + 0.1)}%{{opacity:1}}100%{{opacity:0;stroke-dashoffset:0}}}}'
               f'.xq-go #bs use{{animation:bs {g(B1 + 0.35 - B0)}s linear {g(B0 - 0.05)}s both}}')
    # onde rose quand la presse tamponne le point turquoise
    css.append('@keyframes rg{0%{opacity:0;width:14px;height:14px;margin:-7px}11%{opacity:.9}'
               f'100%{{opacity:0;width:60px;height:60px;margin:-30px}}}}.xq-go #rg{{animation:rg .45s linear {g(H1)}s both}}')
    tb = LOGO['teal']['bbox']
    logo = (
        f'<svg width="0" height="0"><defs>{defs}</defs></svg>'
        f'<div id="L" style="left:{lx}px;top:{ly}px;width:{VB[2]}px;height:{VB[3]}px;transform-origin:0 0">'
        + part('dp', 'd', PINK) + part('db', 'd') + part('fb', 'f') + part('fu', 'f', BLUE)
        + part('sp', 's') + part('bf', 'b')
        + f'<div id="bs"><svg><use href="#pb" fill="none" stroke="{PINK}" stroke-width="{g(1.6 * K)}" stroke-linejoin="round" '
          f'stroke-dasharray="{g(Lby)} {g(Lby + 16)}"/></svg></div>'
        + part('ft', 'o') + part('fo', 'o')
        + f'<div id="rg" style="left:{g((tb[0] + tb[2]) / 2 - fx)}px;top:{g((tb[1] + tb[3]) / 2 - fy)}px;'
          f'width:14px;height:14px;margin:-7px;box-sizing:border-box;border:2.5px solid {PINK};border-radius:50%;opacity:0"></div>'
        + f'<div id="td" style="left:{g(tb[0] - fx)}px;top:{g(tb[1] - fy)}px;width:{g(tb[2] - tb[0])}px;'
          f'height:{g(tb[3] - tb[1])}px;background:{TEAL}"></div></div>'
    )
    # ---- les machines (un seul SVG, coordonnées de diapositive)
    o = []
    S = f'stroke="{DARK}"'

    def appear(t_in, t_out):
        return [(t_in, 0), (t_in + 0.25, 1), (t_out, 1), (t_out + 0.25, 0)]

    def mach(eid, op, xs, ys, easing=None):
        D.add(eid, frames([op, xs, ys]), easing)

    o.append(f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PINK}"/>'
             f'<stop offset=".8" stop-color="{PINK}"/><stop offset="1" stop-color="{PINK}" stop-opacity=".2"/></linearGradient>'
             '<clipPath id="bc"><rect x="1080" y="403" width="8" height="34"/></clipPath></defs>')

    # 1. découpeuse laser : portique, tête, faisceau ; étincelles et fumée derrière lui
    mach('a', appear(0.15, LZ1 + 0.05), [(0, 0)], [(0.15, -14), (0.4, 0), (LZ1 + 0.05, 0), (LZ1 + 0.3, -14)])
    o.append('<g id="a"><rect class="w" x="548" y="345" width="14" height="26" rx="3"/>'
             '<rect class="w" x="1078" y="345" width="14" height="26" rx="3"/>'
             '<rect class="w b" x="560" y="352" width="520" height="12" rx="6"/></g>')
    sparks = []
    for i, t in enumerate([LZ0 + 0.12 + k * 0.17 for k in range(8)]):
        dx, dy = (-14 if i % 2 else 12), (-16 if i % 3 else 10)
        sparks.append((t, x_laser(t), 450 + (i * 37) % 110, dx, dy, 2 + i % 2 * 0.6))
    dirs = sorted(set((dx, dy) for _, _, _, dx, dy, _ in sparks))
    for k, (dx, dy) in enumerate(dirs):
        css.append(f'@keyframes s{k}{{0%{{opacity:0;transform:none}}15%{{opacity:1}}'
                   f'100%{{opacity:0;transform:translate({dx}px,{dy}px)}}}}.xq-go .s{k}{{animation:s{k} .4s linear both}}')
    for t, x, y, dx, dy, r in sparks:
        o.append(f'<circle class="s{dirs.index((dx, dy))}" cx="{round(x)}" cy="{y}" r="{g(r)}" style="animation-delay:{n(t)}s"/>')
    css.append('@keyframes sm{0%{opacity:0;transform:none}22%{opacity:.7}100%{opacity:0;transform:translate(0,-36px) scale(2.75)}}'
               '.sm{transform-box:fill-box;transform-origin:center;opacity:0}.xq-go .sm{animation:sm .9s linear both}')
    for t in [LZ0 + 0.2 + k * 0.28 for k in range(5)]:
        o.append(f'<circle class="sm" cx="{round(x_laser(t) - 14)}" cy="440" r="4" style="animation-delay:{n(t)}s"/>')
    mach('b', appear(0.15, LZ1 + 0.05), [(LZ0, 0), (LZ1, 469)], [(0.15, -14), (0.4, 0), (LZ1 + 0.05, 0), (LZ1 + 0.3, -14)])
    D.add('bb', frames([[(LZ0 - 0.1, 0), (LZ0, 1), (LZ1, 1), (LZ1 + 0.1, 0)], [(0, 0)], [(0, 0)]]))
    D.add('bd', frames([[(0, 1)], [(0, 0)], [(LZ0, 0), (LZ0 + 0.18, 110), (LZ0 + 0.36, 0), (LZ0 + 0.54, 110), (LZ0 + 0.72, 0),
                                              (LZ0 + 0.9, 110), (LZ0 + 1.08, 0), (LZ0 + 1.26, 110), (LZ1, 30)]]))
    o.append('<g id="b"><g id="bb" opacity="0">'
             f'<rect x="603" y="392" width="10" height="178" fill="{PINK}" opacity=".18"/>'
             '<rect x="606.5" y="392" width="3" height="178" fill="url(#bg)"/>'
             f'<g id="bd"><circle cx="608" cy="448" r="7" fill="{PINK}" opacity=".35"/>'
             f'<circle cx="608" cy="448" r="3.6" fill="{WHITE}"/></g></g>'
             '<rect class="w b" x="584" y="334" width="48" height="42" rx="7"/>'
             f'<rect x="590" y="341" width="36" height="6" rx="3" fill="{BLUE}"/>'
             '<path class="w" d="M599 376h18l-4 14h-10z"/>'
             f'<circle cx="608" cy="390" r="3" fill="{PINK}"/></g>')

    # 2. imprimante 3D : trois passages de la buse, couche par couche
    rise = [(P0 - 0.25, -10), (P0, 0), (P1, edge_fdm(P1) - 598), (P1 + 0.25, -42)]
    mach('c', appear(P0 - 0.25, P1), [(0, 0)], rise)
    o.append('<g id="c"><rect class="w" x="800" y="561" width="250" height="10" rx="5"/></g>')
    mach('e', appear(P0 - 0.25, P1), [(0, 0)], rise)
    third = (P1 - P0) / 3
    D.add('ex', frames([[(0, 1)], [(P0, 0), (P0 + third, 192), (P0 + 2 * third, 0), (P1, 192)], [(0, 0)]]), 'ease-in-out')
    o.append('<g id="e"><g id="ex">'
             f'<path d="M827 512v34" stroke="{BLUE}" stroke-width="5" stroke-linecap="round"/>'
             '<rect class="w b" x="812" y="546" width="30" height="24" rx="5"/>'
             f'<path d="M818 554h18M818 561h18" {S} stroke-width="1.8"/>'
             f'<rect x="819" y="570" width="16" height="8" rx="1.5" fill="{BLUE}"/>'
             f'<path d="M821 578h12l-6 12z" fill="{PINK}"/></g></g>')

    # 3. fraiseuse CNC : la broche descend et taille le séparateur, copeaux projetés
    mach('h', appear(C0 - 0.25, C1), [(0, 0)], [(C0 - 0.25, -14), (C0, 0), (C1, 158), (C1 + 0.25, 144)])
    css.append(f'@keyframes fl{{to{{transform:translate(0,-14px)}}}}.xq-go .fl{{animation:fl .35s linear {n(C0)}s 2 both}}')
    flutes = ''.join(f'M1080 {y + 7}l8-7' for y in range(395, 449, 7))
    o.append('<g id="h">'
             f'<rect class="w" x="1070" y="329" width="28" height="12" rx="4" style="fill:{VIOLET}"/>'
             '<rect class="w b" x="1068" y="341" width="32" height="52" rx="6"/>'
             f'<rect x="1074" y="357" width="20" height="5" rx="2.5" fill="{BLUE}"/>'
             f'<rect class="w" x="1074" y="393" width="20" height="10" rx="2" style="fill:{LIGHT}"/>'
             '<rect class="w" x="1080" y="403" width="8" height="34" style="stroke-width:2"/>'
             f'<g clip-path="url(#bc)"><path class="fl" d="{flutes}" {S} stroke-width="1.6"/></g>'
             f'<path d="M1080 437h8l-4 6z" fill="{PINK}"/></g>')
    for k, side in enumerate((1, -1)):
        css.append(f'@keyframes c{k}{{0%{{opacity:0;transform:none}}13%{{opacity:1}}'
                   f'50%{{transform:translate({side * 26}px,-14px)}}100%{{opacity:0;transform:translate({side * 50}px,12px)}}}}'
                   f'.xq-go .c{k}{{animation:c{k} .6s linear both}}')
    cols = (BLUE, VIOLET, LIGHT, BLUE)
    for i, t in enumerate([C0 + 0.08 + k * 0.08 for k in range(8)]):
        side = 1 if i % 2 == 0 else -1
        o.append(f'<path class="c{i % 2}" d="M{1084 + side * 5} {round(441 + 158 * (t - C0) / (C1 - C0))}h5v2.5h-5z" '
                 f'fill="{cols[i % 4]}" style="animation-delay:{n(t)}s"/>')

    # 4. traceur de découpe : la lame suit « By »
    mach('i', appear(B0 - 0.25, B1), [(0, 0)], [(B0 - 0.25, -12), (B0, 0), (B1, 0), (B1 + 0.25, -12)])
    o.append('<g id="i"><rect class="w" x="1094" y="546" width="74" height="8" rx="4"/></g>')
    mach('j', appear(B0 - 0.25, B1), [(B0, 0), (B0 + 0.12, 8), (B0 + 0.24, 2), (B0 + 0.36, 30), (B0 + 0.48, 22), (B1, 34)],
         [(B0 - 0.25, -12), (B0, 0), (B1, 0), (B1 + 0.25, -12)])
    o.append('<g id="j"><rect class="w" x="1104" y="532" width="24" height="30" rx="4"/>'
             f'<rect x="1108" y="538" width="16" height="4" rx="2" fill="{VIOLET}"/>'
             f'<rect class="w" x="1113" y="562" width="6" height="10" style="fill:{LIGHT};stroke-width:2"/>'
             f'<path d="M1113 572h6l-3 6z" fill="{PINK}"/></g>')

    # 5. impression UV : deux passages sur « forem »
    uvy = [(U0 - 0.25, -12), (U0, 0), (U1, 0), (U2, 30), (U3, 30), (U3 + 0.25, 18)]
    mach('k', appear(U0 - 0.25, U3), [(0, 0)], uvy)
    o.append('<g id="k"><rect class="w" x="1144" y="517" width="210" height="8" rx="4"/></g>')
    css.append('@keyframes dr{0%{opacity:0;transform:none}22%{opacity:1}100%{opacity:0;transform:translate(0,18px)}}'
               '.xq-go .dr{animation:dr .45s linear both}')
    for t, col in [(U0 + 0.1, BLUE), (U0 + 0.22, PINK), (U0 + 0.34, VIOLET), (U2 + 0.1, PINK), (U2 + 0.22, BLUE), (U2 + 0.34, VIOLET)]:
        x, y = (1336 - 176 * (t - U0) / (U1 - U0), 546) if t < U1 else (1160 + 176 * (t - U2) / (U3 - U2), 576)
        o.append(f'<circle class="dr" cx="{round(x)}" cy="{y}" r="2" fill="{col}" style="animation-delay:{n(t)}s"/>')
    mach('l', appear(U0 - 0.25, U3), [(U0, 176), (U1, 0), (U2, 0), (U3, 176)], uvy)
    o.append('<g id="l">'
             f'<rect x="1159" y="548" width="2" height="29" fill="{PINK}" opacity=".9"/>'
             '<rect class="w b" x="1130" y="506" width="60" height="30" rx="6"/>'
             + ''.join(f'<rect x="{x}" y="512" width="7" height="12" rx="2" fill="{c}"/>'
                       for x, c in ((1137, BLUE), (1147, VIOLET), (1157, PINK), (1167, DARK)))
             + f'<rect class="w" x="1136" y="536" width="48" height="5" rx="2.5" style="fill:{LIGHT};stroke-width:2"/></g>')

    # 6. presse à chaud : tamponne le point turquoise
    mach('m', [(H0 - 0.35, 0), (H0 - 0.15, 1), (H2 - 0.05, 1), (H2 + 0.15, 0)], [(0, 0)],
         [(H0 - 0.35, -110), (H0 - 0.15, -90), (H0, 0), (H1, 0), (H2, -60), (H2 + 0.15, -80)])
    o.append('<g id="m"><rect class="w" x="1310" y="500" width="40" height="10" rx="5"/>'
             f'<rect class="w" x="1326" y="510" width="8" height="60" style="fill:{BLUE};stroke-width:2"/>'
             '<rect class="w b" x="1301" y="570" width="58" height="16" rx="4"/>'
             f'<rect x="1306" y="581" width="48" height="2.5" rx="1.2" fill="{PINK}"/></g>')

    machines = f'<svg width="{EW}" height="{EH}" viewBox="{EX} {EY} {EW} {EH}">' + ''.join(o) + '</svg>'
    base = (f'.w{{fill:{WHITE};stroke:{DARK};stroke-width:2.5;stroke-linejoin:round;stroke-linecap:round}}.b{{stroke-width:3}}'
            f'#L div,#L svg{{width:760px;height:184px}}.s0,.s1,.s2,.s3{{fill:{PINK};opacity:0}}.c0,.c1,.dr{{opacity:0}}'
            f'.sm{{fill:{LIGHT}}}')
    return page(EW, EH, base + ''.join(css), logo + machines, D.js() + WAAPI)


# ================================================================ 2. le « 6 » imprimé par la buse
def six_embed(six_svg, sw, sh, ink_top, ink_bot, t0, dur=1.8):
    """Le 6 se révèle de bas en haut pendant que la buse fait ses passages ; elle s'en va à la fin."""
    amp, nw, nh, tip_x, tip_y = 118, 64, 78, 32, 74
    pad_l = max(26, 26 + amp + tip_x - sw / 2)
    pad_t = tip_y - ink_top + 30
    W, H = round(sw + 2 * pad_l), round(sh + pad_t + 6)
    sx, sy = pad_l, pad_t                            # coin du 6 dans la page
    travel = ink_bot - ink_top
    T = dur + 0.42
    pc = lambda t: g((t - (t0 - 0.12)) / T * 100)
    css = (f'@keyframes pr{{from{{clip-path:inset({g(ink_bot)}px 0 0 0)}}to{{clip-path:inset({g(ink_top)}px 0 0 0)}}}}'
           f'.xq-go #six{{animation:pr {g(dur)}s linear {n(t0)}s both}}'
           f'@keyframes nz{{0%{{opacity:0;transform:translate(0,{g(travel)}px)}}{pc(t0)}%{{opacity:1;transform:translate(0,{g(travel)}px)}}'
           f'{pc(t0 + dur)}%{{opacity:1;transform:translate(0,0)}}100%{{opacity:0;transform:translate(0,-24px)}}}}'
           f'.xq-go #nz{{animation:nz {g(T)}s linear {n(t0 - 0.12)}s both}}'
           f'@keyframes bx{{from{{transform:translateX(-{amp}px)}}to{{transform:translateX({amp}px)}}}}'
           f'.xq-go #nx{{animation:bx {n(dur / 5)}s ease-in-out {n(t0)}s 5 alternate both}}')
    nozzle = (f'<svg width="{nw}" height="{nh}" viewBox="0 0 64 78">'
              f'<path d="M32 1v17" stroke="{BLUE}" stroke-width="5" stroke-linecap="round"/>'
              f'<rect x="12" y="18" width="40" height="32" rx="6" fill="{WHITE}" stroke="{DARK}" stroke-width="3"/>'
              f'<path d="M20 29h24M20 38h24" stroke="{DARK}" stroke-width="2.2" stroke-linecap="round"/>'
              f'<rect x="21" y="50" width="22" height="9" rx="2" fill="{BLUE}"/>'
              f'<path d="M23 59h18l-9 15z" fill="{PINK}"/></svg>')
    body = (f'<div id="six" style="left:{g(sx)}px;top:{g(sy)}px;width:{sw}px;height:{sh}px;clip-path:inset({g(ink_bot)}px 0 0 0)">'
            f'{six_svg}</div>'
            f'<div id="nz" style="left:{g(sx + sw / 2 - tip_x)}px;top:{g(sy + ink_top - tip_y)}px;width:{nw}px;height:{nh}px;opacity:0">'
            f'<div id="nx" style="width:{nw}px;height:{nh}px">{nozzle}</div></div>')
    return page(W, H, css, body), (W, H, sx, sy)


# ================================================================ 3. la maquette qui se dessine au trait
def maquette_embed(t0):
    """Même dessin que maquette3, en tracés compacts ; les traits se dessinent l'un après l'autre,
    les aplats de chaque objet apparaissent quand ses traits sont finis."""
    import maquette3 as M
    objs = M.scene()
    order = sorted(range(len(objs)), key=lambda k: M.DRAW_ORDER.index(objs[k].name))
    timing, obj_end, t = {}, {}, t0
    for k in order:
        for j, (_, pts, _) in enumerate(objs[k].strokes):
            du = max(0.36, min(1.1, M.plen(pts) / 2600.0))
            timing[(k, j)] = (t, du)
            t += du * (1 - 0.77)
        obj_end[k] = t
    end = t
    pts = [M.P(x, y, z) for x in (0, M.W) for y in (0, M.D) for z in (-M.SLAB, M.WALL_H + 40)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, miny = min(xs) - 8, min(ys) - 8
    w, h = round(max(xs) + 8 - minx), round(max(ys) + 8 - miny)
    K = 2
    idx = {id(ob): k for k, ob in enumerate(objs)}
    anim, static = [], []
    for ob in M.paint_order(objs):
        k = idx[id(ob)]
        fills = ''.join(f'<path d="{enc([p], K)}" fill="{c}"/>' for c, p in ob.fills) + ''.join(scale_flat(f, K) for f in ob.flat)
        anim.append(f'<g data-t="{n(obj_end[k] + 0.05)}">{fills}</g>')
        static.append(fills)
        for j, (col, p, sw) in enumerate(ob.strokes):
            st, du = timing[(k, j)]
            d = enc([p], K, closed=False)
            anim.append(f'<path d="{d}" stroke="{col}" stroke-width="{g(sw * K)}" data-t="{n(st)} {n(du)}"/>')
            static.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{g(sw * K)}" '
                          'stroke-linecap="round" stroke-linejoin="round"/>')
    vb = f'{g(minx * K)} {g(miny * K)} {g(w * K)} {g(h * K)}'
    label = ('Maquette de l’atelier : imprimantes 3D, fraiseuse CNC, traceur vinyle, studio vidéo, '
             'imprimante UV et découpeuse laser')
    static_svg = (f'<svg width="{w}" height="{h}" viewBox="{vb}" aria-label="{label}" xmlns="http://www.w3.org/2000/svg" '
                  f'style="display:block">{"".join(static)}</svg>')
    css = 'path[data-t]{fill:none;stroke-linecap:round;stroke-linejoin:round}'
    svg = f'<svg width="{w}" height="{h}" viewBox="{vb}">{"".join(anim)}</svg>'
    play = ('[].forEach.call(d.querySelectorAll("[data-t]"),function(e){var t=e.getAttribute("data-t").split(" ");'
            'if(t[1]){var L=e.getTotalLength();e.style.strokeDasharray=L+" "+(L+4);'
            'A.push(e.animate([{strokeDashoffset:L},{strokeDashoffset:0}],{duration:t[1]*1e3,delay:t[0]*1e3,fill:"both"}))}'
            'else A.push(e.animate([{opacity:0},{opacity:1}],{duration:450,delay:t[0]*1e3,fill:"both"}))});')
    return page(w, h, css, svg, play), static_svg, (w, h), end


def scale_flat(s, K):
    """Éléments « flat » de maquette3 (déjà en SVG) : on les met à l'échelle des tracés compacts."""
    def sc(m):
        return f'{m.group(1)}="{g(float(m.group(2)) * K)}"'
    s = re.sub(r'\b(x|y|width|height|rx|ry|cx|cy|r|x1|y1|x2|y2|stroke-width)="(-?[\d.]+)"', sc, s)

    def scd(m):
        nums = re.findall(r'-?\d+\.?\d*', m.group(1))
        out = m.group(1)
        return 'd="' + re.sub(r'-?\d+\.?\d*', lambda n: g(float(n.group(0)) * K), out) + '"'
    s = re.sub(r'd="([^"]*)"', scd, s)
    s = re.sub(r'points="([^"]*)"', lambda m: 'points="' + re.sub(r'-?\d+\.?\d*', lambda n: g(float(n.group(0)) * K), m.group(1)) + '"', s)
    return s


def x_embed(cls, x, y, w, h, html):
    n = len(html.encode('utf-8'))
    assert n <= LIMIT, f'page intégrée trop lourde : {n} octets'
    return (f'<x-embed class="{cls}" style="position:absolute; left:{g(x)}px; top:{g(y)}px; width:{g(w)}px; '
            f'height:{g(h)}px">{html}</x-embed>')


if __name__ == '__main__':
    h = intro_embed()
    print('intro', len(h.encode()))
    open('/tmp/intro_embed.html', 'w').write(h)
