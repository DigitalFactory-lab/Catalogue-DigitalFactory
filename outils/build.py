#!/usr/bin/env python3
"""Génère les diapositives du deck « Les types d'ateliers de la Digital Factory »."""
import re
import json, os, datetime
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

ROOT = os.environ.get('DECK_PROJECT', '/home/claude/deck/project')   # dossier « project » de la présentation
NB = ' '   # espace insécable
AP = '’'   # apostrophe typographique

DARK, BLUE, VIOLET = '#2f3a48', '#5b60a8', '#8c4292'
PINK = '#F0268B'   # couleur « peps » : quelques détails en action (faisceau laser, point laser, étincelle IA, voyant REC)
BG, LINE, MUTED = '#f4f5f7', '#e0e0e0', '#5f6673'
N_SLIDES = 10
PX_PER_STEP = 1920 // N_SLIDES

def q(s):
    return s.replace("'", AP)

# ---------------------------------------------------------------- commun
def prog(i):
    return f'<div class="prog"><div class="progfill" style="width:{i * PX_PER_STEP}px"></div></div>'

def bignum(nn):
    return f'<p class="bignum f" style="--i:1">{nn}</p>'

def head(kicker, name, promise):
    return (
        '<div class="head">'
        f'<div class="kick a" style="--i:0"><div class="sq"></div><p class="kicker">{q(kicker)}</p></div>'
        f'<h2 class="title a" style="--i:1">{q(name)}<br><span class="hl">{q(promise)}</span></h2>'
        '</div>'
    )

def duration(value, lo, hi, sub=None, public=()):
    """Bloc durée : grand chiffre + règle 0-40 h (plein jusqu'à lo, hachuré jusqu'à hi)."""
    W = 760
    k = W / 40
    solid = round(lo * k)
    hatch = round((hi - lo) * k)
    fill = f'<div class="solid" style="width:{solid}px"></div>'
    if hatch:
        fill += f'<div class="hatch" style="width:{hatch}px"></div>'
    ticks = ''
    for h in (0, 8, 16, 24, 32, 40):
        x = round(h * k)
        label = '0' if h == 0 else f'{h}{NB}h'
        if h == 0:
            ticks += f'<p class="tick" style="left:0px">{label}</p>'
        elif h == 40:
            ticks += f'<p class="tick" style="left:{x - 120}px; text-align:right">{label}</p>'
        else:
            ticks += f'<p class="tick" style="left:{x - 60}px; text-align:center">{label}</p>'
    subhtml = f'<p class="dursub">{q(sub)}</p>' if sub else ''
    return (
        '<div class="dblock a" style="--i:4">'
        '<div class="fiche">'
        f'<div class="fdur"><p class="dlabel">Durée de référence</p><p class="dur">{value}</p>{subhtml}</div>'
        '<div class="fpub"><p class="plabel">Public cible</p><ul class="publ">'
        + ''.join(f'<li><span>{q(x)}</span></li>' for x in public) +
        '</ul></div>'
        '</div>'
        f'<div class="track"><div class="grow" style="width:{solid + hatch}px"><div class="fill" style="width:{solid + hatch}px">{fill}</div></div></div>'
        f'<div class="ticks">{ticks}</div>'
        '</div>'
    )

def svg(w, h, label, inner, style=''):
    st = f' style="display:block; {style}"' if style else ' style="display:block"'
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-label="{q(label)}" '
            f'xmlns="http://www.w3.org/2000/svg"{st}>{inner}</svg>')

def pin(x, y, w, h, inner, cls='', i=None, extra=''):
    c = f' class="{cls}"' if cls else ''
    iv = f' --i:{i};' if i is not None else ''
    hh = f' height:{h}px;' if h else ''
    return f'<div{c} style="position:absolute; left:{x}px; top:{y}px; width:{w}px;{hh}{iv}{extra}">{inner}</div>'

S = f'stroke="{DARK}" stroke-linecap="round" stroke-linejoin="round"'

# ---------------------------------------------------------------- dessins
def d_printer():
    """Imprimante 3D fermée, vue de face (200 x 220)."""
    lines = ''.join(
        f'<line x1="72" y1="{y}" x2="128" y2="{y}" stroke="{BG}" stroke-width="1.6"/>'
        for y in range(125, 168, 7))
    return svg(200, 220, 'Imprimante 3D', (
        f'<rect x="2" y="2" width="196" height="216" rx="12" fill="#ffffff" {S} stroke-width="3"/>'
        f'<rect x="20" y="20" width="160" height="160" rx="6" fill="{BG}" {S} stroke-width="2"/>'
        f'<line x1="20" y1="56" x2="180" y2="56" {S} stroke-width="2"/>'
        f'<rect x="86" y="46" width="28" height="30" rx="4" fill="#ffffff" {S} stroke-width="2.5"/>'
        f'<path d="M93 76 L107 76 L100 88 Z" fill="{DARK}"/>'
        f'<rect x="72" y="118" width="56" height="50" fill="{BLUE}"/>{lines}'
        f'<rect x="40" y="168" width="120" height="8" rx="2" fill="{DARK}"/>'
        f'<line x1="20" y1="198" x2="180" y2="198" {S} stroke-width="2"/>'
        f'<circle cx="166" cy="198" r="5" fill="{VIOLET}"/>'))

def d_laser():
    """Découpeuse laser, vue de face (260 x 150)."""
    return svg(260, 150, 'Découpeuse laser', (
        f'<path d="M14 44 L36 4 L224 4 L246 44 Z" fill="{BG}" {S} stroke-width="3"/>'
        f'<path d="M58 14 L202 14 L214 36 L46 36 Z" fill="#ffffff" {S} stroke-width="2"/>'
        f'<rect x="2" y="44" width="256" height="104" rx="10" fill="#ffffff" {S} stroke-width="3"/>'
        f'<rect x="24" y="58" width="212" height="56" rx="4" fill="{BG}" {S} stroke-width="2"/>'
        f'<rect x="116" y="62" width="28" height="18" rx="3" fill="#ffffff" {S} stroke-width="2"/>'
        f'<line x1="130" y1="80" x2="130" y2="100" stroke="{PINK}" stroke-width="3" stroke-linecap="round"/>'
        f'<circle cx="130" cy="103" r="4" fill="{PINK}"/>'
        f'<rect x="40" y="104" width="180" height="6" fill="{BLUE}"/>'
        f'<line x1="24" y1="130" x2="236" y2="130" {S} stroke-width="2"/>'))

def d_uv():
    """Imprimante UV à plat, vue de face (220 x 120)."""
    return svg(220, 120, 'Imprimante UV à plat', (
        f'<rect x="2" y="40" width="216" height="78" rx="10" fill="#ffffff" {S} stroke-width="3"/>'
        f'<rect x="12" y="8" width="196" height="24" rx="5" fill="{BG}" {S} stroke-width="2.5"/>'
        f'<line x1="40" y1="32" x2="40" y2="40" {S} stroke-width="2.5"/>'
        f'<line x1="180" y1="32" x2="180" y2="40" {S} stroke-width="2.5"/>'
        f'<rect x="96" y="30" width="36" height="16" rx="3" fill="#ffffff" {S} stroke-width="2"/>'
        f'<rect x="64" y="54" width="92" height="14" fill="{VIOLET}"/>'
        f'<rect x="64" y="54" width="46" height="14" fill="{BLUE}"/>'
        f'<line x1="24" y1="96" x2="196" y2="96" {S} stroke-width="2"/>'))

