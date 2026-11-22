"""Construit la ROM traduite de CFC2 Expand Edition (et le patch IPS).

    python tools/build.py --rom "SNK vs. Capcom - Card Fighters 2 - Expand Edition (Japan).ngc" --lang fr [--ips]
    -> out/<lang>.ngc (+ out/<lang>.ips, vérifié en le réappliquant)

- ROM JP 2 Mio + 2 Mio (puce 2, CPU 0x800000) : code VWF 0x800000, FONT 0x800400, LARG 0x800C00,
  EXPAND 0x800D00, textes traduits à partir de 0x801000.
- Traductions : lang/<lang>/lot_*.tsv, « index<TAB>texte » (\\n = ligne, codes entre accolades, voir
  encode()) ; lot_25* = noms des cartes (« carte<TAB>nom<TAB>capacité »). Lignes # ignorées.
- Code ajouté : tools/asm/vwf.asm, livré assemblé (vwf.bin). Pour le modifier : Macro Assembler AS
  (asl, p2bin), dossier indiqué par la variable d'environnement ASL_DIR.
"""
import argparse, glob, os, sys, subprocess
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import police  # noqa: E402
import forme  # noqa: E402
import graphismes  # noqa: E402
import plaques  # noqa: E402
import cartes  # noqa: E402
import logo  # noqa: E402
import rom_jp  # noqa: E402
import ips  # noqa: E402

TABLE = 0xE0000
NB = 6250
PUCE2 = 0x200000           # fichier ; CPU = 0x800000
SITES_VWF = (0x2060A8, 0x206181, 0x2063D0, 0x206456, 0x2065A5)


