"""Maquette isométrique de l'atelier, dessinée au trait (style de la présentation).

Chaque objet a ses faces (aplats) et un tracé continu de ses arêtes visibles.
Les tracés se dessinent les uns après les autres (stroke-dashoffset), puis les aplats
de l'objet apparaissent et masquent les traits qui sont derrière. Pas de personnage.
L'état sans animation (éditeur, PDF, PowerPoint) montre la maquette terminée.
"""
import math

DARK, BLUE, VIOLET = '#2f3a48', '#5b60a8', '#8c4292'
BG = '#f4f5f7'
TOP, FRONT, SIDE = '#FFFFFF', '#EEF0F3', '#E1E4EA'
C30 = math.cos(math.radians(30))
K = 0.92
SW = 2.4


def P(x, y, z=0.0):
    return ((x - y) * C30 * K, ((x + y) * 0.5 - z) * K)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def plen(pts):
    return sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def pd(pts, close=False):
    return 'M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in pts) + ('Z' if close else '')


class Obj:
    """Un objet = des faces (aplats) + des tracés (polylignes continues)."""
    def __init__(self, name, bbox):
        self.name = name
        self.b = bbox                 # boîte englobante 3D, pour l'ordre de peinture
        self.fills = []               # (couleur, points écran)
        self.strokes = []             # (couleur, points écran, épaisseur)
        self.flat = []                # éléments qui apparaissent en fondu avec les aplats

    def box(self, x, y, z, w, d, h, top=TOP, front=FRONT, side=SIDE, color=DARK):
        x0, y0, z0, x1, y1, z1 = x, y, z, x + w, y + d, z + h
        self.fills += [(front, [P(x0, y1, z1), P(x1, y1, z1), P(x1, y1, z0), P(x0, y1, z0)]),
                       (side, [P(x1, y0, z1), P(x1, y1, z1), P(x1, y1, z0), P(x1, y0, z0)]),
                       (top, [P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)])]
        A, B, C, D = P(x0, y1, z1), P(x1, y0, z1), P(x1, y1, z1), P(x1, y1, z0)
        hexa = [A, P(x0, y0, z1), B, P(x1, y0, z0), D, P(x0, y1, z0), A]
        self.strokes.append((color, hexa + [C, D, C, B], SW))
        return self

    def line(self, pts3, color=DARK, sw=SW):
        self.strokes.append((color, [P(*p) for p in pts3], sw))
        return self

    def face_rect(self, plane, a0, a1, b0, b1, c, color=DARK, sw=SW * 0.8, fill=None):
        """Rectangle dessiné sur une face : plane 'y' (face avant, y=c), 'x' (face droite, x=c) ou 'z' (dessus, z=c)."""
        if plane == 'y':
            q = [(a0, c, b1), (a1, c, b1), (a1, c, b0), (a0, c, b0), (a0, c, b1)]
        elif plane == 'x':
            q = [(c, a0, b1), (c, a1, b1), (c, a1, b0), (c, a0, b0), (c, a0, b1)]
        else:
            q = [(a0, b0, c), (a1, b0, c), (a1, b1, c), (a0, b1, c), (a0, b0, c)]
        pts = [P(*p) for p in q]
        if fill:
            self.fills.append((fill, pts[:-1]))
        self.strokes.append((color, pts, sw))
        return self


def behind(a, b):
    ax0, ay0, az0, ax1, ay1, az1 = a
    bx0, by0, bz0, bx1, by1, bz1 = b
    return ((ax1 <= bx0 + 1e-6) or (ay1 <= by0 + 1e-6) or (az1 <= bz0 + 1e-6)) and not (
        (bx1 <= ax0 + 1e-6) or (by1 <= ay0 + 1e-6) or (bz1 <= az0 + 1e-6))


def paint_order(objs):
    n = len(objs)
    deps = [set(i for i in range(n) if i != j and behind(objs[i].b, objs[j].b)) for j in range(n)]
    done, out = set(), []
    rest = sorted(range(n), key=lambda k: (objs[k].b[0] + objs[k].b[1], objs[k].b[2]))
    while rest:
        k = next((k for k in rest if deps[k] <= done), rest[0])
        out.append(objs[k]); done.add(k); rest.remove(k)
    return out


def ellipse_x(cx, cy, cz, r, n=40, turns=1.0, r_end=None):
    """Cercle (ou spirale) dessiné sur un plan x = cx (mur gauche)."""
    pts = []
    m = int(n * turns)
    for i in range(m + 1):
        t = 2 * math.pi * i / n
        rr = r if r_end is None else r + (r_end - r) * i / m
        pts.append((cx, cy + rr * math.cos(t), cz + rr * math.sin(t)))
    return pts


def ellipse_z(cx, cy, cz, r, n=36):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), cz) for i in range(n + 1)]