def d_route():
    """Sol + parcours de visite en pointillés (824 x 130)."""
    return svg(824, 130, 'Parcours de visite devant les machines', (
        f'<line x1="0" y1="10" x2="824" y2="10" stroke="{LINE}" stroke-width="3"/>'
        f'<path d="M24 74 C 120 40, 200 108, 300 74 S 480 40, 580 74 S 720 108, 784 74" fill="none" '
        f'stroke="{BLUE}" stroke-width="4" stroke-dasharray="12 10" stroke-linecap="round"/>'
        f'<path d="M776 62 L800 74 L776 86" fill="none" stroke="{BLUE}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="24" cy="74" r="12" fill="{VIOLET}"/>'
        f'<circle cx="120" cy="60" r="7" fill="#ffffff" stroke="{BLUE}" stroke-width="3"/>'
        f'<circle cx="420" cy="58" r="7" fill="#ffffff" stroke="{BLUE}" stroke-width="3"/>'
        f'<circle cx="712" cy="90" r="7" fill="#ffffff" stroke="{BLUE}" stroke-width="3"/>'))

def d_fdm():
    """Principe de l'impression 3D : buse et couches (316 x 200)."""
    layers = ''.join(f'<rect x="40" y="{y}" width="236" height="7" fill="{BLUE}"/>' for y in (160, 168, 176))
    return svg(316, 200, 'Buse d’impression 3D déposant des couches', (
        f'<line x1="158" y1="0" x2="158" y2="22" stroke="{BLUE}" stroke-width="6" stroke-linecap="round"/>'
        f'<rect x="132" y="22" width="52" height="44" rx="6" fill="#ffffff" {S} stroke-width="3"/>'
        f'<line x1="140" y1="36" x2="176" y2="36" {S} stroke-width="2"/>'
        f'<line x1="140" y1="46" x2="176" y2="46" {S} stroke-width="2"/>'
        f'<path d="M146 66 L170 66 L158 86 Z" fill="{DARK}"/>'
        f'{layers}'
        f'<rect x="40" y="152" width="118" height="7" fill="{VIOLET}"/>'
        f'<line x1="158" y1="90" x2="158" y2="148" stroke="{VIOLET}" stroke-width="2" stroke-dasharray="4 5"/>'
        f'<rect x="22" y="184" width="272" height="10" rx="3" fill="{DARK}"/>'))

def d_cut():
    """Découpe laser vue de dessus (316 x 200)."""
    return svg(316, 200, 'Tête laser découpant une forme dans une plaque', (
        f'<rect x="28" y="74" width="260" height="122" rx="6" fill="{BG}" {S} stroke-width="2.5"/>'
        f'<path d="M158 92 A42 42 0 1 1 116 134" fill="none" stroke="{VIOLET}" stroke-width="4" stroke-linecap="round"/>'
        f'<path d="M116 134 A42 42 0 0 1 158 92" fill="none" stroke="{MUTED}" stroke-width="3" stroke-dasharray="6 7" stroke-linecap="round"/>'
        f'<rect x="138" y="8" width="40" height="38" rx="6" fill="#ffffff" {S} stroke-width="3"/>'
        f'<line x1="146" y1="20" x2="170" y2="20" {S} stroke-width="2"/>'
        f'<line x1="158" y1="46" x2="158" y2="86" stroke="{VIOLET}" stroke-width="3" stroke-linecap="round"/>'
        f'<circle cx="158" cy="92" r="7" fill="{VIOLET}"/>'))

def d_blueprint():
    """Feuille de conception avec cotes (150 x 150)."""
    return svg(150, 150, 'Plan de conception d’un objet', (
        f'<path d="M14 4 L112 4 L138 30 L138 146 L14 146 Z" fill="#ffffff" {S} stroke-width="3"/>'
        f'<path d="M112 4 L112 30 L138 30" fill="none" {S} stroke-width="2.5"/>'
        f'<rect x="40" y="56" width="62" height="50" fill="none" stroke="{BLUE}" stroke-width="3"/>'
        f'<line x1="40" y1="120" x2="102" y2="120" {S} stroke-width="2"/>'
        f'<line x1="40" y1="114" x2="40" y2="126" {S} stroke-width="2"/>'
        f'<line x1="102" y1="114" x2="102" y2="126" {S} stroke-width="2"/>'
        f'<line x1="116" y1="56" x2="116" y2="106" {S} stroke-width="2"/>'
        f'<line x1="110" y1="56" x2="122" y2="56" {S} stroke-width="2"/>'
        f'<line x1="110" y1="106" x2="122" y2="106" {S} stroke-width="2"/>'
        f'<circle cx="71" cy="81" r="9" fill="{VIOLET}"/>'))

def d_present():
    """Écran de présentation sur pied (150 x 150)."""
    return svg(150, 150, 'Écran de présentation', (
        f'<rect x="6" y="6" width="138" height="92" rx="8" fill="#ffffff" {S} stroke-width="3"/>'
        f'<rect x="28" y="58" width="16" height="26" fill="{BLUE}"/>'
        f'<rect x="54" y="44" width="16" height="40" fill="{BLUE}"/>'
        f'<rect x="80" y="30" width="16" height="54" fill="{VIOLET}"/>'
        f'<line x1="106" y1="84" x2="124" y2="84" {S} stroke-width="2"/>'
        f'<line x1="75" y1="98" x2="75" y2="142" {S} stroke-width="3"/>'
        f'<line x1="75" y1="118" x2="44" y2="146" {S} stroke-width="3"/>'
        f'<line x1="75" y1="118" x2="106" y2="146" {S} stroke-width="3"/>'))

def d_link():
    """Ligne de progression entre conception et présentation (440 x 40)."""
    return svg(440, 40, 'Progression du projet', (
        f'<line x1="6" y1="20" x2="420" y2="20" stroke="{BLUE}" stroke-width="4" stroke-linecap="round"/>'
        f'<path d="M410 8 L432 20 L410 32" fill="none" stroke="{BLUE}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="110" cy="20" r="8" fill="#ffffff" stroke="{BLUE}" stroke-width="3"/>'
        f'<circle cx="214" cy="20" r="8" fill="#ffffff" stroke="{BLUE}" stroke-width="3"/>'
        f'<circle cx="318" cy="20" r="8" fill="#ffffff" stroke="{BLUE}" stroke-width="3"/>'))

def d_printer_small():
    return svg(84, 92, 'Imprimante 3D', (
        f'<rect x="2" y="2" width="80" height="88" rx="8" fill="#ffffff" {S} stroke-width="3"/>'
        f'<rect x="11" y="11" width="62" height="62" rx="4" fill="{BG}" {S} stroke-width="2"/>'
        f'<line x1="11" y1="26" x2="73" y2="26" {S} stroke-width="2"/>'
        f'<rect x="35" y="21" width="14" height="13" rx="2" fill="#ffffff" {S} stroke-width="2"/>'
        f'<rect x="30" y="48" width="24" height="20" fill="{BLUE}"/>'
        f'<rect x="20" y="67" width="44" height="4" fill="{DARK}"/>'))

