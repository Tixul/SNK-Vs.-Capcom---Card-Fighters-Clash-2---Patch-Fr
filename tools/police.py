"""Police française de CFC2 (dessins repris du patch Party Mail, même auteur).

Encodage FR (1 octet) : 0x20-0x7E = ASCII (0x40 '@' = case vide d'une tuile entière, alignement) ;
0x80.. = accents et signes (ACCENTS) ; codes >= 0x100 (icônes, boutons) écrits {1EC} dans le texte.

Sorties :
  construit() -> FONT (256 x 8 octets 1 bpp, bit 7 = colonne de gauche), LARG (256 avances),
                 EXPAND (256 mots : 1 bit -> 2 bits « 11 », pixel 0 en bits 15-14)
  police_2bpp(rom) : réécrit dans la police d'origine (0x8D00C + code*16, fond 1 / encre 3) les
                 codes 0x21-0xFF en chasse fixe, pour les routines d'affichage non converties.
Lignes : 0 = accent des capitales, 1-6 = capitales / chiffres, 3-6 = minuscules, 7 = jambage.
"""
POLICE_JP = 0x8D00C

ACCENTS = 'éèêëàâîïôûùüçœÉÈÊÀÇÔÎ«»…~ËŒÙÛÂ'
CODE_ACCENT = {c: 0x80 + i for i, c in enumerate(ACCENTS)}
# glyphes d'origine gardés tels quels (rognés) : 「 」 et le « vs »
GARDES = {'「': 0x22, '」': 0x23}

G = {}


def _g(c, *lignes, haut=1):
    rows = ['' for _ in range(8)]
    for i, l in enumerate(lignes):
        rows[haut + i] = l
    G[c] = rows


