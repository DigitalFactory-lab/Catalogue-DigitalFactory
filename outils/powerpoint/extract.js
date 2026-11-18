// Mesure la mise en page rendue du deck web et l'exporte en JSON (positions, styles, animations, SVG).
const { chromium } = require('/opt/npm-tools/node_modules/playwright');
const fs = require('fs'); const path = require('path');
const ROOT = process.argv[2]; const OUT = process.argv[3];
const deck = JSON.parse(fs.readFileSync(path.join(ROOT, 'project/deck.json'), 'utf8'));
const base = `* { margin: 0 } body { font: 32px/1.2 sans-serif }
body > section { width: 1920px !important; height: 1080px !important; overflow: hidden !important; box-sizing: border-box !important; position: relative; isolation: isolate }
section[hidden], aside, noscript { display: none !important }
h1 { font-size: 96px; font-weight: 600 } h2 { font-size: 64px; font-weight: 600 } h3 { font-size: 44px; font-weight: 600 }
p, li, h1, h2, h3, td, th { overflow-wrap: break-word; text-wrap: pretty }`;
const secs = deck.order.map(id => fs.readFileSync(path.join(ROOT, 'project/slides', id + '.html'), 'utf8')
  .replace(/<x-embed([^>]*)>[\s\S]*?<\/x-embed>/g, '<x-embed$1></x-embed>')).join('\n');   // pages intégrées : absentes du PowerPoint
