"""Graphismes traduits (tuiles brutes 2 bpp, 8x8, pixel 0 en bits 15-14 du mot petit-boutiste).

etiquette_nom(rom) : bandeau « NAME » de la saisie du nom (4 tuiles en 0x9F3C2) -> « NOM ».
Style d'origine : lettres couleur 1, ombre couleur 3 décalée (+1, +1), fond 0 (transparent).
"""
NOM_ADR = 0x9F3C2

LETTRES = {
    'N': ['1...1', '11..1', '1.1.1', '1..11', '1...1'],
    'O': ['.111.', '1...1', '1...1', '1...1', '.111.'],
    'M': ['1...1', '11.11', '1.1.1', '1...1', '1...1'],
}


def bandeau(mot, ntuiles, x0=1, y0=1):
    W = ntuiles * 8
    pix = [[0] * W for _ in range(8)]
    x = x0
    corps = set()
    for c in mot:
        g = LETTRES[c]
        for y, l in enumerate(g):
            for i, ch in enumerate(l):
                if ch == '1':
                    corps.add((x + i, y0 + y))
        x += len(g[0]) + 2
    for (px, py) in corps:
        pix[py][px] = 1
    for (px, py) in corps:
        for dx, dy in ((1, 0), (0, 1), (1, 1)):
            qx, qy = px + dx, py + dy
            if qx < W and qy < 8 and (qx, qy) not in corps:
                pix[qy][qx] = 3
    out = bytearray()
    for t in range(ntuiles):
        for y in range(8):
            w = 0
            for i in range(8):
                w |= pix[y][t * 8 + i] << (14 - 2 * i)
            out += w.to_bytes(2, 'little')
    return bytes(out)


def etiquette_nom(rom):
    rom[NOM_ADR:NOM_ADR + 64] = bandeau('NOM', 4)


# Boutons des menus : blocs bruts de 22 tuiles (11 x 2) ; parallélogramme fond 3, bord 1/2 ;
# libellé couleur 1 + ombre couleur 2 à droite, lignes 3..10.
BOUTONS = {0xA0D30: 'Duel libre', 0xBB333: 'Donner carte', 0xBF036: 'Atelier deck',
           0xC0B93: 'Sauvegarde', 0xC1526: 'Match amical', 0xC1F80: 'Recevoir carte',
           0xC41FA: 'Lexique', 0xC6B87: 'Échanges', 0xC7021: 'Connexion DC', 0xC8057: 'Détecteur',
           0xC94BD: 'Tutoriel', 0xC9735: 'Menu 13', 0xC9893: 'Histoire', 0xC9C89: 'Combat',
           0xD609D: 'Menu cartes', 0xD9920: 'Match à mort', 0xDA98B: 'Boutique'}


def _bloc_pix(rom, a, nc, nr):
    p = [[0] * (nc * 8) for _ in range(nr * 8)]
    for k in range(nc * nr):
        g = rom[a + k * 16:a + k * 16 + 16]
        c, r = k % nc, k // nc
        for y in range(8):
            w = g[2 * y] | g[2 * y + 1] << 8
            for x in range(8):
                p[r * 8 + y][c * 8 + x] = (w >> (14 - 2 * x)) & 3
    return p


def _bloc_ecrit(rom, a, p, nc, nr):
    for k in range(nc * nr):
        c, r = k % nc, k // nc
        b = bytearray()
        for y in range(8):
            w = 0
            for x in range(8):
                w |= p[r * 8 + y][c * 8 + x] << (14 - 2 * x)
            b += w.to_bytes(2, 'little')
        rom[a + k * 16:a + k * 16 + 16] = b


def boutons(rom, font, larg):
    import police
    for a, txt in BOUTONS.items():
        p = _bloc_pix(rom, a, 11, 2)
        for y in range(2, 13):
            xs = [x for x in range(88) if p[y][x] == 3]
            for x in range(xs[0] + 1, xs[-1]):
                p[y][x] = 3
        L = sum(larg[police.code_de(c)] for c in txt)
        assert L <= 70, (txt, L)
        x = 10 + (70 - L) // 2
        for ch in txt:
            k = police.code_de(ch)
            for gy in range(8):
                v = font[k * 8 + gy]
                for gx in range(8):
                    if v & (0x80 >> gx):
                        p[3 + gy][x + gx] = 1
                        if p[3 + gy][x + gx + 1] == 3:
                            p[3 + gy][x + gx + 1] = 2
            x += larg[k]
        _bloc_ecrit(rom, a, p, 11, 2)


