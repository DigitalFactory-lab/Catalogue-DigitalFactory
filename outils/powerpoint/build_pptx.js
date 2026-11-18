// Construit le PowerPoint à partir de la mise en page mesurée sur la version web (layout.json).
const pptxgen = require('/opt/npm-tools/node_modules/pptxgenjs');
const SKILL = '/root/.claude/skills/synced/e89c4d2b-9a64-4639-b9cd-9da828478f08_881957ae-9ffb-4883-abe2-5c5b30a17dfc/pptx';
const { applyTheme } = require(SKILL + '/scripts/apply_theme.js');
const fs = require('fs'); const path = require('path');
const L = JSON.parse(fs.readFileSync('/home/claude/pptx/layout.json', 'utf8'));
const OUT = process.argv[2] || '/home/claude/pptx/types-ateliers-digital-factory.pptx';

const THEME = { name: 'Digital Factory', headFontFace: 'Poppins', bodyFontFace: 'Poppins',
  colors: { dk1: '333333', lt1: 'FFFFFF', dk2: '2F3A48', lt2: 'F4F5F7', accent1: '5B60A8', accent2: '8C4292',
            accent3: '5F6673', accent4: 'E0E0E0', accent5: 'C5CAD3', accent6: 'E3E5EA', hlink: '5B60A8', folHlink: '8C4292' } };
const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.theme = { headFontFace: 'Poppins', bodyFontFace: 'Poppins' };
pres.title = 'Les types d’ateliers de la Digital Factory';
pres.author = 'Digital Factory – Le Forem';
const C = pres.SchemeColor;
const SCHEME = { '333333': C.text1, 'FFFFFF': C.background1, '2F3A48': C.text2, 'F4F5F7': C.background2, '5B60A8': C.accent1,
  '8C4292': C.accent2, '5F6673': C.accent3, 'E0E0E0': C.accent4, 'C5CAD3': C.accent5, 'E3E5EA': C.accent6 };
const col = (hex) => SCHEME[hex] || hex;
const P = (px) => +(px / 144).toFixed(4);
const pt = (px) => +(px / 2).toFixed(2);

// ---------------------------------------------------------------- dispositions (layouts)
const kickerPh = (color) => ({ placeholder: { options: { name: 'kicker', type: 'body', x: P(158), y: P(126), w: P(1300), h: P(34),
  fontSize: 12, color, valign: 'middle', margin: 0, charSpacing: 1.5 }, text: '' } });
const covSlide = L.find(x => x.id === 'couverture');
const covTitle = covSlide.items.find(it => it.kind === 'text' && it.runs.map(r => r.t || '').join('').includes('types d’ateliers'));
pres.defineSlideMaster({ title: 'DF Couverture', background: { color: 'F4F5F7' },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: P(covTitle.x), y: P(covTitle.y), w: P(covTitle.w + 12), h: P(covTitle.h + 8),
      fontSize: 32, bold: true, color: C.text2, align: 'left', valign: 'top', margin: 0, lineSpacing: 35.2, charSpacing: -0.75 }, text: '' } },
    { rect: { x: 0, y: P(1074), w: P(1920), h: P(6), fill: { color: C.accent4 } } },
  ] });
pres.defineSlideMaster({ title: 'DF Contenu', background: { color: 'F4F5F7' },
  objects: [
    { rect: { x: P(128), y: P(135), w: P(14), h: P(14), fill: { color: C.accent2 } } },
    kickerPh(C.accent1),
    { placeholder: { options: { name: 'title', type: 'title', x: P(128), y: P(174), w: P(1664), h: P(150), fontSize: 32, bold: true,
      color: C.text2, align: 'left', valign: 'top', margin: 0, lineSpacing: 35.2, charSpacing: -0.75 }, text: '' } },
    { rect: { x: 0, y: P(1074), w: P(1920), h: P(6), fill: { color: C.accent4 } } },
  ] });