const html = `<!doctype html><html><head><meta charset="utf-8"><style>${base}</style><link rel="stylesheet" href="/project/deck.css"></head><body>${secs}</body></html>`;
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome', args: ['--host-resolver-rules=MAP * ^NOTFOUND'] });
  const ctx = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1920, height: 1080 } });
  const page = await ctx.newPage(); let first = true;
  await page.route('**/*', async (route) => {
    const req = route.request(); const u = new URL(req.url());
    if (req.isNavigationRequest()) { if (!first) return route.abort('aborted'); first = false; return route.fulfill({ contentType: 'text/html', body: html }); }
    if (u.pathname.startsWith('/project/')) { const p = path.join(ROOT, decodeURIComponent(u.pathname)); if (!p.startsWith(path.join(ROOT, 'project'))) return route.abort('aborted'); return route.fulfill({ path: p, contentType: p.endsWith('.css') ? 'text/css' : undefined }); }
    return route.abort('aborted');
  });
  await page.goto('http://deck.local/');
  await page.evaluate(() => document.fonts.ready);
  // 1. noter les animations déclarées, 2. les couper pour mesurer l'état final
  await page.evaluate(() => {
    document.querySelectorAll('body > section *').forEach(el => {
      const cs = getComputedStyle(el);
      if (cs.animationName && cs.animationName !== 'none') {
        el.dataset.an = cs.animationName.split(',')[0].trim();
        el.dataset.ad = String(Math.round(parseFloat(cs.animationDelay.split(',')[0]) * 1000));
        el.dataset.au = String(Math.round(parseFloat(cs.animationDuration.split(',')[0]) * 1000));
      }
    });
    const st = document.createElement('style'); st.textContent = '* { animation: none !important; transition: none !important; }';
    document.head.appendChild(st);
  });
  const data = await page.evaluate(() => {
    const toHex = (c) => { const m = c && c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(',').map(s => s.trim()); const v = p.slice(0, 3).map(Number); return { hex: v.map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase(), a: p[3] !== undefined ? Number(p[3]) : 1 }; };
    const out = [];
    for (const sec of document.querySelectorAll('body > section')) {
      const sr = sec.getBoundingClientRect(); const items = []; let nsvg = 0;
      const R = (el) => { const r = el.getBoundingClientRect(); return { x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height }; };
      const animOf = (el) => { let e = el; while (e && e !== sec) { if (e.dataset && e.dataset.an) return { name: e.dataset.an, delay: +e.dataset.ad, dur: +e.dataset.au }; e = e.parentElement; } return null; };
      const textStyle = (el) => { const cs = getComputedStyle(el); const fs = parseFloat(cs.fontSize); let lh = cs.lineHeight === 'normal' ? fs * 1.2 : parseFloat(cs.lineHeight); return { size: fs, weight: +cs.fontWeight, color: toHex(cs.color), lh, ls: cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing), align: cs.textAlign, upper: cs.textTransform === 'uppercase' }; };
      const runsOf = (el) => { const runs = []; const up = getComputedStyle(el).textTransform === 'uppercase';
        const rec = (node) => { for (const ch of node.childNodes) {
          if (ch.nodeType === 3) { let t = ch.textContent; if (!t) continue; if (up) t = t.toUpperCase(); const cs = getComputedStyle(ch.parentElement); runs.push({ t, color: toHex(cs.color), weight: +cs.fontWeight }); }
          else if (ch.nodeName === 'BR') runs.push({ br: true });
          else if (ch.nodeType === 1) rec(ch); } };
        rec(el); return runs; };
      const boxStyle = (el) => { const cs = getComputedStyle(el); const bg = toHex(cs.backgroundColor); const bw = parseFloat(cs.borderTopWidth) || 0;
        return { bg: bg && bg.a > 0 ? bg : null, bgImage: cs.backgroundImage !== 'none' ? cs.backgroundImage : null, bw: cs.borderTopStyle === 'none' ? 0 : bw, bc: toHex(cs.borderTopColor), bstyle: cs.borderTopStyle,
          btop: (parseFloat(cs.borderTopWidth) || 0) > 0 && cs.borderTopStyle !== 'none' && ((parseFloat(cs.borderLeftWidth) || 0) === 0 || cs.borderLeftStyle === 'none'),
          radius: parseFloat(cs.borderTopLeftRadius) || 0, shadow: cs.boxShadow !== 'none' ? cs.boxShadow : null }; };
      const walk = (el) => {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return;
        const tag = el.tagName.toLowerCase();
        if (tag === 'aside') return;
        if (tag === 'svg') { nsvg++; items.push({ kind: 'img', id: `${sec.id}_${nsvg}`, svg: el.outerHTML, label: el.getAttribute('aria-label'), ...R(el), anim: animOf(el), cls: el.parentElement.className }); return; }
        if (/\bnoexport\b/.test(el.getAttribute('class') || '')) return;
        const bs = boxStyle(el);
        if (tag === 'ul' || tag === 'ol') {
          const lis = [...el.children].filter(c => c.tagName === 'LI');
          const lcs = lis.length ? getComputedStyle(lis[0]) : cs;
          items.push({ kind: 'list', tag, cls: el.className, ordered: tag === 'ol',
            lis: lis.map(li => ({ runs: runsOf(li), color: toHex(getComputedStyle(li).color) })),
            st: textStyle(lis[0] || el), indent: parseFloat(cs.paddingLeft) || 0, gap: parseFloat(lcs.marginTop) || 0,
            ...R(el), anim: animOf(el) });
          return;
        }
        const isText = ['p', 'h1', 'h2', 'h3'].includes(tag);
        const directText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
        const painted = bs.bg || bs.bgImage || bs.bw > 0;
        if (isText || directText) {
          items.push({ kind: 'text', tag, cls: el.className, runs: runsOf(el), st: textStyle(el), box: painted ? bs : null, flexCenter: cs.justifyContent === 'center', ...R(el), anim: animOf(el), parentCls: el.parentElement.className });
          return;
        }
        // hachures (durée variable) : redessinées en SVG avec leurs vraies couleurs
        if (bs.bgImage && bs.bgImage.includes('repeating-linear-gradient')) {
          const cols = bs.bgImage.match(/rgba?\([^)]+\)/g) || ['rgb(91, 96, 168)', 'rgb(224, 224, 224)'];
          const r = R(el); nsvg++;
          const hs = `<svg xmlns="http://www.w3.org/2000/svg" width="${r.w}" height="${r.h}" viewBox="0 0 ${r.w} ${r.h}">` +
            `<defs><pattern id="h" patternUnits="userSpaceOnUse" width="9" height="9" patternTransform="rotate(45)">` +
            `<rect width="9" height="9" fill="${cols[cols.length - 1]}"/><rect width="4" height="9" fill="${cols[0]}"/></pattern></defs>` +
            `<rect width="${r.w}" height="${r.h}" fill="url(#h)"/></svg>`;
          items.push({ kind: 'img', id: `${sec.id}_${nsvg}`, svg: hs, label: 'Durée variable', ...r, anim: animOf(el), cls: el.className });
          return;
        }
        if (painted) items.push({ kind: 'box', tag, cls: el.className, bs, ...R(el), anim: animOf(el) });
        for (const ch of el.children) walk(ch);
      };
      for (const ch of sec.children) walk(ch);
      out.push({ id: sec.id, cls: sec.className, transition: sec.dataset.transition || null, items });
    }
    return out;
  });
  fs.writeFileSync(path.join(OUT, 'layout.json'), JSON.stringify(data, null, 1));
  fs.mkdirSync(path.join(OUT, 'svg'), { recursive: true });
  for (const s of data) for (const it of s.items) if (it.kind === 'img') fs.writeFileSync(path.join(OUT, 'svg', it.id + '.svg'), it.svg);
  console.log(data.map(s => `${s.id}: ${s.items.length} items`).join('\n'));
  await browser.close();
})();