# Bandeaux en anglais (table d'images 0x97C00-0x98070 : ptr, n, w, h=1, carte 0..n-1) -> français.
# adresse fichier des tuiles : texte (majuscules). Le style (couleur du texte, ombre) est relevé sur l'original.
BANDEAUX = {
    0xD2E4C: 'CÂBLE', 0xD62F9: 'RENFORT', 0xAEEA0: 'COMBAT', 0xC16FC: 'NOM',
    0xC7FF9: 'CARTE RE 3', 0xC6FC3: 'CARTE AC 3', 0xC6B19: 'CARTE AC/RE', 0xDA91D: 'CARTE PERSO',
    0xA0CB2: 'TOUT CAPCOM', 0xC7440: 'TOUT SNK', 0xD7A50: 'BILAN', 0xD2E8A: 'MOYENNE',
    0xC49AB: 'EFFACEMENT', 0x9F354: 'CHOIX DECK', 0xD2EE8: 'DUEL CARTES', 0xC220A: 'RARETÉ',
    0xC0846: 'CAPACITÉ', 0xAEF3C: 'GAIN CARTE', 0xC4A39: 'REPRISE', 0xD2F66: 'LIAISON DC',
    0xAEF9A: 'MOTS', 0xC4A87: 'TUTORIEL', 0xD2FD4: 'CHOIX CARTE', 0xAEFD8: 'CARTE ÉCHANGÉE',
    0xC4AE5: 'CARTE OFFERTE', 0xAF076: 'BOUTIQUE', 0xC4B83: 'ATELIER', 0xAF0E4: 'MATCH À MORT',
    0xC4BF1: 'MATCH AMICAL', 0xAF1A2: 'DUEL LIBRE', 0xAF210: 'MENU', 0xA88BD: 'SAUVEGARDE',
    0xAF27E: 'NOM DU DECK', 0xAF2EC: 'ALBUM CARTES', 0xAF36A: 'CRÉER DECK', 0xAF466: 'MENU CARTES',
    0xAF3D8: 'FICHE PERSO', 0xBBC66: 'OPTIONS', 0xAEEDE: 'RECHERCHE', 0xD9AF6: 'TPS',
}


def _style(p, W):
    """Couleur du texte, couleur de l'ombre (ou None), haut du texte."""
    import collections
    cnt = collections.Counter(v for row in p for v in row if v)
    if not cnt:
        return None
    voisin = collections.Counter()
    for y in range(8):
        for x in range(W):
            v = p[y][x]
            if v and x > 0 and y > 0:
                for dx, dy in ((1, 0), (0, 1), (1, 1)):
                    u = p[y - dy][x - dx]
                    if u and u != v:
                        voisin[v] += 1
                        break
    cols = sorted(cnt, key=lambda c: voisin[c] / cnt[c])
    corps = cols[0]
    ombre = cols[1] if len(cols) > 1 else None
    haut = min(y for y in range(8) for x in range(W) if p[y][x] == corps)
    return corps, ombre, haut


def bandeau_fr(rom, a, n, txt, font, larg):
    import police
    W = n * 8
    p = _bloc_pix(rom, a, n, 1)
    st = _style(p, W)
    corps, ombre, haut = st
    codes = [police.code_de(c) for c in txt]
    esp = 1
    L = sum(larg[k] for k in codes) + (1 if ombre else 0)
    assert L <= W - 1, 'bandeau trop long : %s (%d px pour %d)' % (txt, L, W)
    q = [[0] * W for _ in range(8)]
    x = 1 + (W - 1 - L) // 2 if n >= 6 else 1
    dy = haut - 1                      # ligne 1 des capitales -> haut du texte d'origine
    pix = set()
    for k in codes:
        for gy in range(8):
            v = font[k * 8 + gy]
            for gx in range(8):
                if v & (0x80 >> gx):
                    yy = gy + dy
                    if 0 <= yy < 8 and x + gx < W:
                        pix.add((x + gx, yy))
        x += larg[k] - 1 + esp
    for (xx, yy) in pix:
        q[yy][xx] = corps
    if ombre:
        for (xx, yy) in pix:
            for ddx, ddy in ((1, 0), (0, 1), (1, 1)):
                X, Y = xx + ddx, yy + ddy
                if X < W and Y < 8 and (X, Y) not in pix:
                    q[Y][X] = ombre
    avant = bytes(rom[a:a + n * 16])
    _bloc_ecrit(rom, a, q, n, 1)
    return avant


