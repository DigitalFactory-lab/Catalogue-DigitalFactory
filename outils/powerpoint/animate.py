"""Ajoute transitions et animations d'entrée (fondu, balayage) au PowerPoint généré."""
import re, sys, zipfile, shutil, os
SRC, DST = sys.argv[1], sys.argv[2]
EFFECTS = {
    'fade':  ('10', '0', 'fade'),
    'wipeL': ('22', '8', 'wipe(right)'),
    'wipeB': ('22', '4', 'wipe(up)'),
    'wipeR': ('22', '2', 'wipe(left)'),
    'wipeT': ('22', '1', 'wipe(down)'),
}
def timing(shapes):
    cid = [4]
    def nid():
        cid[0] += 1; return cid[0]
    effects = []
    for k, (spid, eff, delay, dur, is_sp) in enumerate(shapes):
        pid, sub, filt = EFFECTS[eff]
        node = 'afterEffect' if k == 0 else 'withEffect'
        a, b, c = nid(), nid(), nid()
        effects.append(
            f'<p:par><p:cTn id="{a}" presetID="{pid}" presetClass="entr" presetSubtype="{sub}" fill="hold" grpId="0" nodeType="{node}">'
            f'<p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>'
            f'<p:set><p:cBhvr><p:cTn id="{b}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:to><p:strVal val="visible"/></p:to></p:set>'
            f'<p:animEffect transition="in" filter="{filt}"><p:cBhvr><p:cTn id="{c}" dur="{dur}"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>'
            f'</p:childTnLst></p:cTn></p:par>')
    bld = ''.join(f'<p:bldP spid="{s[0]}" grpId="0" animBg="1"/>' for s in shapes if s[4])
    return (
        '<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
        '<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
        '<p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>'
        '<p:par><p:cTn id="4" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
        + ''.join(effects) +
        '</p:childTnLst></p:cTn></p:par>'
        '</p:childTnLst></p:cTn></p:par>'
        '</p:childTnLst></p:cTn>'
        '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
        '</p:childTnLst></p:cTn></p:par></p:tnLst>'
        + (f'<p:bldLst>{bld}</p:bldLst>' if bld else '') +
        '</p:timing>')

zin = zipfile.ZipFile(SRC)
tmp = DST + '.tmp'
zout = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    m = re.fullmatch(r'ppt/slides/slide(\d+)\.xml', item.filename)
    if m:
        n = int(m.group(1))
        x = data.decode('utf-8')
        shapes = []
        for mm in re.finditer(r'<p:(nvSpPr|nvPicPr|nvCxnSpPr)><p:cNvPr id="(\d+)" name="an_(fade|wipeL|wipeB|wipeR|wipeT)_(\d+)_(\d+)_\d+"', x):
            shapes.append((mm.group(2), mm.group(3), int(mm.group(4)), int(mm.group(5)), mm.group(1) == 'nvSpPr'))
        shapes.sort(key=lambda s: (s[2], int(s[0])))
        add = ''
        if n > 1:
            add += '<p:transition spd="med"><p:push dir="l"/></p:transition>'
        if shapes:
            add += timing(shapes)
        # puces dans la couleur bleue de la charte (accent1 = #5B60A8)
        x = x.replace('<a:buSzPct val="100000"/><a:buChar', '<a:buClr><a:schemeClr val="accent1"/></a:buClr><a:buSzPct val="100000"/><a:buChar')
        assert x.count('</p:clrMapOvr>') == 1
        x = x.replace('</p:clrMapOvr>', '</p:clrMapOvr>' + add)
        data = x.encode('utf-8')
        print(f'slide{n}: {len(shapes)} animations')
    zout.writestr(item, data)
zout.close(); zin.close()
shutil.move(tmp, DST)