# ---------------------------------------------------------------- l'atelier
W, D = 520, 360
SLAB, WALL_H, WALL_T = 26, 46, 8


def scene():
    objs = []
    # socle : sol et tranche à couches bleues
    floor = Obj('sol', (0, 0, -SLAB, W, D, 0))
    floor.box(0, 0, -SLAB, W, D, SLAB)
    zig = []
    for k, z in enumerate((-5.5, -10.5, -15.5, -20.5)):
        a, b, c = (2, D, z), (W, D, z), (W, 2, z)
        zig += [a, b, c] if k % 2 == 0 else [c, b, a]
    floor.line(zig, BLUE, 1.8)
    # allée au sol (pointillés bleus, en fondu)
    for a, b in (((40, 196, 0), (486, 196, 0)), ((222, 196, 0), (222, 346, 0))):
        pa, pb = P(*a), P(*b)
        floor.flat.append(f'<path d="M{pa[0]:.1f} {pa[1]:.1f}L{pb[0]:.1f} {pb[1]:.1f}" stroke="{BLUE}" stroke-width="2.2" '
                          'stroke-dasharray="7 8" stroke-linecap="round" fill="none"/>')
    objs.append(floor)
    # murs du fond et bobines de filament
    wb = Obj('mur du fond', (0, 0, 0, W, WALL_T, WALL_H)); wb.box(0, 0, 0, W, WALL_T, WALL_H); objs.append(wb)
    wl = Obj('mur gauche', (0, WALL_T, 0, WALL_T, D, WALL_H)); wl.box(0, WALL_T, 0, WALL_T, D - WALL_T, WALL_H)
    for cy in (84, 122, 160):
        wl.line(ellipse_x(WALL_T, cy, 22, 16), DARK, SW * 0.8)
        wl.line(ellipse_x(WALL_T, cy, 22, 13, n=24, turns=3.2, r_end=5.5), BLUE, 1.7)
    objs.append(wl)
    # imprimantes 3D sur un établi
    bench = Obj('établi', (22, 16, 0, 186, 60, 20)); bench.box(22, 16, 0, 164, 44, 20); objs.append(bench)
    for i in range(3):
        x = 30 + i * 52
        pr = Obj(f'imprimante {i + 1}', (x, 20, 20, x + 42, 56, 66))
        pr.box(x, 20, 20, 42, 36, 46)
        pr.face_rect('y', x + 7, x + 35, 27, 57, 56, fill=BG)
        zig = []
        for k in range(4 if i == 1 else 3):
            z = 30 + k * 3.4
            zig += [(x + 13, 56, z), (x + 29, 56, z)] if k % 2 == 0 else [(x + 29, 56, z), (x + 13, 56, z)]
        pr.line(zig, BLUE, 2.2)
        objs.append(pr)
    # fraiseuse CNC (table, portique, broche)
    cnc_t = Obj('table CNC', (232, 24, 0, 372, 112, 24)); cnc_t.box(232, 24, 0, 140, 88, 24); objs.append(cnc_t)
    for x in (246, 352):
        up = Obj('montant', (x, 62, 24, x + 8, 72, 66)); up.box(x, 62, 24, 8, 10, 42); objs.append(up)
    br = Obj('pont', (246, 62, 66, 360, 72, 76)); br.box(246, 62, 66, 114, 10, 10); objs.append(br)
    sp = Obj('broche', (300, 72, 40, 314, 84, 74)); sp.box(300, 72, 40, 14, 12, 34)
    sp.line([(307, 78, 40), (307, 78, 30)], DARK, SW)
    objs.append(sp)
    # traceur vinyle sur pied
    for x in (412, 488):
        lg = Obj('pied', (x, 30, 0, x + 6, 36, 30)); lg.box(x, 30, 0, 6, 6, 30); objs.append(lg)
    pl = Obj('traceur', (400, 24, 30, 504, 50, 52)); pl.box(400, 24, 30, 104, 26, 22)
    pl.face_rect('y', 412, 492, 36, 44, 50)
    pl.face_rect('z', 410, 494, 30, 40, 52, VIOLET, 2)
    objs.append(pl)
    # studio vidéo : fond déroulant, caméra sur trépied, lumière
    bd = Obj('fond', (26, 214, 0, 32, 330, 74)); bd.box(26, 214, 0, 6, 116, 64)
    bd.line([(32, 214, 70), (32, 330, 70)], DARK, SW)
    objs.append(bd)
    roll = Obj('rouleau', (24, 210, 64, 34, 334, 74)); roll.box(24, 210, 64, 10, 124, 10); objs.append(roll)
    tri = Obj('trépied', (112, 262, 0, 136, 286, 44))
    c = (124, 274)
    tri.line([(c[0] - 12, c[1] - 7, 0), (c[0], c[1], 40), (c[0] + 12, c[1] - 7, 0), (c[0], c[1], 40), (c[0], c[1] + 13, 0)], DARK, 2.2)
    objs.append(tri)
    cam = Obj('caméra', (112, 266, 40, 138, 284, 56)); cam.box(112, 266, 40, 26, 18, 16)
    cam.face_rect('x', 270, 280, 44, 52, 138, VIOLET, 2.2)
    objs.append(cam)
    li = Obj('lumière', (66, 312, 0, 92, 324, 86))
    li.line([(78, 318, 0), (78, 318, 62)], DARK, 2.2)
    li.box(66, 312, 62, 26, 8, 24)
    li.face_rect('y', 70, 88, 66, 82, 320, VIOLET, 2)
    objs.append(li)
    # imprimante UV à plat
    uv = Obj('imprimante UV', (250, 232, 0, 340, 284, 30)); uv.box(250, 232, 0, 90, 52, 30)
    uv.face_rect('z', 262, 328, 242, 274, 30, VIOLET, 2)
    objs.append(uv)
    ga = Obj('portique UV', (258, 252, 30, 332, 260, 40)); ga.box(258, 252, 30, 74, 8, 10); objs.append(ga)
    # découpeuse laser
    lz = Obj('découpeuse laser', (356, 226, 0, 508, 304, 38)); lz.box(356, 226, 0, 152, 78, 38)
    lz.face_rect('z', 368, 470, 236, 294, 38, DARK, SW * 0.8, fill=BG)
    lz.line(ellipse_z(418, 265, 38, 18), VIOLET, 2.6)
    lz.face_rect('z', 482, 496, 240, 254, 38, DARK, 2, fill=DARK)
    objs.append(lz)
    return objs