def assemble(nom):
    """asm/<nom>.bin livré ; réassemblé depuis asm/<nom>.asm si ASL_DIR est défini."""
    d = os.path.join(ICI, 'asm')
    asl = os.environ.get('ASL_DIR')
    if asl:
        x = '.exe' if os.name == 'nt' else ''
        subprocess.run([os.path.join(asl, 'asl' + x), '-cpu', '96C141', '-q', '-L', nom + '.asm'], cwd=d,
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run([os.path.join(asl, 'p2bin' + x), nom + '.p', nom + '.bin'], cwd=d, check=True,
                       stdout=subprocess.DEVNULL)
    return open(os.path.join(d, nom + '.bin'), 'rb').read()


def pose(rom, adr, avant, apres):
    a, b = bytes.fromhex(avant), bytes.fromhex(apres)
    o = adr - 0x200000 if adr >= 0x200000 else adr
    if rom[o:o + len(a)] != a:
        raise SystemExit('octets inattendus en %06X : %s (attendu %s)' % (adr, rom[o:o + len(a)].hex(), avant))
    rom[o:o + len(b)] = b


def call(adr):
    return '1d' + adr.to_bytes(3, 'little').hex()


def encode(texte):
    """Texte FR -> octets. \\n -> 0B ; {M a b c d} -> 0E a b c d ; {I ...} -> octets ;
    {1EC} (3 chiffres) -> glyphe préfixé 01 EC ; {08 02} / {0C} -> octets bruts."""
    out = bytearray()
    i = 0
    while i < len(texte):
        c = texte[i]
        if c == '\\' and texte[i + 1:i + 2] == 'n':
            out.append(0x0B); i += 2; continue
        if c == '{':
            j = texte.index('}', i)
            corps = texte[i + 1:j].split()
            if corps[0] == 'M':
                out.append(0x0E); out += bytes(int(h, 16) for h in corps[1:])
            elif corps[0] == 'I':
                out += bytes(int(h, 16) for h in corps[1:])
            elif len(corps) == 1 and len(corps[0]) == 3:
                k = int(corps[0], 16); out += bytes([k >> 8, k & 0xFF])
            else:
                out += bytes(int(h, 16) for h in corps)
            i = j + 1
            continue
        out.append(0x40 if c == '@' else police.code_de(c))
        i += 1
    return bytes(out) + b'\x00'


def lit_trad(fichiers):
    t = {}
    for f in fichiers:
        for ln in open(f, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if not ln or ln.startswith('#'):
                continue
            p = ln.split('\t')
            t[int(p[0])] = p[1]
    return t


def base_rom(jp):
    rom = bytearray(jp) + bytearray(b'\xff' * 0x200000)
    code = assemble('vwf')
    rom[PUCE2:PUCE2 + len(code)] = code
    font, larg, expand = police.construit(jp)
    rom[PUCE2 + 0x400:PUCE2 + 0xC00] = font
    rom[PUCE2 + 0xC00:PUCE2 + 0xD00] = larg
    rom[PUCE2 + 0xD00:PUCE2 + 0xF00] = expand
    police.police_2bpp(rom)
    INIT, VWF, MONOCALL = 0x800000, 0x800004, 0x800008      # sauts en tête de vwf.asm
    pose(rom, 0x247979, call(0x205FE2), call(MONOCALL))       # grille du clavier : cases de 8 px
    pose(rom, 0x24789A, call(0x200919), call(0x80000C))       # 1er affichage de la grille
    pose(rom, 0x25097B, call(0x205FE2), call(MONOCALL))       # champ du nom (curseur par case)
    pose(rom, 0x205FE8, 'd7ee9bd9ccff01', call(INIT) + '000000')
    for s in SITES_VWF:
        o = s - 0x200000
        avant = rom[o:o + 11].hex()
        assert avant.startswith('d7e2881dcc5924'), (hex(s), avant)
        # call VWF ; jr +5 (après les inc d'origine, gardés pour d'éventuels sauts)
        pose(rom, s, avant[:14], call(VWF) + '6805' + '00')
    # plaques de lieu des décors (tuiles ajoutées éventuelles en puce 2, zone 0x380000+)
    zone = Zone(rom, 0x380000, 0x3F0000)
    plaques.plaques(rom, jp, font, larg, zone)
    plaques.autonomes(rom, font, larg)
    graphismes.boutons(rom, font, larg)
    graphismes.bandeaux(rom, font, larg)
    graphismes.bulles(rom, font, larg)
    graphismes.titre(rom, font, larg)
    logo.logo(rom)                          # logo « CARD FIGHTERS » (écran-titre)
    graphismes.tutoriel(rom, font, larg, jp)
    graphismes.pv_duel(rom)
    graphismes.pv_terrain(rom)
    graphismes.enseigne_joyjoy(rom)
    graphismes.debut_duel(rom, font, larg, jp)
    # choix Oui/Non du code {0C}/{0D} : chaînes codées en dur (« はい » col. 5 / « いいえ » col. 10,
    # puis col. 2 / col. 7) -> chaînes FR en puce 2, les deux « lda XIZ,(…) » redirigés
    for site, ancien, txt in ((0x206163, 0x206199, '@@@@@Oui@@@Non'), (0x206173, 0x2061A7, '@@Oui@@@Non')):
        a = zone.met(encode(txt))
        pose(rom, site, 'f2' + ancien.to_bytes(3, 'little').hex() + '36', 'f2' + a.to_bytes(3, 'little').hex() + '36')
    return rom


class Zone:
    """Allocation linéaire dans la puce 2 (adresses fichier) ; met() renvoie l'adresse CPU."""
    def __init__(self, rom, debut, fin):
        self.rom, self.p, self.fin = rom, debut, fin

    def met(self, octets, align=2):
        self.p = (self.p + align - 1) & ~(align - 1)
        assert self.p + len(octets) <= self.fin, 'zone pleine'
        a = self.p
        self.rom[a:a + len(octets)] = octets
        self.p += len(octets)
        return a - PUCE2 + 0x800000


CLAVIER = {
    # page : (adresse fichier, nombre de grilles (1 = caractères, + table ゛, + table ゜), lignes FR)
    1: (0x47A56, 3, ['ABCDEFGHIJKLMNOPQ', 'RSTUVWXYZ@ÀÂÇÉÈÊË', 'ÎÔÙÛŒ@@-.\'!?&@@@@', '@@@@@@@@@@@@@@@@@']),
    2: (0x47B3C, 3, ['abcdefghijklmnopq', 'rstuvwxyz@àâçéèêë', 'îïôùûüœ@-.\'!?&@@@', '@@@@@@@@@@@@@@@@@']),
}


def clavier(rom):
    """Pages de saisie du nom : hiragana -> majuscules, katakana -> minuscules ; tables ゛゜ vidées.
    La page 3 (ABC, chiffres, symboles) reste celle d'origine."""
    for page, (adr, ngr, lignes) in CLAVIER.items():
        p = adr
        assert rom[p:p + 1] != b'\x00'
        for g in range(ngr):
            for r in range(4):
                if g == 0:
                    l = lignes[r]
                    assert len(l) == 17, l
                    b = bytes(0x40 if c == '@' else police.code_de(c) for c in l)   # @ = case vide
                else:
                    b = b'\x40' * 17
                assert rom[p + 17] == (0x0B if r < 3 else 0x00), (page, g, r, hex(p))
                rom[p:p + 17] = b
                p += 18


def main():
    ap = argparse.ArgumentParser(description='Construit la ROM traduite et le patch IPS.')
    ap.add_argument('--rom', required=True, help="ROM japonaise d'origine")
    ap.add_argument('--lang', default='fr', help='dossier lang/<code>')
    ap.add_argument('--ips', action='store_true', help='fabrique aussi out/<code>.ips')
    a = ap.parse_args()
    jp = rom_jp.charge(a.rom)
    forme.init(jp)
    fichiers = sorted(glob.glob(os.path.join(os.path.dirname(ICI), 'lang', a.lang, 'lot_*.tsv')))
    if not fichiers:
        raise SystemExit('aucun fichier lang/%s/lot_*.tsv' % a.lang)
    rom = base_rom(jp)
    clavier(rom)
    graphismes.etiquette_nom(rom)
    graphismes.glyphe_pv(rom)
    noms = [f for f in fichiers if os.path.basename(f).startswith('lot_25')]
    trad = lit_trad([f for f in fichiers if f not in noms])
    for f in noms:
        print('noms de cartes :', cartes.ecrit_noms(rom, f))
    types = {i: t for i, (t, _) in rom_jp.source(jp).items()}
    NLx = chr(92) + 'n'
    p = PUCE2 + 0x1000
    for idx, txt in sorted(trad.items()):
        if types.get(idx) == 'D' or '¶' in txt:
            txt = forme.dialogue(txt)
        elif 3100 <= idx <= 3199:          # pages du lexique : le jeu coupe au nombre de tuiles -> on coupe aux mots
            lignes = []
            for l in txt.split(NLx):
                lignes += forme.coupe(l, 136) if forme.px(l) > 136 else [l]
            txt = NLx.join(lignes)
        b = encode(txt)
        rom[p:p + len(b)] = b
        rom[TABLE + idx * 4:TABLE + idx * 4 + 4] = (p - PUCE2 + 0x800000).to_bytes(4, 'little')
        p += len(b)
    os.makedirs('out', exist_ok=True)
    sortie = os.path.join('out', a.lang + '.ngc')
    open(sortie + '.tmp', 'wb').write(rom)
    os.replace(sortie + '.tmp', sortie)
    print(sortie, len(trad), 'textes,', hex(p), 'utilisé')
    if a.ips:
        ips.ecrit(jp, bytes(rom), os.path.join('out', a.lang + '.ips'))


if __name__ == '__main__':
    main()