const contentObjects = (bgSquare, kickerColor, titleColor, track) => ([
  { rect: { x: P(128), y: P(135), w: P(14), h: P(14), fill: { color: bgSquare } } },
  kickerPh(kickerColor),
  { placeholder: { options: { name: 'title', type: 'title', x: P(128), y: P(174), w: P(1664), h: P(150), fontSize: 32, bold: true,
    color: titleColor, align: 'left', valign: 'top', margin: 0, lineSpacing: 35.2, charSpacing: -0.75 }, text: '' } },
  { rect: { x: 0, y: P(1074), w: P(1920), h: P(6), fill: track } },
]);
pres.defineSlideMaster({ title: 'DF Contenu lavande', background: { color: 'EAEBF5' },
  objects: contentObjects(C.accent2, C.accent1, C.text2, { color: C.accent4 }) });
pres.defineSlideMaster({ title: 'DF Sombre contenu', background: { color: '2F3A48' },
  objects: contentObjects(C.background1, C.background1, C.background1, { color: '4A5566' }) });
pres.defineSlideMaster({ title: 'DF Dégradé', background: { path: '/home/claude/pptx/img/grad.png' },
  objects: contentObjects(C.background1, C.background1, C.background1, { color: 'FFFFFF', transparency: 72 }) });
pres.defineSlideMaster({ title: 'DF Sombre', background: { color: '2F3A48' },
  objects: [
    { rect: { x: P(128), y: P(135), w: P(14), h: P(14), fill: { color: C.background1 } } },
    kickerPh(C.background1),
    { rect: { x: P(128), y: P(994), w: P(14), h: P(14), fill: { color: C.background1 } } },
    { text: { text: 'DIGITAL FACTORY · LE FOREM', options: { x: P(158), y: P(985), w: P(900), h: P(32), fontSize: 12, color: C.background1,
      charSpacing: 1.5, margin: 0, valign: 'middle', isTextBox: true } } },
    { rect: { x: 0, y: P(1074), w: P(1920), h: P(6), fill: { color: '4A5566' } } },
  ] });

// ---------------------------------------------------------------- utilitaires
let seq = 0;
const effectOf = (a, sid) => {
  if (!a) return null;
  let d = a.delay;
  // couverture : l'intro (logo construit par les machines, buse du 6, maquette dessinée) n'existe que dans la version
  // en ligne ; dans PowerPoint, le contenu arrive tout de suite, dans un ordre court
  if (sid === 'couverture') {
    if (a.delay === 10100) return { e: 'wipeB', d: 500, u: 1400 };         // le 6 s'imprime de bas en haut
    const map = { 8700: 0, 7900: 300, 10000: 1100 };                       // logo, « types d'ateliers », surtitre
    if (a.name === 'fade' && a.delay > 12000) d = 900;                     // maquette
    else if (map[a.delay] !== undefined) d = map[a.delay];
    else if (a.delay >= 10150 && a.delay < 11000) d = a.delay - 8900;      // puces 01 à 06
    else d = Math.max(0, d - 7500);
  }
  const u = Math.max(300, Math.min(a.dur || 600, 2400));
  if (['rise', 'fade', 'slidein', 'drop', 'spool', 'focus', 'cvSlide', 'cvZoom'].includes(a.name)) return { e: 'fade', d, u: 600 };
  if (a.name === 'grow' || a.name === 'rvxi' || a.name === 'rvxo') return { e: 'wipeL', d, u: a.name === 'grow' ? 900 : u };
  if (a.name === 'rvli' || a.name === 'rvlo') return { e: 'wipeR', d, u };
  if (a.name === 'rvyi' || a.name === 'rvyo') return { e: 'wipeT', d, u };
  if (['revi', 'revo', 'rvbi', 'rvbo'].includes(a.name)) return { e: 'wipeB', d, u: Math.min(u, 2000) };
  return null;
};
let SID = '';
const nameFor = (it, base) => { const f = effectOf(it.anim, SID); seq += 1; return f ? `an_${f.e}_${f.d}_${f.u}_${seq}` : `${base}_${seq}`; };
const shadowOf = (s) => { if (!s) return undefined; const m = s.match(/rgba?\(([^)]+)\)\s+([-\d.]+)px\s+([-\d.]+)px\s+([-\d.]+)px/); if (!m) return undefined;
  const p = m[1].split(',').map(x => x.trim()); const hex = p.slice(0, 3).map(n => (+n).toString(16).padStart(2, '0')).join('').toUpperCase();
  return { type: 'outer', color: hex, opacity: Math.min(0.2, (p[3] ? +p[3] : 1) * 1.6), blur: pt(+m[4]), offset: Math.max(0, pt(+m[3])), angle: 90 }; };
