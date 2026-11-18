"""Couverture du catalogue.

Trois pages intégrées (voir embeds.py) jouent l'intro (le logo construit par les machines, puis
le logo part en haut à gauche), l'impression du « 6 » et le dessin de la maquette de l'atelier.
La diapositive porte aussi les mêmes éléments en version fixe (logo, 6, maquette) : l'éditeur,
les exports et PowerPoint montrent ainsi la couverture terminée, et pendant la présentation ces
éléments apparaissent en fondu par-dessus leur double animé quand celui-ci a fini.
Renvoie le HTML de la section et le bloc CSS de la couverture.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = json.load(open(os.path.join(HERE, 'logo_parts.json')))
TEAL = LOGO['teal']['color']


def svg(w, h, label, inner, vb=None):
    vb = vb or f'0 0 {w} {h}'
    return (f'<svg width="{w:g}" height="{h:g}" viewBox="{vb}" aria-label="{label}" '
            f'xmlns="http://www.w3.org/2000/svg" style="display:block">{inner}</svg>')


def pin(x, y, w, h, inner='', cls='', style=''):
    c = f' class="{cls}"' if cls else ''
    return (f'<div{c} style="position:absolute; left:{x:g}px; top:{y:g}px; width:{w:g}px; height:{h:g}px;{style}">'
            f'{inner}</div>')


# ---------------------------------------------------------------- nouvelle couverture : pages intégrées + éléments fixes
# Les pages intégrées (x-embed) jouent l'intro, l'impression du 6 et le dessin de la maquette.
# Les éléments fixes de la diapositive (logo, 6, maquette) montrent l'état final dans l'éditeur,
# les exports et PowerPoint ; pendant la présentation, ils apparaissent en fondu par-dessus
# leur double animé quand celui-ci a fini.
MQX, MQY = 1075, 250
T_LOGO_SEAL = 8.7


def logo_seal():
    from embeds import enc, logo_polys, FIN_X, FIN_Y, VB, SC, g
    subs = []
    for k in ('digital', 'factory', 'sep', 'by', 'forem'):
        subs += [[(x - VB[0], y - VB[1]) for x, y in p] for p in logo_polys(LOGO[k]['d'])]
    tb = LOGO['teal']['bbox']
    w, h = round(VB[2] * SC, 2), round(VB[3] * SC, 2)
    inner = (f'<g transform="scale({SC / 4:.6g})"><path d="{enc(subs, 4)}" fill="#000000" fill-rule="evenodd"/>'
             f'<rect x="{g((tb[0] - VB[0]) * 4)}" y="{g((tb[1] - VB[1]) * 4)}" width="{g((tb[2] - tb[0]) * 4)}" '
             f'height="{g((tb[3] - tb[1]) * 4)}" fill="{TEAL}"/></g>')
    html = (f'<div class="cvLg" style="position:absolute; left:{FIN_X:.2f}px; top:{FIN_Y:.2f}px; width:{w}px; height:{h}px; '
            f'background:#f4f5f7">{svg(w, h, "Digital Factory by Forem", inner)}</div>')
    return html, [f'.cvLg {{ animation: fade 0.3s linear {T_LOGO_SEAL}s both; }}']


def cover(prog_html, info_html, info_css, six_html, mq_t0=7.8):
    from embeds import intro_embed, maquette_embed, x_embed, EX, EY, EW, EH
    seal_html, seal_css = logo_seal()
    mq_page, mq_static, (w, h), end = maquette_embed(mq_t0)
    html = (
        '<section id="couverture" class="light cover" data-transition="push">'
        + prog_html
        + x_embed('noexport', EX, EY, EW, EH, intro_embed())
        + seal_html
        + x_embed('noexport', MQX, MQY, w, h, mq_page)
        + pin(MQX, MQY, w, h, mq_static, cls='cvMq')
        + six_html
        + info_html
        + '</section>'
    )
    css = (['/* couverture:début */'] + seal_css
           + [f'.cvMq {{ animation: fade 0.4s linear {end + 0.5:.2f}s both; }}'] + info_css + ['/* couverture:fin */'])
    return html, '\n'.join(css)