def bandeaux(rom, font, larg):
    src = bytes(rom)
    zones, faits = [], []
    for a in range(0x97C00, 0x98070):
        ptr = int.from_bytes(src[a:a + 4], 'little')
        if not (0x290000 <= ptr < 0x2E0000):
            continue
        n, w, h = int.from_bytes(src[a + 4:a + 6], 'little'), src[a + 6], src[a + 7]
        if not (2 <= n <= 40 and w == n and h == 1 and list(src[a + 8:a + 8 + n]) == list(range(n))):
            continue
        t = ptr - 0x200000
        zones.append((t, t + n * 16))
        if t in BANDEAUX:
            faits.append((t, n))
    for t, n in faits:
        bandeau_fr(rom, t, n, BANDEAUX[t], font, larg)
    # octets partagés avec une image voisine NON traduite : on garde l'original
    for t, n in faits:
        for z0, z1 in zones:
            if (z0, z1) == (t, t + n * 16) or z0 in [f[0] for f in faits]:
                continue
            for o in range(max(t, z0), min(t + n * 16, z1)):
                rom[o] = src[o]


# Bulles d'aide des menus : images de 12 x 4 tuiles (0x300 octets) dès 0xCF1D9 ; intérieur couleur 1,
# texte couleur 3, 3 lignes (haut des glyphes en y = 3, 12, 22), x 6..91.
BULLES = [
    "J'avance dans l'histoire à coups de duels !",                 # Rikuto
    "J'affronte mes anciens rivaux ou un ami (câble) !",
    "Je gère mes decks et j'échange par câble !",
    "Boutique et services par le terminal !",
    "Je sauvegarde ma progression !",
    "Duels libres contre Haruna et cie ! Sans pitiééé !",          # Haruna
    "Duel entre amis ! Le gagnant gagne une carte !",
    "Perdez, et une carte de votre deck s'envole !",
    "Les règles du duel ! Les bases d'abord !",
    "Le lexique du duel ! Que du texte (+_+!)",
    "Crée tes decks ou consulte ton album de cartes.",             # Mme Lip
    "Donne des cartes à un ami. 6 sortes au plus !",
    "Reçois des cartes d'un ami.",
    "Échangez des cartes à la boutique.",
    "Utilisez la machine d'échange.",
    "Connexion à « Capcom vs. SNK 2 » (Dreamcast).",
    "Cherchez des cartes avec l'unité sans fil.",
    "Désolée ! Vous n'avez pas assez de cartes !",                 # Haruna
    "Pas de carte AC « ESP » : accès impossible.",
]
BULLE0, BULLE_PAS = 0xCF1D9, 0x300


def bulles(rom, font, larg):
    import police, forme
    for i, txt in enumerate(BULLES):
        a = BULLE0 + i * BULLE_PAS
        p = _bloc_pix(rom, a, 12, 4)
        for y in range(3, 30):
            for x in range(96):
                if p[y][x] == 3:
                    p[y][x] = 1
        lignes = forme.coupe(txt, 86)
        assert len(lignes) <= 3, (i, lignes)
        for ly, l in zip((3, 12, 22), lignes):
            x = 6
            for ch in l:
                k = police.code_de(ch)
                for gy in range(8):
                    v = font[k * 8 + gy]
                    for gx in range(8):
                        if v & (0x80 >> gx):
                            p[ly + gy][x + gx] = 3
                x += larg[k]
        _bloc_ecrit(rom, a, p, 12, 4)