def d_wrench():
    return svg(92, 92, 'Clé, symbole du métier', (
        f'<path d="M62 8 A22 22 0 0 0 40 36 L10 66 A9 9 0 0 0 26 82 L56 52 A22 22 0 0 0 84 30 L72 42 L58 38 L54 24 L66 12 Z" '
        f'fill="#ffffff" {S} stroke-width="3.5"/>'
        f'<circle cx="19" cy="73" r="4" fill="{VIOLET}"/>'))

def d_merge():
    return svg(824, 94, 'Les deux apports convergent vers les stagiaires', (
        f'<path d="M180 2 L180 24 L412 84" fill="none" stroke="{BLUE}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M644 2 L644 24 L412 84" fill="none" stroke="{BLUE}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="412" cy="85" r="8" fill="{VIOLET}"/>'))

def d_lock():
    return svg(110, 110, 'Cadenas', (
        f'<path d="M32 50 L32 34 A23 23 0 0 1 78 34 L78 50" fill="none" {S} stroke-width="5"/>'
        f'<rect x="18" y="50" width="74" height="56" rx="9" fill="#ffffff" {S} stroke-width="4"/>'
        f'<circle cx="55" cy="72" r="8" fill="{VIOLET}"/>'
        f'<line x1="55" y1="78" x2="55" y2="92" stroke="{VIOLET}" stroke-width="6" stroke-linecap="round"/>'))

def d_chip():
    pins = ''
    for k in (34, 55, 76):
        pins += (f'<line x1="{k}" y1="8" x2="{k}" y2="22" {S} stroke-width="3.5"/>'
                 f'<line x1="{k}" y1="88" x2="{k}" y2="102" {S} stroke-width="3.5"/>'
                 f'<line x1="8" y1="{k}" x2="22" y2="{k}" {S} stroke-width="3.5"/>'
                 f'<line x1="88" y1="{k}" x2="102" y2="{k}" {S} stroke-width="3.5"/>')
    return svg(110, 110, 'Puce d’intelligence artificielle', (
        f'{pins}<rect x="22" y="22" width="66" height="66" rx="9" fill="#ffffff" {S} stroke-width="4"/>'
        f'<path d="M55 36 L60 50 L74 55 L60 60 L55 74 L50 60 L36 55 L50 50 Z" fill="{PINK}"/>'))

def d_levels():
    return svg(46, 36, 'Niveaux variés', (
        f'<rect x="2" y="22" width="10" height="12" rx="2" fill="{BLUE}"/>'
        f'<rect x="18" y="12" width="10" height="22" rx="2" fill="{BLUE}"/>'
        f'<rect x="34" y="2" width="10" height="32" rx="2" fill="{VIOLET}"/>'))

def d_camera():
    """Caméra du studio sur trépied (330 x 270)."""
    return svg(330, 270, 'Caméra du studio de captation vidéo', (
        f'<rect x="40" y="40" width="190" height="112" rx="14" fill="#ffffff" {S} stroke-width="3.5"/>'
        f'<path d="M230 72 L300 46 L300 146 L230 120 Z" fill="{BG}" {S} stroke-width="3.5"/>'
        f'<circle cx="104" cy="96" r="30" fill="{BG}" {S} stroke-width="3"/>'
        f'<circle cx="104" cy="96" r="13" fill="{BLUE}"/>'
        f'<rect x="64" y="20" width="70" height="20" rx="5" fill="#ffffff" {S} stroke-width="3"/>'
        f'<circle cx="202" cy="64" r="9" fill="{VIOLET}"/>'
        f'<line x1="135" y1="152" x2="135" y2="196" {S} stroke-width="4"/>'
        f'<line x1="135" y1="196" x2="76" y2="264" {S} stroke-width="4"/>'
        f'<line x1="135" y1="196" x2="194" y2="264" {S} stroke-width="4"/>'
        f'<line x1="135" y1="196" x2="135" y2="264" {S} stroke-width="4"/>'))

def d_frame():
    """Cadre de prise de vue avec une personne (380 x 260)."""
    c = BLUE
    brackets = (
        f'<path d="M6 46 L6 6 L46 6" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M334 6 L374 6 L374 46" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M6 214 L6 254 L46 254" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M334 254 L374 254 L374 214" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')
    return svg(380, 260, 'Cadre de prise de vue avec une personne face à la caméra', (
        f'{brackets}'
        f'<circle cx="190" cy="104" r="40" fill="#ffffff" {S} stroke-width="3.5"/>'
        f'<path d="M106 254 C 106 190, 150 162, 190 162 C 230 162, 274 190, 274 254" fill="#ffffff" {S} stroke-width="3.5"/>'
        f'<circle cx="34" cy="34" r="9" fill="{VIOLET}"/>'))

# ---------------------------------------------------------------- « 6 » en couches
def glyph_six(height=450, pad=10):
    f = TTFont('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf')
    gs = f.getGlyphSet()
    g = gs['six']
    bp = BoundsPen(gs); g.draw(bp)
    xmin, ymin, xmax, ymax = bp.bounds
    s = height / (ymax - ymin)
    sp = SVGPathPen(gs)
    tp = TransformPen(sp, (s, 0, 0, -s, -xmin * s + pad, ymax * s + pad))
    g.draw(tp)
    w = (xmax - xmin) * s + 2 * pad
    return sp.getCommands(), round(w), height + 2 * pad

def hero_six():
    d, w, h = glyph_six()
    period, bar = 14, 11
    inner = (
        f'<defs><pattern id="cv-layers" x="0" y="{(h - 10) % period}" width="40" height="{period}" patternUnits="userSpaceOnUse">'
        f'<rect x="0" y="0" width="40" height="{bar}" fill="#ffffff"/></pattern></defs>'
        f'<path d="{d}" fill="url(#cv-layers)"/>')
    return svg(w, h, 'Le chiffre 6, imprimé couche par couche', inner), w, h

def d_nozzle():
    return svg(64, 76, 'Buse', (
        '<line x1="32" y1="0" x2="32" y2="18" stroke="#ffffff" stroke-width="5" stroke-linecap="round"/>'
        '<rect x="12" y="18" width="40" height="34" rx="6" fill="#ffffff"/>'
        f'<line x1="18" y1="30" x2="46" y2="30" stroke="{BLUE}" stroke-width="2.5"/>'
        f'<line x1="18" y1="40" x2="46" y2="40" stroke="{BLUE}" stroke-width="2.5"/>'
        '<path d="M22 52 L42 52 L32 70 Z" fill="#ffffff"/>'))