# --- capitales (lignes 1-6) ---
_g('A', '.##.', '#..#', '#..#', '####', '#..#', '#..#')
_g('B', '###.', '#..#', '###.', '#..#', '#..#', '###.')
_g('C', '.###', '#...', '#...', '#...', '#...', '.###')
_g('D', '###.', '#..#', '#..#', '#..#', '#..#', '###.')
_g('E', '####', '#...', '###.', '#...', '#...', '####')
_g('F', '####', '#...', '###.', '#...', '#...', '#...')
_g('G', '.###', '#...', '#...', '#.##', '#..#', '.###')
_g('H', '#..#', '#..#', '####', '#..#', '#..#', '#..#')
_g('I', '###', '.#.', '.#.', '.#.', '.#.', '###')
_g('J', '..##', '...#', '...#', '...#', '#..#', '.##.')
_g('K', '#..#', '#.#.', '##..', '#.#.', '#..#', '#..#')
_g('L', '#...', '#...', '#...', '#...', '#...', '####')
_g('M', '#...#', '##.##', '#.#.#', '#...#', '#...#', '#...#')
_g('N', '#..#', '##.#', '#.##', '#..#', '#..#', '#..#')
_g('O', '.##.', '#..#', '#..#', '#..#', '#..#', '.##.')
_g('P', '###.', '#..#', '#..#', '###.', '#...', '#...')
_g('Q', '.##.', '#..#', '#..#', '#..#', '#.#.', '.#.#')
_g('R', '###.', '#..#', '#..#', '###.', '#.#.', '#..#')
_g('S', '.###', '#...', '.##.', '...#', '...#', '###.')
_g('T', '###', '.#.', '.#.', '.#.', '.#.', '.#.')
_g('U', '#..#', '#..#', '#..#', '#..#', '#..#', '.##.')
_g('V', '#...#', '#...#', '#...#', '.#.#.', '.#.#.', '..#..')
_g('W', '#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#')
_g('X', '#..#', '#..#', '.##.', '.##.', '#..#', '#..#')
_g('Y', '#.#', '#.#', '#.#', '.#.', '.#.', '.#.')
_g('Z', '####', '...#', '..#.', '.#..', '#...', '####')
# --- minuscules (x = lignes 3-6) ---
_g('a', '.###', '#..#', '#..#', '.###', haut=3)
_g('b', '#...', '#...', '###.', '#..#', '#..#', '###.')
_g('c', '.##', '#..', '#..', '.##', haut=3)
_g('d', '...#', '...#', '.###', '#..#', '#..#', '.###')
_g('e', '.##.', '####', '#...', '.###', haut=3)
_g('f', '.##', '#..', '###', '#..', '#..', '#..')
_g('g', '.###', '#..#', '.###', '...#', '###.', haut=3)
_g('h', '#...', '#...', '###.', '#..#', '#..#', '#..#')
_g('i', '#', '.', '#', '#', '#', '#')
_g('j', '.#', '..', '.#', '.#', '.#', '.#', '#.')
_g('k', '#..', '#..', '#.#', '##.', '#.#', '#.#')
_g('l', '#', '#', '#', '#', '#', '#')
_g('m', '##.#.', '#.#.#', '#.#.#', '#.#.#', haut=3)
_g('n', '###.', '#..#', '#..#', '#..#', haut=3)
_g('o', '.##.', '#..#', '#..#', '.##.', haut=3)
_g('p', '###.', '#..#', '###.', '#...', '#...', haut=3)
_g('q', '.###', '#..#', '.###', '...#', '...#', haut=3)
_g('r', '#.#', '##.', '#..', '#..', haut=3)
_g('s', '.###', '##..', '..##', '###.', haut=3)
_g('t', '#..', '###', '#..', '#..', '.##', haut=2)
_g('u', '#..#', '#..#', '#..#', '.###', haut=3)
_g('v', '#.#', '#.#', '#.#', '.#.', haut=3)
_g('w', '#...#', '#.#.#', '#.#.#', '.#.#.', haut=3)
_g('x', '#..#', '.##.', '.##.', '#..#', haut=3)
_g('y', '#..#', '#..#', '.###', '...#', '###.', haut=3)
_g('z', '####', '..#.', '.#..', '####', haut=3)
# --- chiffres ---
_g('0', '.##.', '#..#', '#..#', '#..#', '#..#', '.##.')
_g('1', '.#.', '##.', '.#.', '.#.', '.#.', '###')
_g('2', '.##.', '#..#', '..#.', '.#..', '#...', '####')
_g('3', '###.', '...#', '.##.', '...#', '...#', '###.')
_g('4', '..#.', '.##.', '#.#.', '####', '..#.', '..#.')
_g('5', '####', '#...', '###.', '...#', '...#', '###.')
_g('6', '.##.', '#...', '###.', '#..#', '#..#', '.##.')
_g('7', '####', '...#', '..#.', '.#..', '.#..', '.#..')
_g('8', '.##.', '#..#', '.##.', '#..#', '#..#', '.##.')
_g('9', '.##.', '#..#', '#..#', '.###', '...#', '.##.')
# --- ponctuation ---
_g('!', '#', '#', '#', '#', '.', '#')
_g('?', '.##.', '#..#', '..#.', '.#..', '....', '.#..')
_g('.', '#', haut=6)
_g(',', '.#', '#.', haut=6)
_g(':', '#', '.', '.', '#', haut=3)
_g(';', '.#', '..', '..', '.#', '#.', haut=3)
_g("'", '#', '#', haut=1)
_g('-', '###', haut=4)
_g('(', '.#', '#.', '#.', '#.', '#.', '.#')
_g(')', '#.', '.#', '.#', '.#', '.#', '#.')
_g('/', '..#', '..#', '.#.', '.#.', '#..', '#..')
_g('+', '.#.', '###', '.#.', haut=3)
_g('=', '###', '...', '###', haut=3)
_g('%', '#..#', '...#', '..#.', '.#..', '#...', '#..#')
_g('&', '.#..', '#.#.', '.#..', '#.##', '#..#', '.##.')
_g('*', '#.#', '.#.', '#.#', haut=2)
_g('"', '#.#', '#.#', haut=1)
_g('<', '..#', '.#.', '#..', '.#.', '..#', haut=2)
_g('>', '#..', '.#.', '..#', '.#.', '#..', haut=2)
_g('[', '##', '#.', '#.', '#.', '#.', '##')
_g(']', '##', '.#', '.#', '.#', '.#', '##')
_g('_', '####', haut=7)
_g('#', '.#.#', '####', '.#.#', '####', '.#.#', haut=1)
_g('«', '.#.#', '#.#.', '.#.#', haut=3)
_g('»', '#.#.', '.#.#', '#.#.', haut=3)
_g('…', '#.#.#', haut=6)
_g('~', '.#.#', '#.#.', haut=3)


def _acc(c, base, accent, ligne=1):
    rows = list(G[base])
    w = max(len(r) for r in rows)
    for i, l in enumerate(accent):
        rows[ligne + i] = l.ljust(w, '.')
    G[c] = rows


