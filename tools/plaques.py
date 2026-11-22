"""Plaques de lieu peintes dans les décors (tools/decors.py) : texte japonais -> français.

Plaque = rangées de tuiles 1-2, colonnes 1-8 de l'image (bord couleur 2 en x=9/70, y=9/22).
Zone de texte réécrite : x 10..69, y 11..20 ; fond refait selon le motif de la plaque
(y<=14 : couleur 1 ; y=15/17 : damier 3/1 ; y=16 : damier 1/3 ; y>=18 : couleur 3) ; texte couleur 2
avec la police FR (ligne 0 du glyphe en y=12).
Tuiles : une case de la plaque reçoit une tuile propre ; on réutilise d'abord les tuiles qui ne servent
qu'à la plaque, puis on ajoute des tuiles (le bloc de tuiles est alors recopié sur la puce 2 et
l'enregistrement mis à jour). Limite VRAM : 0x118 + n <= 0x200.
"""
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import decors, police  # noqa: E402

TEXTES = {0: 'École CF', 1: 'Club de cartes', 2: 'Direction', 3: "Toit de l'école", 4: 'Parc Joyful',
          5: 'Joy Joy', 6: 'Lost World', 7: 'Vanguard', 8: 'Le CP', 9: 'Église Rooster', 10: 'MV Land',
          11: 'Powered Lab', 12: 'Repaire C.O.F', 14: 'Salle de duel'}
X0, X1, Y0, Y1 = 10, 69, 11, 20
MAXN = 0x200 - 0x118
u = decors.u


def fond(x, y):
    if y <= 14:
        return 1
    if y in (15, 17):
        return 3 if x % 2 == 0 else 1
    if y == 16:
        return 1 if x % 2 == 0 else 3
    return 3


def tuile_pix(d, tiles, t):
    g = d[tiles + t * 16:tiles + t * 16 + 16]
    return [[((g[2 * y] | g[2 * y + 1] << 8) >> (14 - 2 * x)) & 3 for x in range(8)] for y in range(8)]


def tuile_oct(p):
    b = bytearray()
    for y in range(8):
        w = 0
        for x in range(8):
            w |= p[y][x] << (14 - 2 * x)
        b += w.to_bytes(2, 'little')
    return bytes(b)


def largeur(txt, font, larg):
    return sum(larg[police.code_de(c)] for c in txt) - 1