# Écran-titre : libellés détourés (lettres couleur 1, contour couleur 3, fond 0), 8 lignes.
TITRE = {0xCF06D: (7, 'CONTINUER'), 0xD9B24: (7, 'COMMENCER'), 0xD7A9E: (11, 'APPUIE SUR #')}
ICONE_A = (0xD7A9E, 33, 42)          # colonnes de l'icône « A » dans PRESS A BUTTON


def _detoure(rom, a, n, txt, font, larg, icone=None):
    import police
    W = n * 8
    corps = set()
    x = 1
    for ch in txt:
        if ch == '#':
            x += 1
            ix = x
            x += icone[0] and len(icone[0][0]) or 0
            x += 1
            continue
        k = police.code_de(ch)
        for gy in range(8):
            v = font[k * 8 + gy]
            for gx in range(8):
                if v & (0x80 >> gx):
                    corps.add((x + gx, gy))
        x += larg[k]
    assert x <= W, (txt, x, W)
    q = [[0] * W for _ in range(8)]
    for (cx, cy) in corps:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                X, Y = cx + dx, cy + dy
                if 0 <= X < W and 0 <= Y < 8:
                    q[Y][X] = 3
    for (cx, cy) in corps:
        q[cy][cx] = 1
    if icone:
        for y in range(8):
            for i, v in enumerate(icone[0][y]):
                q[y][ix + i] = v
    return q


def titre(rom, font, larg):
    src = bytes(rom)
    a0, c0, c1 = ICONE_A
    p = _bloc_pix(src, a0, 11, 1)
    ic = [p[y][c0:c1] for y in range(8)]
    for a, (n, txt) in TITRE.items():
        q = _detoure(rom, a, n, txt, font, larg, icone=(ic,) if '#' in txt else None)
        _bloc_ecrit(rom, a, q, n, 1)


# Étapes du tutoriel : images 12 x 2 ; intitulé couleur 2 + liseré couleur 1 (gauche/haut), x 33..95, y 0..11.
TUTO = {0xD2AD9: 'Le deck', 0xD4330: 'Le duel', 0xD490F: 'La main', 0xD4E7E: 'Attaque',
        0xD812A: 'Combos', 0xD8679: 'Cartes RE', 0xDA2F3: 'Victoire'}


