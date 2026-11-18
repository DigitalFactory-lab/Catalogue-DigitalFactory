const sharp = require('/opt/npm-tools/node_modules/sharp');
const fs = require('fs'); const path = require('path');
const dir = '/home/claude/pptx/svg';
// fond en dégradé de la charte (bleu foncé → bleu → violet, 120°), pour la diapositive Modularité
const GRAD = '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"><defs><linearGradient id="g" gradientUnits="userSpaceOnUse" ' +
  'x1="6.2" y1="-10.7" x2="1913.8" y2="1090.7"><stop offset="0" stop-color="#2f3a48"/><stop offset=".62" stop-color="#5b60a8"/>' +
  '<stop offset="1" stop-color="#8c4292"/></linearGradient></defs><rect width="1920" height="1080" fill="url(#g)"/></svg>';
(async () => { await sharp(Buffer.from(GRAD)).png().toFile('/home/claude/pptx/img/grad.png');
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.svg'))) {
  await sharp(fs.readFileSync(path.join(dir, f)), { density: 216 }).png().toFile(path.join(dir, f.replace('.svg', '.png'))); }
  console.log(fs.readdirSync(dir).filter(f => f.endsWith('.png')).length, 'png'); })();
