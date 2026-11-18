#!/usr/bin/env python3
"""Version web autonome du catalogue (index.html), pour GitHub Pages ou tout hébergement statique.

Mêmes diapositives que la présentation en ligne (mêmes fichiers HTML et CSS). Un petit lecteur
affiche une diapositive à la fois, à l'échelle de la fenêtre : flèches du clavier, clic, glissement
du doigt, touche F pour le plein écran, numéro de diapositive dans l'adresse (#3).
Les pages intégrées (<x-embed>) deviennent des iframes isolées (sandbox="allow-scripts").

Usage : python3 web.py DOSSIER_PROJECT SORTIE.html [DOSSIER_POLICES]
Avec DOSSIER_POLICES (chemin relatif à la page, par ex. « fonts »), Poppins est servie depuis le site
lui-même (fichiers woff2) au lieu de Google Fonts : aucune requête vers un service tiers.
"""
import html
import json
import os
import re
import sys

DECK = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/deck/project'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'index.html'

deck = json.load(open(os.path.join(DECK, 'deck.json'), encoding='utf-8'))
deck_css = open(os.path.join(DECK, 'deck.css'), encoding='utf-8').read()
title = deck.get('title', 'Présentation')
FONT_DIR = sys.argv[3] if len(sys.argv) > 3 else None
if FONT_DIR:
    fonts = '<style>' + ''.join(
        f"@font-face {{ font-family: 'Poppins'; font-style: normal; font-weight: {w}; font-display: swap; "
        f"src: url('{FONT_DIR}/Poppins-{name}.woff2') format('woff2'); }}"
        for w, name in ((400, 'Regular'), (500, 'Medium'), (700, 'Bold'))) + '</style>'
else:
    fonts = ''.join(f'<link rel="stylesheet" href="{html.escape(f["href"])}">'
                    for f in deck.get('faces', {}).values() if f.get('href'))


def to_iframe(m):
    attrs, inner = m.group(1), m.group(2)
    style = re.search(r'style="([^"]*)"', attrs).group(1)
    return (f'<iframe class="emb" sandbox="allow-scripts" aria-hidden="true" tabindex="-1" title="" '
            f'style="{style}" srcdoc="{html.escape(inner, quote=True)}"></iframe>')


slides = []
for sid in deck['order']:
    s = open(os.path.join(DECK, 'slides', sid + '.html'), encoding='utf-8').read()
    s = re.sub(r'<x-embed([^>]*)>(.*?)</x-embed>', to_iframe, s, flags=re.S)
    s = re.sub(r'<aside>.*?</aside>', '', s, flags=re.S)
    slides.append(s)

BASE = """* { margin: 0 }
html, body { height: 100%; }
body { font: 32px/1.2 sans-serif; overflow: hidden; background: #1f2630; }
h1 { font-size: 96px; font-weight: 600 } h2 { font-size: 64px; font-weight: 600 } h3 { font-size: 44px; font-weight: 600 }
p, li, h1, h2, h3, td, th { overflow-wrap: break-word; text-wrap: pretty }
x-shape, x-icon { display: block }
"""

PLAYER_CSS = """
#deck { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; transform-origin: 0 0; }
#deck > section { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; overflow: hidden; isolation: isolate; }
#deck > section:not(.on) { display: none !important; }
iframe.emb { display: block; border: 0; background: transparent; pointer-events: none; }
#ui { position: fixed; right: 16px; bottom: 16px; display: flex; align-items: center; gap: 4px; padding: 4px;
  background: rgba(31, 38, 48, 0.82); border-radius: 999px; font: 500 14px/1 'Poppins', Arial, sans-serif; color: #ffffff;
  transition: opacity 0.4s; z-index: 10; }
#ui.idle { opacity: 0; }
#ui button { width: 36px; height: 36px; border: 0; border-radius: 50%; background: transparent; color: inherit; cursor: pointer;
  display: flex; align-items: center; justify-content: center; }
#ui button:hover:not(:disabled), #ui button:focus-visible { background: rgba(255, 255, 255, 0.16); outline: none; }
#ui button:disabled { opacity: 0.35; cursor: default; }
#ui svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }
#count { min-width: 56px; text-align: center; font-variant-numeric: tabular-nums; }
"""

ICON = lambda d: f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{d}"/></svg>'
UI = ('<nav id="ui" aria-label="Navigation dans la présentation">'
      f'<button id="prev" type="button" aria-label="Diapositive précédente">{ICON("M15 5l-7 7 7 7")}</button>'
      '<span id="count" aria-live="polite"></span>'
      f'<button id="next" type="button" aria-label="Diapositive suivante">{ICON("M9 5l7 7-7 7")}</button>'
      f'<button id="fs" type="button" aria-label="Plein écran (touche F)">{ICON("M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5")}</button>'
      '</nav>')