# ---------------------------------------------------------------- rendu et minutage du tracé
DRAW_ORDER = ['sol', 'mur du fond', 'mur gauche', 'établi', 'imprimante 1', 'imprimante 2', 'imprimante 3',
              'table CNC', 'montant', 'pont', 'broche', 'pied', 'traceur', 'fond', 'rouleau', 'lumière',
              'trépied', 'caméra', 'imprimante UV', 'portique UV', 'découpeuse laser']


def render(t0=7.6, speed=2600.0, overlap=0.77, min_dur=0.36):
    objs = scene()
    # minutage : les tracés s'enchaînent dans l'ordre du dessin, à vitesse à peu près constante
    timing = {}
    t = t0
    order = sorted(range(len(objs)), key=lambda k: DRAW_ORDER.index(objs[k].name))
    obj_end = {}
    for k in order:
        o = objs[k]
        for j, (_, pts, _) in enumerate(o.strokes):
            L = plen(pts)
            dur = max(min_dur, min(1.1, L / speed))
            timing[(k, j)] = (t, dur, L)
            t += dur * (1 - overlap)
        obj_end[k] = t
    total_end = t
    # cadre
    pts = [P(x, y, z) for x in (0, W) for y in (0, D) for z in (-SLAB, WALL_H + 40)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    pad = 8
    minx, maxx, miny, maxy = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    w, h = round(maxx - minx), round(maxy - miny)
    out = []
    idx = {id(o): k for k, o in enumerate(objs)}
    for o in paint_order(objs):
        k = idx[id(o)]
        fd = obj_end[k] + 0.05
        fills = ''.join(f'<path d="{pd(p, True)}" fill="{c}"/>' for c, p in o.fills) + ''.join(o.flat)
        T = fd + 0.45
        out.append(f'<g><animate attributeName="opacity" values="0;0;1" keyTimes="0;{fd / T:.4f};1" dur="{T:.3f}s" begin="0s"/>'
                   f'{fills}</g>')
        for j, (col, p, sw) in enumerate(o.strokes):
            st, du, L = timing[(k, j)]
            T = st + du
            out.append(f'<path d="{pd(p)}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" '
                       f'stroke-linejoin="round" stroke-dasharray="{L:.1f} {L + 2:.1f}">'
                       f'<animate attributeName="stroke-dashoffset" values="{L:.1f};{L:.1f};0" keyTimes="0;{st / T:.4f};1" '
                       f'dur="{T:.3f}s" begin="0s"/></path>')
    body = ''.join(out)
    svg = (f'<svg width="{w}" height="{h}" viewBox="{minx:.1f} {miny:.1f} {w} {h}" '
           'aria-label="Maquette de l’atelier : imprimantes 3D, fraiseuse CNC, traceur vinyle, studio vidéo, '
           'imprimante UV et découpeuse laser" xmlns="http://www.w3.org/2000/svg" style="display:block">'
           f'{body}</svg>')
    return svg, (w, h), total_end


CSS = ['.cvMq { animation: fade 0.3s linear 7.75s both; }']


if __name__ == '__main__':
    svg, size, end = render()
    open('/tmp/maquette3.svg', 'w').write(svg)
    print(size, len(svg), 'fin du tracé', round(end, 2))