def d_spool():
    c = 270
    parts = [f'<circle cx="{c}" cy="{c}" r="262" fill="none" stroke="#ffffff" stroke-opacity="0.55" stroke-width="3"/>']
    import math
    for k in range(8):
        a = math.radians(k * 45 + 10)
        parts.append(f'<circle cx="{c + 236 * math.cos(a):.1f}" cy="{c + 236 * math.sin(a):.1f}" r="8" fill="none" stroke="#ffffff" stroke-opacity="0.55" stroke-width="2.5"/>')
    for r in range(112, 216, 6):
        parts.append(f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="#ffffff" stroke-width="2.2"/>')
    parts.append(f'<circle cx="{c}" cy="{c}" r="92" fill="none" stroke="#ffffff" stroke-opacity="0.8" stroke-width="3"/>')
    parts.append(f'<circle cx="{c}" cy="{c}" r="34" fill="none" stroke="#ffffff" stroke-width="3"/>')
    for k in range(3):
        a = math.radians(k * 120 - 60)
        parts.append(f'<line x1="{c + 34 * math.cos(a):.1f}" y1="{c + 34 * math.sin(a):.1f}" x2="{c + 84 * math.cos(a):.1f}" y2="{c + 84 * math.sin(a):.1f}" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>')
    return svg(540, 540, 'Bobine de filament', ''.join(parts))


# ---------------------------------------------------------------- pièces animées
def wrap(cls, x, y, w, h, inner, extra=''):
    """Fenêtre de révélation : extérieur (masque) + intérieur (contenu), animés en sens opposés."""
    o, i = cls
    return (f'<div class="{o}" style="position:absolute; left:{x}px; top:{y}px; width:{w}px; height:{h}px; overflow:hidden;{extra}">'
            f'<div class="{i}" style="width:{w}px; height:{h}px">{inner}</div></div>')

def d_printer_body():
    return svg(200, 220, 'Imprimante 3D', (
        f'<rect x="2" y="2" width="196" height="216" rx="12" fill="#ffffff" {S} stroke-width="3"/>'
        f'<rect x="20" y="20" width="160" height="160" rx="6" fill="{BG}" {S} stroke-width="2"/>'
        f'<line x1="20" y1="56" x2="180" y2="56" {S} stroke-width="2"/>'
        f'<rect x="40" y="168" width="120" height="8" rx="2" fill="{DARK}"/>'
        f'<line x1="20" y1="198" x2="180" y2="198" {S} stroke-width="2"/>'
        f'<circle cx="166" cy="198" r="5" fill="{VIOLET}"/>'))

def d_printer_object():
    lines = ''.join(f'<line x1="0" y1="{y}" x2="56" y2="{y}" stroke="{BG}" stroke-width="1.6"/>' for y in range(7, 50, 7))
    return svg(56, 50, 'Pièce imprimée', f'<rect x="0" y="0" width="56" height="50" fill="{BLUE}"/>{lines}')

def d_hotend_small():
    return svg(28, 44, 'Tête d’impression', (
        f'<rect x="1.5" y="1.5" width="25" height="28" rx="4" fill="#ffffff" {S} stroke-width="2.5"/>'
        f'<path d="M7 30 L21 30 L14 42 Z" fill="{DARK}"/>'))

def d_uv_body():
    return svg(220, 120, 'Imprimante UV à plat', (
        f'<rect x="2" y="40" width="216" height="78" rx="10" fill="#ffffff" {S} stroke-width="3"/>'
        f'<rect x="12" y="8" width="196" height="24" rx="5" fill="{BG}" {S} stroke-width="2.5"/>'
        f'<line x1="40" y1="32" x2="40" y2="40" {S} stroke-width="2.5"/>'
        f'<line x1="180" y1="32" x2="180" y2="40" {S} stroke-width="2.5"/>'
        f'<rect x="64" y="54" width="92" height="14" fill="none" stroke="{LINE}" stroke-width="2" stroke-dasharray="4 4"/>'
        f'<line x1="24" y1="96" x2="196" y2="96" {S} stroke-width="2"/>'))

def d_uv_head():
    return svg(36, 16, 'Tête d’impression UV', f'<rect x="1.5" y="1.5" width="33" height="13" rx="3" fill="#ffffff" {S} stroke-width="2"/>'
               f'<rect x="10" y="5" width="6" height="6" fill="{BLUE}"/><rect x="20" y="5" width="6" height="6" fill="{VIOLET}"/>')

def d_uv_tile():
    return svg(92, 14, 'Impression UV', f'<rect x="0" y="0" width="46" height="14" fill="{BLUE}"/><rect x="46" y="0" width="46" height="14" fill="{VIOLET}"/>')

def d_fdm_body():
    layers = ''.join(f'<rect x="40" y="{y}" width="236" height="7" fill="{BLUE}"/>' for y in (160, 168, 176))
    return svg(316, 200, 'Plateau d’impression 3D et premières couches', f'{layers}<rect x="22" y="184" width="272" height="10" rx="3" fill="{DARK}"/>')

def d_hotend_fdm():
    return svg(52, 146, 'Buse d’impression 3D', (
        f'<line x1="26" y1="0" x2="26" y2="18" stroke="{BLUE}" stroke-width="6" stroke-linecap="round"/>'
        f'<rect x="1.5" y="18" width="49" height="44" rx="6" fill="#ffffff" {S} stroke-width="3"/>'
        f'<line x1="9" y1="32" x2="43" y2="32" {S} stroke-width="2"/>'
        f'<line x1="9" y1="42" x2="43" y2="42" {S} stroke-width="2"/>'
        f'<path d="M14 62 L38 62 L26 82 Z" fill="{DARK}"/>'
        f'<line x1="26" y1="86" x2="26" y2="138" stroke="{VIOLET}" stroke-width="2" stroke-dasharray="4 5"/>'))

def d_cut_body():
    import math
    cx, cy, r = 158, 135, 42
    segs = ''
    for k in range(12):
        a0 = math.radians(-90 + 30 * k); a1 = math.radians(-90 + 30 * (k + 1))
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        segs += (f'<path class="seg" style="--i:{k}" d="M{x0:.2f} {y0:.2f} A{r} {r} 0 0 1 {x1:.2f} {y1:.2f}" '
                 f'fill="none" stroke="{VIOLET}" stroke-width="4" stroke-linecap="round"/>')
    return svg(316, 200, 'Plaque découpée au laser selon un cercle', (
        f'<rect x="28" y="64" width="260" height="132" rx="6" fill="{BG}" {S} stroke-width="2.5"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{MUTED}" stroke-width="2" stroke-dasharray="5 7"/>'
        f'{segs}'))

def d_laser_dot():
    return svg(26, 26, 'Tête laser', (
        f'<rect x="1.5" y="1.5" width="23" height="23" rx="6" fill="{DARK}"/>'
        f'<circle cx="13" cy="13" r="5" fill="{PINK}" stroke="#ffffff" stroke-width="2"/>'))

def d_camera_body():
    return svg(330, 270, 'Caméra du studio de captation vidéo', (
        f'<rect x="40" y="40" width="190" height="112" rx="14" fill="#ffffff" {S} stroke-width="3.5"/>'
        f'<path d="M230 72 L300 46 L300 146 L230 120 Z" fill="{BG}" {S} stroke-width="3.5"/>'
        f'<circle cx="104" cy="96" r="30" fill="{BG}" {S} stroke-width="3"/>'
        f'<circle cx="104" cy="96" r="13" fill="{BLUE}"/>'
        f'<rect x="64" y="20" width="70" height="20" rx="5" fill="#ffffff" {S} stroke-width="3"/>'
        f'<line x1="135" y1="152" x2="135" y2="196" {S} stroke-width="4"/>'
        f'<line x1="135" y1="196" x2="76" y2="264" {S} stroke-width="4"/>'
        f'<line x1="135" y1="196" x2="194" y2="264" {S} stroke-width="4"/>'
        f'<line x1="135" y1="196" x2="135" y2="264" {S} stroke-width="4"/>'))

# outils de l'intro (logo fabriqué par les machines)
def t_laser():
    return svg(44, 190, 'Tête laser', (
        f'<rect x="2" y="0" width="40" height="30" rx="7" fill="{DARK}"/>'
        f'<rect x="10" y="10" width="14" height="5" rx="2" fill="{VIOLET}"/>'
        f'<rect x="15" y="30" width="14" height="8" rx="2" fill="#c5cad3"/>'
        f'<line x1="22" y1="38" x2="22" y2="172" stroke="{VIOLET}" stroke-width="3" stroke-linecap="round"/>'
        f'<circle cx="22" cy="130" r="5" fill="#ffffff" stroke="{VIOLET}" stroke-width="2.5"/>'))

def t_nozzle():
    return svg(40, 34, 'Buse d’imprimante 3D', (
        f'<rect x="0" y="0" width="40" height="22" rx="5" fill="{DARK}"/>'
        f'<line x1="16" y1="7" x2="24" y2="15" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>'
        f'<line x1="24" y1="7" x2="16" y2="15" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>'
        f'<path d="M13 22 L27 22 L20 33 Z" fill="{VIOLET}"/>'))

def t_drill():
    zig = ' '.join(f'L{14 + (5 if k % 2 else -5)} {56 + 4 * k}' for k in range(1, 9))
    return svg(28, 92, 'Fraise de CNC', (
        f'<rect x="0" y="0" width="28" height="46" rx="6" fill="{DARK}"/>'
        f'<circle cx="14" cy="12" r="3.5" fill="{VIOLET}"/>'
        f'<rect x="5" y="46" width="18" height="8" rx="2" fill="#c5cad3"/>'
        f'<path d="M14 56 {zig} L14 90" fill="none" stroke="{MUTED}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'))

def t_uvhead():
    return svg(64, 28, 'Tête d’impression UV', (
        f'<rect x="0" y="0" width="64" height="26" rx="6" fill="{DARK}"/>'
        f'<rect x="8" y="7" width="9" height="12" rx="2" fill="{BLUE}"/>'
        f'<rect x="21" y="7" width="9" height="12" rx="2" fill="{VIOLET}"/>'
        f'<rect x="34" y="7" width="9" height="12" rx="2" fill="#c5cad3"/>'
        f'<rect x="47" y="7" width="9" height="12" rx="2" fill="#ffffff"/>'))

def d_nozzle_dark():
    return svg(64, 76, 'Buse', (
        f'<line x1="32" y1="0" x2="32" y2="18" stroke="{BLUE}" stroke-width="5" stroke-linecap="round"/>'
        f'<rect x="12" y="18" width="40" height="34" rx="6" fill="{DARK}"/>'
        f'<line x1="18" y1="30" x2="46" y2="30" stroke="#ffffff" stroke-width="2.5"/>'
        f'<line x1="18" y1="40" x2="46" y2="40" stroke="#ffffff" stroke-width="2.5"/>'
        f'<path d="M22 52 L42 52 L32 70 Z" fill="{VIOLET}"/>'))

def hero_six_light(height=300):
    d, w, h = glyph_six(height=height)
    period, bar = 11, 8.5
    inner = (
        f'<defs><pattern id="cv2-layers" x="0" y="{(h - 10) % period}" width="40" height="{period}" patternUnits="userSpaceOnUse">'
        f'<rect x="0" y="0" width="40" height="{bar}" fill="{BLUE}"/></pattern></defs>'
        f'<path d="{d}" fill="url(#cv2-layers)"/>')
    return svg(w, h, 'Le chiffre 6, imprimé couche par couche', inner), w, h

def d_spool_light():
    import math
    c = 200
    parts = [f'<circle cx="{c}" cy="{c}" r="194" fill="none" stroke="{DARK}" stroke-opacity="0.3" stroke-width="2.5"/>']
    for k in range(8):
        a = math.radians(k * 45 + 10)
        parts.append(f'<circle cx="{c + 175 * math.cos(a):.1f}" cy="{c + 175 * math.sin(a):.1f}" r="6" fill="none" stroke="{DARK}" stroke-opacity="0.3" stroke-width="2"/>')
    for r in range(84, 160, 5):
        parts.append(f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{BLUE}" stroke-width="1.8"/>')
    parts.append(f'<circle cx="{c}" cy="{c}" r="68" fill="#ffffff" stroke="{DARK}" stroke-width="2.5"/>')
    parts.append(f'<circle cx="{c}" cy="{c}" r="26" fill="none" stroke="{DARK}" stroke-width="2.5"/>')
    for k in range(3):
        a = math.radians(k * 120 - 60)
        parts.append(f'<line x1="{c + 26 * math.cos(a):.1f}" y1="{c + 26 * math.sin(a):.1f}" x2="{c + 62 * math.cos(a):.1f}" y2="{c + 62 * math.sin(a):.1f}" stroke="{DARK}" stroke-width="2.5" stroke-linecap="round"/>')
    return svg(400, 400, 'Bobine de filament', ''.join(parts))

# ---------------------------------------------------------------- diapositives
slides = {}

# 01 — Couverture : le logo construit par les machines comme dans la vidéo (voir cover.py),
# puis il remonte en haut à gauche et les informations s'affichent, avec la maquette de l'atelier à droite
from cover import cover
from embeds import six_embed, x_embed
T0 = 7.6                                   # arrivée des informations
T_SIX = T0 + 0.1                           # la buse imprime le « 6 » (1,8 s)
T_KICK = T_SIX + 1.8 + 0.5                 # la buse partie, le surtitre et les puces arrivent
six2, sw2, sh2 = hero_six_light(330)
HERO_X, HERO_Y = 128, 128 + 176 + 24 * 1.2 + 28      # coin du 6 dans la diapositive (mise en page en flux)
# copie du 6 pour la page intégrée, avec son propre identifiant de motif (aucun doublon d'id dans la diapositive)
six_page, (EW6, EH6, SX6, SY6) = six_embed(six2.replace('cv2-layers', 'xq-layers'), sw2, sh2, ink_top=10, ink_bot=sh2 - 10, t0=T_SIX)
six_html = x_embed('noexport', HERO_X - SX6, round(HERO_Y - SY6, 2), EW6, EH6, six_page)
chips = ''.join(
    f'<p class="chip cvIn" style="animation-delay:{T_KICK + 0.15 + n * 0.08:.2f}s"><span class="hl">{num}</span>{NB}{NB}{name}</p>'
    for n, (num, name) in enumerate((('01', 'Visites'), ('02', 'Premiers pas'), ('03', 'Immersion'), ('04', 'Métier augmenté'),
                                     ('05', 'Culture numérique'), ('06', 'Face caméra'))))
info_html = (
    f'<div class="kick cvIn" style="margin-top:176px; animation-delay:{T_KICK:.2f}s"><div class="sq"></div><p class="kicker">Catalogue des ateliers</p></div>'
    '<div style="display:flex; align-items:center; gap:56px; margin-top:28px">'
    f'<div class="cvSix" style="width:{sw2}px; height:{sh2}px">{six2}</div>'
    f'<div class="cvIn" style="width:600px; animation-delay:{T0 + 0.3:.2f}s">'
    '<p style="font-size:150px; font-weight:700; line-height:1; letter-spacing:-4px; color:#2f3a48">ateliers</p>'
    '<p style="font-size:28px; font-weight:400; line-height:1.4; color:#333333; margin-top:14px; white-space:nowrap">modulables selon les besoins du groupe</p>'
    '</div>'
    '</div>'
    f'<div style="display:flex; gap:14px; margin-top:auto">{chips}</div>'
)
info_css = [
    f'.cvSix {{ animation: fade 0.3s linear {T_SIX + 1.8 + 0.6:.2f}s both; }}',
    '.chip { font-size: 24px; font-weight: 500; color: #2f3a48; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 40px; '
    'padding: 10px 22px; line-height: 1.3; box-shadow: 0 4px 24px rgba(47, 58, 72, 0.06); white-space: nowrap; }',
    '.cvIn { animation: rise 0.65s cubic-bezier(0.2, 0.7, 0.2, 1) both; }',
]
cover_html, cover_css = cover(prog(1), info_html, info_css, six_html)
slides['couverture'] = cover_html

# 02 — Aperçu
TYPES = [
    ('01', 'Visites', f'2{NB}h', 2, 2),
    ('02', 'Premiers pas', f'8{NB}h', 8, 8),
    ('03', 'Immersion', f'40{NB}h', 40, 40),
    ('04', 'Métier augmenté', f'16 à 24{NB}h', 16, 24),
    ('05', 'Culture numérique', f'4 à 8{NB}h', 4, 8),
    ('06', 'Face caméra', f'4 à 8{NB}h', 4, 8),
]
OVW = 820
k = OVW / 40
scale = ''
for h in (0, 8, 16, 24, 32, 40):
    x = round(h * k)
    lab = '0' if h == 0 else f'{h}{NB}h'
    if h == 0:
        scale += f'<p class="tick" style="left:0px">{lab}</p>'
    elif h == 40:
        scale += f'<p class="tick" style="left:{x - 120}px; text-align:right">{lab}</p>'
    else:
        scale += f'<p class="tick" style="left:{x - 60}px; text-align:center">{lab}</p>'
grid = svg(OVW, 516, 'Repères de durée tous les 8 heures', ''.join(
    f'<line x1="{round(h * k) + (1 if h == 0 else -1 if h == 40 else 0)}" y1="0" x2="{round(h * k) + (1 if h == 0 else -1 if h == 40 else 0)}" y2="516" stroke="{LINE}" stroke-width="2" stroke-dasharray="4 8"/>'
    for h in (0, 8, 16, 24, 32, 40)))
rows = ''
for n, (num, name, dur, lo, hi) in enumerate(TYPES):
    solid = round(lo * k); hatch = round((hi - lo) * k)
    fill = f'<div class="solid" style="width:{solid}px; height:18px"></div>'
    if hatch:
        fill += f'<div class="hatch" style="width:{hatch}px; height:18px"></div>'
    rows += (
        f'<div class="ovrow a" style="--i:{n + 3}">'
        f'<p class="ovnum">{num}</p><p class="ovname">{name}</p>'
        f'<div class="ovtrack"><div class="grow" style="width:{solid + hatch}px; height:18px; border-radius:9px">'
        f'<div class="fill" style="width:{solid + hatch}px; height:18px; animation-delay:{0.45 + n * 0.11:.2f}s">{fill}</div></div></div>'
        f'<p class="ovdur">{dur}</p>'
        '</div>')
slides['apercu'] = (
    '<section id="apercu" class="light" data-transition="push">'
    f'{prog(2)}'
    + head('Le catalogue', 'Six ateliers,', 'modulables selon les besoins du groupe.') +
    '<div class="ov">'
    f'<div style="position:absolute; left:540px; top:48px; width:{OVW}px; height:516px">{grid}</div>'
    '<div class="ovrow ovhead f" style="--i:2"><p class="ovnum"></p><p class="ovname dlabel" style="font-size:24px">Atelier</p>'
    f'<div class="ovscale">{scale}</div><p class="ovdur dlabel" style="font-size:24px">Durée</p></div>'
    f'{rows}'
    '</div>'
    '</section>'
)

# 03-08 — Types
def type_slide(sid, idx, kicker, name, promise, text, dur_html, fig_html):
    return (
        f'<section id="{sid}" class="light" data-transition="push">'
        f'{bignum(f"0{idx}")}{prog(idx + 2)}'
        + head(f'0{idx} · {kicker}', name, promise) +
        '<div class="cols">'
        f'<div class="colL"><p class="body a" style="--i:2">{q(text)}</p><div class="spacer"></div>{dur_html}</div>'
        f'<div class="colR">{fig_html}</div>'
        '</div>'
        '</section>'
    )

T1 = ("Donner un aperçu de la Digital Factory et de la façon dont les métiers se numérisent, grâce à des démonstrations de machines. "
      "Les visites s'adressent aux groupes comme aux partenaires qui veulent voir ce qu'ils pourraient proposer à leur public.")
T2 = ("Faire découvrir comment les métiers se numérisent, de la conception à la fabrication. Les participants essaient deux technologies, "
      "une par demi-journée (par exemple l'impression 3D et la découpe laser), et voient ce qu'elles changent dans le travail. "
      "L'atelier vise l'acculturation et ne demande aucun prérequis.")
T3 = ("Mener un projet complet dans un scénario proche d'une situation professionnelle, de la conception d'un objet jusqu'à sa présentation. "
      "Le travail en équipe et l'expression orale y comptent autant que la technique. Ce format peut faire suite aux Premiers pas.")
T4 = ("Relier le numérique au métier que les stagiaires ont choisi, dans le cadre de leur parcours de formation. Conçus en lien avec le centre "
      "de compétence concerné, aujourd'hui ConstruForm, ces ateliers montrent ce que la fabrication numérique ou une application peut apporter "
      "sur le terrain. Les formateurs du centre gardent la main sur les techniques du métier.")
T5 = ("Développer les bons réflexes et l'esprit critique pour vivre et travailler avec le numérique, qu'il s'agisse de cybersécurité "
      "(comment protéger ses comptes et ses données) ou d'intelligence artificielle (ses enjeux et ses applications pratiques). "
      "Ces ateliers conviennent à des groupes de niveaux variés.")
T6 = (f"Aider chacun à se présenter avec plus d'assurance grâce au studio de captation vidéo{NB}: repérer ses freins et ses atouts, "
      "puis s'exercer à parler face à la caméra. Selon l'atelier, les participants repartent avec un support utile pour leur recherche "
      "d'emploi, comme un CV vidéo.")

# Fig 01 — Visites
fig1 = (
    '<div class="fig">'
    + pin(0, 0, 824, 0, '<p class="cap">Démonstrations de machines</p>', 'f', 3)
    + pin(20, 104, 200, 220, d_printer_body()
          + wrap(('rvb prt', 'rvbi prt'), 72, 118, 56, 50, d_printer_object())
          + f'<div class="hot" style="position:absolute; left:86px; top:46px; width:28px; height:44px">{d_hotend_small()}</div>', 'a', 4)
    + pin(292, 174, 260, 150, d_laser(), 'a', 5)
    + pin(600, 204, 220, 120, d_uv_body()
          + wrap(('rvx uvt', 'rvxi uvt'), 64, 54, 92, 14, d_uv_tile())
          + f'<div class="uvh" style="position:absolute; left:138px; top:30px; width:36px; height:16px">{d_uv_head()}</div>', 'a', 6)
    + pin(0, 318, 824, 130, d_route(), 'f', 7)
    + '</div>')

# Fig 02 — Premiers pas
def card(kick, drawing, title, sub, i, kh=None):
    khs = f' style="min-height:{kh}px"' if kh else ''
    return (f'<div class="card a" style="--i:{i}"><p class="ckick"{khs}>{q(kick)}</p>'
            f'<div style="margin-top:22px">{drawing}</div>'
            f'<h3 class="ctitle">{q(title)}</h3><p class="csub">{q(sub)}</p></div>')
fig2 = (
    '<div class="cards">'
    + card('Demi-journée 1', '<div style="position:relative; width:316px; height:200px">' + d_fdm_body() + wrap(('rvx lyA', 'rvxi lyA'), 40, 152, 236, 7, f'<div style="width:236px; height:7px; background:{BLUE}"></div>') + wrap(('rvl lyB', 'rvli lyB'), 40, 144, 236, 7, f'<div style="width:236px; height:7px; background:{VIOLET}"></div>') + f'<div class="hzy" style="position:absolute; left:132px; top:4px; width:52px; height:146px"><div class="hzx" style="width:52px; height:146px">{d_hotend_fdm()}</div></div>' + '</div>', 'Technologie 1', "par exemple l'impression 3D", 4)
    + card('Demi-journée 2', '<div style="position:relative; width:316px; height:200px">' + d_cut_body() + '<div class="orbit" style="position:absolute; left:116px; top:93px; width:84px; height:84px; display:flex; justify-content:center">' + f'<div class="orbiti" style="width:26px; height:26px; margin-top:-13px">{d_laser_dot()}</div></div>' + '</div>', 'Technologie 2', 'par exemple la découpe laser', 5)
    + '</div>')

# Fig 03 — Immersion
bars = ''
for n, (lab, col) in enumerate((('Travail en équipe', BLUE), ('Expression orale', VIOLET), ('Technique', DARK))):
    bars += (
        f'<div style="display:flex; align-items:center; gap:24px; margin-top:{18 if n else 20}px">'
        f'<p class="lab" style="width:290px; font-size:28px; font-weight:500">{lab}</p>'
        f'<div style="position:relative; width:500px; height:22px; border-radius:11px; overflow:hidden">'
        f'<div class="fill" style="width:500px; height:22px; animation-delay:0.75s"><div style="width:500px; height:22px; border-radius:11px; background:{col}"></div></div>'
        '</div></div>')
fig3 = (
    '<div class="fig">'
    + pin(0, 40, 150, 150, d_blueprint(), 'a', 3)
    + pin(192, 98, 440, 40, d_link(), 'f', 4)
    + pin(674, 40, 150, 150, d_present(), 'a', 5)
    + pin(0, 206, 300, 0, '<p class="lab">Conception<br>d’un objet</p>', 'a', 4)
    + pin(564, 206, 260, 0, '<p class="lab" style="text-align:right">Présentation</p>', 'a', 6)
    + pin(192, 0, 440, 0, '<p class="sub" style="text-align:center">Un scénario proche d’une situation professionnelle</p>', 'f', 5)
    + pin(0, 330, 824, 0, f'<p class="cap">Comptent autant dans le projet</p>{bars}', 'a', 7)
    + '</div>')

# Fig 04 — Métier augmenté
def node(x, w, icon, title, sub1, sub2, i):
    return pin(x, 0, w, 0, (
        f'<div style="box-sizing:border-box; width:{w}px; background:#ffffff; border:1px solid {LINE}; border-radius:14px; padding:30px; '
        'box-shadow:0 4px 24px rgba(47, 58, 72, 0.07)">'
        f'{icon}<h3 class="ctitle" style="margin-top:16px">{q(title)}</h3>'
        f'<p class="csub" style="color:{BLUE}; font-weight:500">{q(sub1)}</p><p class="csub" style="margin-top:2px">{q(sub2)}</p></div>'), 'a', i)
def node2(icon, title, sub1, sub2, i):
    return (f'<div class="a" style="--i:{i}; box-sizing:border-box; width:360px; background:#ffffff; border:1px solid {LINE}; border-radius:14px; padding:30px; '
            'box-shadow:0 4px 24px rgba(47, 58, 72, 0.07)">'
            f'{icon}<h3 class="ctitle" style="margin-top:16px">{q(title)}</h3>'
            f'<p class="csub" style="color:{BLUE}; font-weight:500">{q(sub1)}</p><p class="csub" style="margin-top:2px">{q(sub2)}</p></div>')
fig4 = (
    '<div class="fig">'
    + pin(0, 0, 824, 0, '<div style="display:flex; gap:104px; align-items:stretch">'
          + node2(d_printer_small(), 'Digital Factory', 'la technologie', 'fabrication numérique et applications', 3)
          + node2(d_wrench(), 'Centre de compétence', 'les techniques du métier', "aujourd'hui ConstruForm", 4)
          + '</div>')
    + pin(0, 368, 824, 94, d_merge(), 'f', 6)
    + pin(302, 372, 220, 0, f'<p class="pill" style="text-align:center; padding:6px 0; border-color:{VIOLET}; font-size:24px">conçus en lien</p>', 'a', 6)
    + pin(222, 462, 380, 0, (
        f'<div style="box-sizing:border-box; width:380px; background:{DARK}; border-radius:14px; padding:22px 28px; text-align:center">'
        '<p style="font-size:30px; font-weight:700; color:#ffffff; line-height:1.25">Les stagiaires</p>'
        '<p style="font-size:24px; color:#c5cad3; line-height:1.35; margin-top:4px">qui ont choisi leur métier</p></div>'), 'a', 7)
    + '</div>')

# Fig 05 — Culture numérique
fig5 = (
    '<div>'
    '<div class="cards">'
    + card('Cybersécurité', d_lock(), 'Protéger ses comptes et ses données', 'les bons réflexes au quotidien et au travail', 4, 60)
    + card('Intelligence artificielle', d_chip(), 'Ses enjeux et ses applications pratiques', "avec l'esprit critique", 5, 60)
    + '</div>'
    f'<div class="prow a" style="--i:6; margin-top:30px">{d_levels()}<p class="lab" style="font-weight:500">Pour des groupes de niveaux variés</p></div>'
    '</div>')

# Fig 06 — Face caméra
steps = ''
for n, (num, txt) in enumerate((('01', 'Repérer ses freins et ses atouts'), ('02', 'S’exercer à parler face à la caméra'))):
    steps += (
        f'<div style="display:flex; align-items:baseline; gap:24px; padding:16px 0; border-top:1px solid {LINE}">'
        f'<p style="width:48px; font-size:28px; font-weight:700; color:{BLUE}; line-height:1.2">{num}</p>'
        f'<p class="lab" style="font-size:30px">{txt}</p></div>')
fig6 = (
    '<div class="fig">'
    + pin(0, 0, 330, 270, d_camera_body(), 'a', 3)
    + pin(193, 55, 18, 18, '', 'rec', None, f' border-radius:9px; background:{PINK};')
    + pin(424, 4, 380, 260, f'<div class="focus" style="width:380px; height:260px">{d_frame()}</div>', 'a', 4)
    + pin(0, 296, 824, 0, steps, 'a', 5)
    + pin(0, 476, 824, 0, (
        f'<div class="prow"><div class="sq" style="width:16px; height:16px"></div>'
        '<p class="lab" style="font-weight:500">Selon l’atelier : un CV vidéo à la clé</p></div>').replace(' : ', f'{NB}: '), 'a', 6)
    + '</div>')

TY = [
    ('visites', 1, 'Visites', 'Visites', 'les métiers qui se numérisent.', T1, duration(f'2{NB}h', 2, 2, public=('Chercheurs d’emploi en formation', 'Formateurs et opérateurs')), fig1),
    ('premiers-pas', 2, 'Premiers pas', 'Premiers pas', 'deux technologies à essayer.', T2, duration(f'8{NB}h', 8, 8, 'soit une journée', public=('Chercheurs d’emploi inscrits via Formapass', 'Groupes de chercheurs d’emploi en formation')), fig2),
    ('immersion', 3, 'Immersion', 'Immersion', 'un projet complet.', T3, duration(f'40{NB}h', 40, 40, public=('Chercheurs d’emploi à la suite des Premiers pas', 'Chercheurs d’emploi inscrits via Formapass')), fig3),
    ('metiers', 4, 'Métier augmenté', 'Métier augmenté', 'relier le numérique au métier.', T4, duration(f'16 à 24{NB}h', 16, 24, public=('Chercheurs d’emploi en formation métier',)), fig4),
    ('culture-numerique', 5, 'Culture numérique', 'Culture numérique', 'réflexes et esprit critique.', T5, duration(f'4 à 8{NB}h', 4, 8, public=('Chercheurs d’emploi en formation', 'Chercheurs d’emploi en formation métier')), fig5),
    ('prise-de-parole', 6, 'Face caméra', 'Face caméra', 'gagner en assurance.', T6, duration(f'4 à 8{NB}h', 4, 8, public=('Chercheurs d’emploi en formation', 'Chercheurs d’emploi en formation métier')), fig6),
]
for sid, idx, kick, name, promise, text, dh, fh in TY:
    slides[sid] = type_slide(sid, idx, kick, name, promise, text, dh, fh)

# 09 — Modularité
TM = ("Selon les besoins du groupe, un module Culture numérique ou Face caméra peut compléter un autre atelier ou en remplacer une partie. "
      "Les durées indiquées servent donc de repère.")
def scen(kick, boxes, sub, i):
    return (f'<div class="card a" style="--i:{i}; width:640px; padding:34px 34px 30px">'
            f'<p class="ckick" style="color:{BLUE}">{q(kick)}</p>'
            f'<div class="brow" style="margin-top:26px">{boxes}</div>'
            f'<p class="csub" style="margin-top:22px">{q(sub)}</p></div>')
AT = '<div class="box at" style="width:112px">Atelier</div>'
def MOD(cls, i):
    return f'<div class="box mod {cls}" style="width:136px; --i:{i}">Module</div>'
figm = (
    '<div class="cards" style="gap:52px; margin-top:56px">'
    + scen('Compléter', AT + AT + MOD('sl', 6), 'un module complète l’atelier', 3)
    + scen('Remplacer une partie', AT + MOD('dr', 7), 'un module remplace une partie de l’atelier', 4)
    + '</div>'
    '<div class="prow f" style="--i:9; gap:40px; margin-top:36px">'
    f'<div class="prow" style="gap:14px"><div style="width:28px; height:28px; border-radius:6px; background:{VIOLET}"></div>'
    '<p class="sub" style="color:#333333">Module Culture numérique ou Face caméra</p></div>'
    f'<div class="prow" style="gap:14px"><div style="box-sizing:border-box; width:28px; height:28px; border-radius:6px; border:2px solid {DARK}; background:#ffffff"></div>'
    '<p class="sub" style="color:#333333">Atelier</p></div>'
    '</div>')
slides['modularite'] = (
    '<section id="modularite" class="light" data-transition="push">'
    f'{prog(9)}'
    + head('Modularité', 'Des ateliers', 'modulables.') +
    f'<p class="body a" style="--i:2; margin-top:48px; width:1320px; font-size:28px">{q(TM)}</p>'
    f'{figm}'
    '</section>'
)

# 10 — En résumé
RC = [
    ('01', 'Visites', f'2{NB}h', 'un aperçu de la numérisation des métiers'),
    ('02', 'Premiers pas', f'8{NB}h', 'deux technologies à essayer'),
    ('03', 'Immersion', f'40{NB}h', 'un projet complet, de la conception à la présentation'),
    ('04', 'Métier augmenté', f'16 à 24{NB}h', 'le numérique relié au métier choisi'),
    ('05', 'Culture numérique', f'4 à 8{NB}h', 'cybersécurité et intelligence artificielle'),
    ('06', 'Face caméra', f'4 à 8{NB}h', 'gagner en assurance pour se présenter'),
]
rrows = ''.join(
    f'<div class="rcrow a" style="--i:{n + 2}"><p class="rcnum">{a}</p><p class="rcname">{b}</p><p class="rcdur">{c}</p><p class="rcdesc">{d}</p></div>'
    for n, (a, b, c, d) in enumerate(RC))
slides['resume'] = (
    '<section id="resume" class="dark foot" data-transition="push">'
    f'{prog(10)}'
    '<div class="kick a" style="--i:0"><div class="sq"></div><p class="kicker">En résumé</p></div>'
    f'<div class="rc" style="margin-top:auto; margin-bottom:auto">{rrows}</div>'
    '<div class="footer f" style="--i:9"><div class="kick"><div class="sq"></div><p class="kicker">Digital Factory · Le Forem</p></div></div>'
    '</section>'
)

ORDER = ['couverture', 'apercu', 'visites', 'premiers-pas', 'immersion', 'metiers', 'culture-numerique', 'prise-de-parole', 'modularite', 'resume']
assert set(ORDER) == set(slides), set(slides) ^ set(ORDER)

os.makedirs(f'{ROOT}/slides', exist_ok=True)
for sid in ORDER:
    with open(f'{ROOT}/slides/{sid}.html', 'w', encoding='utf-8') as fh:
        fh.write(slides[sid] + '\n')

deck = {
    "v": 5,
    "createdOnFiles": {"v": 1, "at": datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')},
    "lists": "css",
    "format": {"v": 1, "shared": ["project/deck.css"]},
    "title": "Les types d’ateliers de la Digital Factory",
    "order": ORDER,
    "sections": {
        "s1": {"description": "Ouverture : les ateliers de la Digital Factory et leurs six types.", "start": "couverture"},
        "s2": {"description": "Les six types d’ateliers, un par diapositive.", "start": "visites"},
        "s3": {"description": "La modularité des ateliers et le résumé.", "start": "modularite"},
    },
    "cover": "couverture",
    "faces": {"poppins": {"family": "Poppins", "href": "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;700&display=swap"}},
    "designSystems": [],
}
with open(f'{ROOT}/deck.json', 'w', encoding='utf-8') as fh:
    json.dump(deck, fh, ensure_ascii=False, indent=1)

for sid in ORDER:
    p = f'{ROOT}/slides/{sid}.html'
    print(sid, os.path.getsize(p), 'octets')


# ---------------------------------------------------------------- CSS de la couverture (bloc régénéré)
_css_path = f'{ROOT}/deck.css'
_css = open(_css_path, encoding='utf-8').read()
_a, _b = '/* couverture:début */', '/* couverture:fin */'
if _a in _css:
    _css = _css[:_css.index(_a)].rstrip() + '\n' + _css[_css.index(_b) + len(_b):].lstrip('\n')
_css = _css.rstrip() + '\n\n' + cover_css + '\n'
open(_css_path, 'w', encoding='utf-8').write(_css)
print('deck.css', len(_css), 'octets')