AIGU, GRAVE, CIRC, TREMA = ['..#.', '.#..'], ['.#..', '..#.'], ['.##.', '#..#'], ['....', '#..#']
_acc('é', 'e', AIGU); _acc('è', 'e', GRAVE); _acc('ê', 'e', CIRC); _acc('ë', 'e', TREMA)
_acc('à', 'a', GRAVE); _acc('â', 'a', CIRC)
_acc('ô', 'o', CIRC); _acc('û', 'u', CIRC); _acc('ù', 'u', GRAVE); _acc('ü', 'u', TREMA)
G['î'] = ['', '.#.', '#.#', '.#.', '.#.', '.#.', '.#.', '']
G['ï'] = ['', '', '#.#', '.#.', '.#.', '.#.', '.#.', '']
G['ç'] = ['', '', '', '.##', '#..', '#..', '.##', '.#.']
G['œ'] = ['', '', '', '.#.##.', '#.####', '#.#...', '.#.###', '']
G['É'] = ['..#.'] + G['E'][1:]
G['È'] = ['.#..'] + G['E'][1:]
G['Ê'] = ['.##.'] + G['E'][1:]
G['Ë'] = ['#..#'] + G['E'][1:]
G['À'] = ['.#..'] + G['A'][1:]
G['Â'] = ['.##.'] + G['A'][1:]
G['Ô'] = ['.##.'] + G['O'][1:]
G['Î'] = ['.#.'] + G['I'][1:]
G['Ù'] = ['.#..'] + G['U'][1:]
G['Û'] = ['.##.'] + G['U'][1:]
G['Ç'] = G['C'][:7] + ['.#..']
G['Œ'] = ['', '.#####', '#.#...', '#.###.', '#.#...', '#.#...', '.#####', '']

ESPACE = 3


def code_de(c):
    if c in CODE_ACCENT:
        return CODE_ACCENT[c]
    if c in GARDES:
        return GARDES[c]
    if c == ' ':
        return 0x20
    o = ord(c)
    if 0x21 <= o <= 0x7E and c != '@':
        return o
    raise KeyError(c)


def _glyphe_jp(rom, code):
    b = rom[POLICE_JP + code * 16: POLICE_JP + code * 16 + 16]
    rows = []
    for y in range(8):
        w = b[2 * y] | b[2 * y + 1] << 8
        rows.append(''.join('#' if (w >> (14 - 2 * x)) & 2 else '.' for x in range(8)))
    return rows


def _rogne(rows):
    cols = [x for x in range(8) if any(len(r) > x and r[x] == '#' for r in rows)]
    if not cols:
        return ['' for _ in rows], 0
    a, b = min(cols), max(cols)
    return [r[a:b + 1] if len(r) > a else '' for r in rows], b - a + 1


def construit(rom):
    """rom = ROM japonaise (police d'origine pour les codes non redessinés)."""
    font = bytearray(256 * 8)
    larg = bytearray(256)
    for code in range(0x20, 0x60):
        rows, w = _rogne(_glyphe_jp(rom, code))
        for y, r in enumerate(rows):
            v = 0
            for x, ch in enumerate(r[:8]):
                if ch == '#':
                    v |= 0x80 >> x
            font[code * 8 + y] = v
        larg[code] = w + 1 if w else ESPACE
    for c, rows in G.items():
        code = code_de(c)
        w = max(len(r) for r in rows)
        for y in range(8):
            v = 0
            for x, ch in enumerate(rows[y] if y < len(rows) else ''):
                if ch == '#':
                    v |= 0x80 >> x
            font[code * 8 + y] = v
        larg[code] = w + 1
    larg[0x20] = ESPACE
    larg[0x40] = 8
    expand = bytearray()
    for v in range(256):
        m = 0
        for x in range(8):
            if v & (0x80 >> x):
                m |= 3 << (14 - 2 * x)
        expand += m.to_bytes(2, 'little')
    return bytes(font), bytes(larg), bytes(expand)


def police_2bpp(rom):
    """Copie des glyphes FR en chasse fixe dans la police d'origine (fond 1, encre 3), centrés."""
    for c, rows in G.items():
        code = code_de(c)
        if code in (0x22, 0x23):
            continue
        w = max(len(r) for r in rows)
        dx = max(0, (8 - w) // 2)
        b = bytearray()
        for y in range(8):
            r = rows[y] if y < len(rows) else ''
            v = 0
            for x in range(8):
                ink = 0 <= x - dx < len(r) and r[x - dx] == '#'
                v |= (3 if ink else 1) << (14 - 2 * x)
            b += v.to_bytes(2, 'little')
        rom[POLICE_JP + code * 16: POLICE_JP + code * 16 + 16] = b


def largeur(octets, larg):
    """Largeur en pixels d'une ligne encodée (codes {1xx} = 8 px, en tuile entière)."""
    w = 0
    i = 0
    while i < len(octets):
        c = octets[i]
        if 1 <= c <= 7:
            w = (w + 7) // 8 * 8 + 8
            i += 2
            continue
        if c == 0x40:
            w = (w + 7) // 8 * 8 + 8
        else:
            w += larg[c]
        i += 1
    return w