def tutoriel(rom, font, larg, jp):
    """Étapes du tutoriel (images 12 x 2 de l'écran du tutoriel) ; chaque case -> adresse(s) ROM de sa tuile
    (tools/data/tuto_cases.json), lue dans la ROM japonaise ; seules les tuiles UNIQUES sont réécrites."""
    import json, os, police
    ici = os.path.dirname(os.path.abspath(__file__))
    cases = json.load(open(os.path.join(ici, 'data', 'tuto_cases.json')))
    for i, txt in enumerate(TUTO.values()):
        p = [[0] * 96 for _ in range(16)]
        for dr in (0, 1):
            for c in range(12):
                a = cases[i]['%d,%d' % (dr, c)][0]
                g = jp[a:a + 16]
                for y in range(8):
                    w = g[2 * y] | g[2 * y + 1] << 8
                    for x in range(8):
                        p[dr * 8 + y][c * 8 + x] = (w >> (14 - 2 * x)) & 3
        avant = [row[:] for row in p]
        for y in range(0, 13):
            for x in range(33, 96):
                if p[y][x] in (1, 2) and len(cases[i]['%d,%d' % (y // 8, x // 8)]) == 1:
                    p[y][x] = 0
        x = 35
        pix = set()
        for ch in txt:
            k = police.code_de(ch)
            for gy in range(8):
                vv = font[k * 8 + gy]
                for gx in range(8):
                    if vv & (0x80 >> gx):
                        pix.add((x + gx, gy))
            x += larg[k]
        for (qx, qy) in pix:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if 0 <= qy + dy < 16 and 0 <= qx + dx < 96 and (qx + dx, qy + dy) not in pix:
                        p[qy + dy][qx + dx] = 1
        for (qx, qy) in pix:
            p[qy][qx] = 2
        for dr in (0, 1):
            for c in range(12):
                nouv = [p[dr * 8 + y][c * 8:c * 8 + 8] for y in range(8)]
                anc = [avant[dr * 8 + y][c * 8:c * 8 + 8] for y in range(8)]
                if nouv == anc:
                    continue
                hits = cases[i]['%d,%d' % (dr, c)]
                assert len(hits) == 1, ('tuile partagée touchée', txt, dr, c, len(hits))
                b = bytearray()
                for y in range(8):
                    w = 0
                    for xx in range(8):
                        w |= nouv[y][xx] << (14 - 2 * xx)
                    b += w.to_bytes(2, 'little')
                rom[hits[0]:hits[0] + 16] = b


# Début de duel : « 先攻 1st.Attack » / « 後攻 2nd Attack » (plan 1 ; tuiles lues dans la ROM japonaise aux
# adresses de tools/data/duel_cases.json).
# Haut (kanji détourés couleur 1) -> mot FR détouré ; bandeau (couleur 1, texte en creux couleur 0) -> texte FR.
# Chaque tuile modifiée est écrite dans TOUTES ses copies identiques (<= 3 : variantes du même dessin).
DUEL = {'premier': ('1ER', 'à attaquer !', 18), 'second': ('2E', 'à attaquer !', 18)}


def debut_duel(rom, font, larg, jp):
    import json, os, police
    ici = os.path.dirname(os.path.abspath(__file__))
    info = json.load(open(os.path.join(ici, 'data', 'duel_cases.json')))

    def dessine(p, txt, x, y, couleur, echelle=1):
        for ch in txt:
            k = police.code_de(ch)
            for gy in range(8):
                vv = font[k * 8 + gy]
                for gx in range(8):
                    if vv & (0x80 >> gx):
                        for sy in range(echelle):
                            for sx in range(echelle):
                                X, Y = x + gx * echelle + sx, y + gy * echelle + sy
                                if 0 <= Y < len(p) and 0 <= X < len(p[0]):
                                    p[Y][X] = couleur
            x += larg[k] * echelle

    ecrit = {}
    for nom, (haut, bande, ybande) in DUEL.items():
        o = info[nom]
        W, H = o['w'] * 8, o['h'] * 8
        p = [[0] * W for _ in range(H)]
        for r in range(o['h']):
            for c in range(o['w']):
                a = o['cases']['%d,%d' % (r, c)][0]
                g = jp[a:a + 16]
                for y in range(8):
                    w = g[2 * y] | g[2 * y + 1] << 8
                    for x in range(8):
                        p[r * 8 + y][c * 8 + x] = (w >> (14 - 2 * x)) & 3
        avant = [row[:] for row in p]
        # haut : efface les kanji, écrit le mot (échelle 2) détouré
        for y in range(ybande):
            for x in range(W):
                p[y][x] = 0
        corps = [[0] * W for _ in range(H)]
        ech = 2 if ybande >= 16 else 1
        L = sum(larg[police.code_de(c)] for c in haut) * ech
        dessine(corps, haut, 16, ybande - 8 * ech, 1, ech)      # avant la colonne 6 (tuiles du 攻 partagées)
        assert 16 + L <= 48, (haut, L)
        for y in range(ybande):
            for x in range(W):
                if corps[y][x]:
                    p[y][x] = 1
        # bandeau : repeint couleur 1 entre ses bords, texte en creux (0)
        for y in range(ybande + 2, ybande + 10):
            xs = [x for x in range(W) if avant[y][x] == 1]
            for x in range(xs[0] + 2, xs[-1] - 1):
                p[y][x] = 1
        L = sum(larg[police.code_de(c)] for c in bande)
        dessine(p, bande, (W - L) // 2, ybande + 2, 0)
        for r in range(o['h']):                 # tuiles très partagées : on n'y touche pas
            for c in range(o['w']):
                if len(o['cases']['%d,%d' % (r, c)]) > 3:
                    for y in range(8):
                        p[r * 8 + y][c * 8:c * 8 + 8] = avant[r * 8 + y][c * 8:c * 8 + 8]
        for r in range(o['h']):
            for c in range(o['w']):
                nouv = [p[r * 8 + y][c * 8:c * 8 + 8] for y in range(8)]
                if nouv == [avant[r * 8 + y][c * 8:c * 8 + 8] for y in range(8)]:
                    continue
                hits = o['cases']['%d,%d' % (r, c)]
                assert 1 <= len(hits) <= 3, ('tuile trop partagée', nom, r, c, len(hits))
                b = bytearray()
                for y in range(8):
                    w = 0
                    for x in range(8):
                        w |= nouv[y][x] << (14 - 2 * x)
                    b += w.to_bytes(2, 'little')
                for a in hits:
                    assert ecrit.get(a, bytes(b)) == bytes(b), ('conflit', hex(a))
                    ecrit[a] = bytes(b)
    for a, b in ecrit.items():
        rom[a:a + 16] = b


# « HP » rouge des plaques de duel (2 tuiles en 0xD68ED, lettres grasses couleur 2) -> « PV »
HP_DUEL = 0xD68ED
PV_DUEL = ['................', '................', '...####..##.##..', '...##.##.##.##..',
           '...####..##.##..', '...##.....###...', '...##......#....', '................']


# « HP » du panneau de terrain (décor du duel) : tuiles 0xBBB59 + 0xBBB69, lettres couleur 1, x 5..15 / y 2..6
HP_TERRAIN = 0xBBB59
PV_TERRAIN = ['#####.##.##', '##.##.##.##', '##.##.##.##', '#####..###.', '##......#..']


def pv_terrain(rom):
    p = _bloc_pix(rom, HP_TERRAIN, 2, 1)
    for y in range(2, 7):
        for x in range(5, 16):
            if p[y][x] == 1:
                p[y][x] = 0
            if PV_TERRAIN[y - 2][x - 5] == '#':
                p[y][x] = 1
    _bloc_ecrit(rom, HP_TERRAIN, p, 2, 1)


# Enseigne « ジョイジョイ » du décor de la ville (tuiles VRAM 0x1BD-0x1BF = fichier 0xAAC22, 3 tuiles) :
# zone de texte x 2..23, y 2..6 (fond 3 = jaune, encre 1 = sombre) ; bord 2 en x=1, filets y=0/1/7 gardés. 22 px pour
# « JOYJOY » -> J sur 2 px.
ENSEIGNE_JOY = 0xAAC22
JOYJOY = ['.#.###.#.#..#.###.#.#',
          '.#.#.#.#.#..#.#.#.#.#',
          '.#.#.#..#...#.#.#..#.',
          '.#.#.#..#...#.#.#..#.',
          '#..###..#..#..###..#.']


def enseigne_joyjoy(rom):
    p = _bloc_pix(rom, ENSEIGNE_JOY, 3, 1)
    for y in range(2, 7):
        for x in range(2, 24):
            p[y][x] = 3
    for y, l in enumerate(JOYJOY):
        for x, c in enumerate(l):
            if c == '#':
                p[2 + y][2 + x] = 1
    _bloc_ecrit(rom, ENSEIGNE_JOY, p, 3, 1)


def pv_duel(rom):
    b = bytearray()
    for t in range(2):
        for l in PV_DUEL:
            w = 0
            for x in range(8):
                if l[t * 8 + x] == '#':
                    w |= 2 << (14 - 2 * x)
            b += w.to_bytes(2, 'little')
    rom[HP_DUEL:HP_DUEL + 32] = b


# glyphe « HP » de la police (code 0x1EF, fond 1 / encre 3) -> « PV » (décision de Tixul : HP = PV)
PV = ['11111111', '11111111', '33313131', '31313131', '31313131', '33113131', '31111311', '31111311']


def glyphe_pv(rom):
    o = 0x8D00C + 0x1EF * 16
    b = bytearray()
    for l in PV:
        w = 0
        for x, ch in enumerate(l):
            w |= int(ch) << (14 - 2 * x)
        b += w.to_bytes(2, 'little')
    rom[o:o + 16] = b


if __name__ == '__main__':
    d = bandeau('NOM', 4)
    for y in range(8):
        print(''.join('.123'[(int.from_bytes(d[t * 16 + 2 * y:t * 16 + 2 * y + 2], 'little') >> (14 - 2 * x)) & 3]
                      for t in range(4) for x in range(8)))