const runsToPptx = (it) => {
  const out = [];
  it.runs.forEach((r) => {
    if (r.br) { if (out.length) out[out.length - 1].options.breakLine = true; return; }
    const o = { color: col(r.color.hex), bold: r.weight >= 600 };
    out.push({ text: r.t, options: o });
  });
  return out;
};
const hatchFor = (w) => { const k = [76, 82, 152, 164].reduce((a, b) => Math.abs(b - w) < Math.abs(a - w) ? b : a); return `/home/claude/pptx/img/hatch${k}.png`; };

const SECTIONS = { couverture: 'Ouverture', visites: 'Types d’ateliers', modularite: 'Modularité et résumé' };
let section = null;
for (const s of L) {
  if (SECTIONS[s.id]) { section = SECTIONS[s.id]; pres.addSection({ title: section }); }
  SID = s.id;
  const has = (c) => new RegExp(`\\b${c}\\b`).test(s.cls);
  const master = s.id === 'couverture' ? 'DF Couverture' : has('grad') ? 'DF Dégradé'
    : has('dark') ? (has('foot') ? 'DF Sombre' : 'DF Sombre contenu') : has('tint') ? 'DF Contenu lavande' : 'DF Contenu';
  const slide = pres.addSlide({ masterName: master, sectionTitle: section });
  for (const it of s.items) {
    const cls = it.cls || '';
    // éléments portés par la disposition
    if (it.kind === 'box' && /\bprog\b/.test(cls)) continue;
    if (it.kind === 'box' && /\bsq\b/.test(cls) && Math.round(it.x) === 128 && s.id !== 'couverture' && (it.y < 170 || it.y > 900)) continue;
    if (it.kind === 'text' && /\bkicker\b/.test(cls) && it.y > 900) continue;
    if (it.kind === 'text' && /\bkicker\b/.test(cls) && it.y < 170) {
      slide.addText(it.runs.filter(r => !r.br).map(r => r.t).join(''), { placeholder: 'kicker', charSpacing: 1.5, align: 'left' });
      continue;
    }
    if (it.kind === 'text' && s.id === 'couverture' && it === covTitle) {
      slide.addText(runsToPptx(it), { placeholder: 'title', align: 'left' });
      continue;
    }
    if (it.kind === 'box' && it.bs.bg && it.bs.bg.hex === 'F4F5F7' && !(it.bs.bw > 0)) continue;
    if (it.kind === 'text' && (it.tag === 'h1' || /\btitle\b/.test(cls))) {
      slide.addText(runsToPptx(it), { placeholder: 'title', align: 'left' });
      continue;
    }
    if (it.kind === 'img') {
      slide.addImage({ path: `/home/claude/pptx/svg/${it.id}.png`, x: P(it.x), y: P(it.y), w: P(it.w), h: P(it.h),
        altText: it.label || '', objectName: nameFor(it, 'img') });
      continue;
    }
    if (it.kind === 'box') {
      const bs = it.bs;
      if (bs.bgImage && bs.bgImage.includes('repeating-linear-gradient')) {
        slide.addImage({ path: hatchFor(it.w), x: P(it.x), y: P(it.y), w: P(it.w), h: P(it.h), altText: 'Durée variable', objectName: nameFor(it, 'hatch') });
        continue;
      }
      if (bs.btop && !bs.bg) {
        slide.addShape(pres.shapes.LINE, { x: P(it.x), y: P(it.y), w: P(it.w), h: 0, line: { color: col(bs.bc.hex), width: Math.max(0.75, pt(bs.bw)) }, objectName: nameFor(it, 'line') });
        continue;
      }
      const r = Math.min(bs.radius, it.h / 2, it.w / 2);
      const opt = { x: P(it.x), y: P(it.y), w: P(it.w), h: P(it.h), objectName: nameFor(it, 'box') };
      if (bs.bg) opt.fill = bs.bg.a < 1 ? { color: col(bs.bg.hex), transparency: Math.round((1 - bs.bg.a) * 100) } : { color: col(bs.bg.hex) };
      else opt.fill = { color: 'FFFFFF', transparency: 100 };
      opt.line = bs.bw > 0 ? { color: col(bs.bc.hex), width: Math.max(0.75, pt(bs.bw)), dashType: bs.bstyle === 'dashed' ? 'dash' : 'solid' } : { type: 'none' };
      const sh = shadowOf(bs.shadow); if (sh) opt.shadow = sh;
      if (/\bsolid\b/.test(cls)) { opt.rectRadius = P(it.h / 2); slide.addShape(pres.shapes.ROUNDED_RECTANGLE, opt); continue; }
      if (r > 0.5) { opt.rectRadius = P(r); slide.addShape(pres.shapes.ROUNDED_RECTANGLE, opt); }
      else slide.addShape(pres.shapes.RECTANGLE, opt);
      continue;
    }
    if (it.kind === 'list') {
      const st = it.st; const paras = [];
      it.lis.forEach((li, k) => {
        const runs = li.runs.filter(r => !r.br && r.t);
        runs.forEach((r, j) => {
          const o = { color: col(r.color.hex), bold: r.weight >= 600 };
          if (j === 0) { o.bullet = { indent: pt(it.indent) }; o.paraSpaceBefore = k ? pt(it.gap) : 0; }
          if (j === runs.length - 1 && k < it.lis.length - 1) o.breakLine = true;
          paras.push({ text: r.t, options: o });
        });
      });
      slide.addText(paras, { fontSize: pt(st.size), lineSpacing: pt(st.lh), margin: 0, x: P(it.x), y: P(it.y), w: P(it.w + 12), h: P(it.h + 8),
        valign: 'top', isTextBox: true, fit: 'none', objectName: nameFor(it, 'list') });
      continue;
    }
    if (it.kind === 'text') {
      const st = it.st;
      const runs = runsToPptx(it);
      const base = { fontSize: pt(st.size), color: col(st.color.hex), bold: st.weight >= 600, charSpacing: st.ls ? pt(st.ls) : undefined,
        lineSpacing: pt(st.lh), margin: 0, paraSpaceBefore: 0, paraSpaceAfter: 0, objectName: nameFor(it, 'txt') };
      if (it.box) {
        const bs = it.box; const r = Math.min(bs.radius, it.h / 2);
        const o = { ...base, x: P(it.x), y: P(it.y), w: P(it.w), h: P(it.h), align: 'center', valign: 'middle',
          fill: bs.bg ? { color: col(bs.bg.hex) } : { color: 'FFFFFF', transparency: 100 },
          line: bs.bw > 0 ? { color: col(bs.bc.hex), width: Math.max(0.75, pt(bs.bw)), dashType: bs.bstyle === 'dashed' ? 'dash' : 'solid' } : { type: 'none' } };
        if (r > 0.5) { o.shape = pres.shapes.ROUNDED_RECTANGLE; o.rectRadius = P(r); } else o.shape = pres.shapes.RECTANGLE;
        slide.addText(runs, o);
        continue;
      }
      const align = st.align === 'right' || st.align === 'end' ? 'right' : st.align === 'center' ? 'center' : 'left';
      let x = it.x, w = it.w + 12;
      if (align === 'right') x = it.x - 12; else if (align === 'center') { x = it.x - 6; }
      slide.addText(runs, { ...base, x: P(x), y: P(it.y), w: P(w), h: P(it.h + 8), align, valign: 'top', isTextBox: true, fit: 'none' });
    }
  }
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log('écrit', OUT);
})();
