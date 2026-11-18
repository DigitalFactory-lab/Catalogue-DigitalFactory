const sharp = require('/opt/npm-tools/node_modules/sharp');
const fs = require('fs'); const path = require('path');
const dir = '/home/claude/pptx/svg';
(async () => { for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.svg'))) {
  await sharp(fs.readFileSync(path.join(dir, f)), { density: 216 }).png().toFile(path.join(dir, f.replace('.svg', '.png'))); }
  console.log(fs.readdirSync(dir).filter(f => f.endsWith('.png')).length, 'png'); })();