JS = """(function () {
  var D = document.getElementById('deck'), S = [].slice.call(D.children), n = S.length, cur = -1;
  var ui = document.getElementById('ui'), count = document.getElementById('count');
  var prev = document.getElementById('prev'), next = document.getElementById('next');
  // Ordre de peinture de Slides : les éléments épinglés placés avant le premier élément en flux passent dessous.
  S.forEach(function (sec) {
    for (var i = 0; i < sec.children.length; i++) {
      var ch = sec.children[i];
      if (getComputedStyle(ch).position === 'absolute') ch.style.zIndex = '-1'; else break;
    }
    [].forEach.call(sec.querySelectorAll('*'), function (el) {
      var p = el.parentElement, ps = p && getComputedStyle(p);
      if (ps && ps.display.indexOf('flex') >= 0 && ps.flexDirection.indexOf('column') === 0 &&
          parseFloat(getComputedStyle(el).flexGrow) > 0) el.style.minHeight = '0';
    });
  });
  function fit() {
    var k = Math.min(innerWidth / 1920, innerHeight / 1080);
    D.style.transform = 'translate(' + (innerWidth - 1920 * k) / 2 + 'px,' + (innerHeight - 1080 * k) / 2 + 'px) scale(' + k + ')';
  }
  function go(i) {
    i = Math.max(0, Math.min(n - 1, i));
    if (i === cur) return;
    if (cur >= 0) S[cur].classList.remove('on');
    cur = i;
    S[cur].classList.add('on');
    count.textContent = (cur + 1) + ' / ' + n;
    prev.disabled = cur === 0; next.disabled = cur === n - 1;
    if (history.replaceState) history.replaceState(null, '', '#' + (cur + 1));
  }
  function fullscreen() {
    var d = document, e = d.documentElement;
    if (d.fullscreenElement || d.webkitFullscreenElement) (d.exitFullscreen || d.webkitExitFullscreen).call(d);
    else if (e.requestFullscreen || e.webkitRequestFullscreen) (e.requestFullscreen || e.webkitRequestFullscreen).call(e);
  }
  var t; function wake() { ui.classList.remove('idle'); clearTimeout(t); t = setTimeout(function () { ui.classList.add('idle'); }, 2500); }
  addEventListener('resize', fit);
  addEventListener('mousemove', wake);
  addEventListener('keydown', function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    var k = e.key;
    if (k === 'ArrowRight' || k === 'PageDown' || k === ' ' || k === 'Enter') { go(cur + 1); e.preventDefault(); }
    else if (k === 'ArrowLeft' || k === 'PageUp' || k === 'Backspace') { go(cur - 1); e.preventDefault(); }
    else if (k === 'Home') go(0);
    else if (k === 'End') go(n - 1);
    else if (k === 'f' || k === 'F') fullscreen();
  });
  prev.onclick = function (e) { e.stopPropagation(); go(cur - 1); };
  next.onclick = function (e) { e.stopPropagation(); go(cur + 1); };
  document.getElementById('fs').onclick = function (e) { e.stopPropagation(); fullscreen(); };
  D.addEventListener('click', function (e) { go(e.clientX < innerWidth * 0.3 ? cur - 1 : cur + 1); });
  var x0 = null;
  addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; wake(); }, { passive: true });
  addEventListener('touchend', function (e) {
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0; x0 = null;
    if (Math.abs(dx) > 50) go(dx < 0 ? cur + 1 : cur - 1);
  });
  addEventListener('hashchange', function () { go((parseInt(location.hash.slice(1), 10) || 1) - 1); });
  fit(); go((parseInt(location.hash.slice(1), 10) || 1) - 1); wake();
})();"""

page = (
    '<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    f'<title>{html.escape(title)}</title>\n'
    '<meta name="description" content="Catalogue des ateliers de la Digital Factory du Forem : six ateliers, '
    'modulables selon les besoins du groupe.">\n'
    f'{fonts}\n<style>\n{BASE}{deck_css}{PLAYER_CSS}</style>\n'
    '<noscript><style>body { overflow: auto; } #deck { position: static; } '
    '#deck > section:not(.on) { position: relative; display: flex !important; }</style></noscript>\n'
    '</head>\n<body>\n<main id="deck">\n' + '\n'.join(slides) + '\n</main>\n' + UI + f'\n<script>\n{JS}\n</script>\n</body>\n</html>\n'
)
open(OUT, 'w', encoding='utf-8').write(page)
print(OUT, len(page.encode('utf-8')), 'octets,', len(slides), 'diapositives')