def traite(rom, src, r, txt, font, larg, zone):
    w = r['w']
    M = [u(src, r['carte'] + k * 2, 2) for k in range(w * r['h'])]
    n = r['n']
    tiles = [src[r['tuiles'] + t * 16:r['tuiles'] + t * 16 + 16] for t in range(n)]
    # pixels de la plaque (cases rangées 1-2, colonnes 1-8)
    P = [(row, c) for row in (1, 2) for c in range(1, 9)]
    for row, c in P:
        assert M[row * w + c] >> 14 == 0, 'miroir dans la plaque'
    pix = {}
    for row, c in P:
        tp = tuile_pix(src, r['tuiles'], M[row * w + c] & 0x1FF)
        for y in range(8):
            for x in range(8):
                pix[(c * 8 + x, row * 8 + y)] = tp[y][x]
    assert pix[(9, 12)] == 2 and pix[(70, 12)] == 2, 'bord de plaque inattendu'
    for x in range(X0, X1 + 1):
        for y in range(Y0, Y1 + 1):
            pix[(x, y)] = fond(x, y)
    L = largeur(txt, font, larg)
    assert L <= X1 - X0 + 1, (txt, L)
    x = X0 + (X1 - X0 + 1 - L) // 2
    for ch in txt:
        k = police.code_de(ch)
        for gy in range(8):
            v = font[k * 8 + gy]
            for gx in range(8):
                if v & (0x80 >> gx):
                    pix[(x + gx, 12 + gy)] = 2
        x += larg[k]
    # tuiles libres : utilisées seulement dans la plaque
    hors = set(M[k] & 0x1FF for k in range(len(M)) if (k // w, k % w) not in P)
    libres = sorted(set(M[row * w + c] & 0x1FF for row, c in P) - hors)
    index = {bytes(t): i for i, t in enumerate(tiles) if i in hors}
    for row, c in P:
        b = tuile_oct([[pix[(c * 8 + xx, row * 8 + yy)] for xx in range(8)] for yy in range(8)])
        if b in index:
            t = index[b]
        elif libres:
            t = libres.pop(0); tiles[t] = b; index[b] = t
        else:
            t = len(tiles); tiles.append(b); index[b] = t
        k = row * w + c
        M[k] = (M[k] & ~0x1FF) | t
    assert len(tiles) <= MAXN, (txt, len(tiles))
    for k, mw in enumerate(M):
        rom[r['carte'] + k * 2:r['carte'] + k * 2 + 2] = mw.to_bytes(2, 'little')
    data = b''.join(tiles)
    if len(tiles) == n:
        rom[r['tuiles']:r['tuiles'] + len(data)] = data
    else:
        a = zone.met(data)
        rom[r['adr'] + 4:r['adr'] + 8] = a.to_bytes(4, 'little')
        rom[r['adr'] + 12:r['adr'] + 14] = len(tiles).to_bytes(2, 'little')
    return len(tiles) - n


# Plaques de lieu « autonomes » (images 8x2 de la table 0x9AC40) : même dessin, décalé de -8/-8.
AUTONOMES = {0xBDBFA: 'École CF', 0xC2FB3: 'Club de cartes', 0xBD8A8: 'Direction', 0xBE6E4: "Toit de l'école",
             0xBE7E2: 'Parc Joyful', 0xBE5E6: 'Joy Joy', 0xBE4E8: 'Lost World', 0xBE3EA: 'Vanguard',
             0xBE2EC: 'Le CP', 0xBE1EE: 'Église Rooster', 0xBE0F0: 'MV Land', 0xBDFF2: 'Powered Lab',
             0xBDEF4: 'Repaire C.O.F'}
# Plaques de noms (images 6x2) : texte couleur 3 + ombre 2 à droite sur fond 1, intérieur x 2..45, y 2..10.
NOMS = {0xBEDC2: 'Rikuto', 0xBF23D: 'Haruna', 0xC093F: 'Lip', 0xA0196: 'Torawo', 0xA09FC: 'Asou',
        0xC0D7E: 'Dogou', 0xD8FFC: 'Fuwa', 0xC8BA9: 'Yashichi', 0xC3A72: 'Kido', 0xD5F93: 'Fou',
        0xBB209: 'Shin', 0xC1E56: 'Kei', 0xDA861: 'Cap', 0xC6A5D: 'Comet', 0xC6F07: 'Neomanto',
        0xC7F3D: 'Nanako', 0xC962B: 'Robomanto', 0xC9A31: 'Sys', 0xCA5A8: 'G. Lady', 0xCC064: 'Zet'}


def _bloc(rom, a, nc, nr):
    p = {}
    for k in range(nc * nr):
        c, r = k % nc, k // nc
        tp = tuile_pix(rom, a + k * 16, 0)
        for y in range(8):
            for x in range(8):
                p[(c * 8 + x, r * 8 + y)] = tp[y][x]
    return p


def _ecrit(rom, a, p, nc, nr):
    for k in range(nc * nr):
        c, r = k % nc, k // nc
        rom[a + k * 16:a + k * 16 + 16] = tuile_oct([[p[(c * 8 + x, r * 8 + y)] for x in range(8)] for y in range(8)])


def _texte(p, txt, font, larg, x0, x1, ytop, couleur, ombre=None):
    L = largeur(txt, font, larg)
    assert L <= x1 - x0 + 1, (txt, L)
    x = x0 + (x1 - x0 + 1 - L) // 2
    pix = set()
    for ch in txt:
        k = police.code_de(ch)
        for gy in range(8):
            v = font[k * 8 + gy]
            for gx in range(8):
                if v & (0x80 >> gx):
                    pix.add((x + gx, ytop + gy))
        x += larg[k]
    for q in pix:
        p[q] = couleur
    if ombre:
        for (qx, qy) in pix:
            if (qx + 1, qy) not in pix and qx + 1 <= x1:
                p[(qx + 1, qy)] = ombre


def autonomes(rom, font, larg):
    for a, txt in AUTONOMES.items():
        p = _bloc(rom, a, 8, 2)
        assert p[(1, 4)] == 2 and p[(62, 4)] == 2, hex(a)
        for x in range(2, 62):
            for y in range(3, 13):
                p[(x, y)] = fond(x + 8, y + 8)
        _texte(p, txt, font, larg, 2, 61, 4, 2)
        _ecrit(rom, a, p, 8, 2)
    for a, txt in NOMS.items():
        p = _bloc(rom, a, 6, 2)
        for x in range(2, 46):
            for y in range(2, 11):
                p[(x, y)] = 1
        _texte(p, txt, font, larg, 2, 45, 2, 3, ombre=2)
        _ecrit(rom, a, p, 6, 2)


def plaques(rom, src, font, larg, zone):
    R = decors.enregistrements(src)
    ajout = {}
    for i, txt in TEXTES.items():
        ajout[i] = traite(rom, src, R[i], txt, font, larg, zone)
    return ajout
