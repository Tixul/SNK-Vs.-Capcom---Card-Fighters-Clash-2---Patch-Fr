"""Mise en forme du français de CFC2 (largeurs au pixel près, chasse variable).

Format d'écriture (colonne FR des lots) :
  - DIALOGUE (boîte de 3 lignes, 144 px) : « {08 xx} » éventuel en tête, puis les boîtes séparées
    par « ¶ ». Chaque boîte est coupée automatiquement en lignes de 144 px ; au-delà de 3 lignes,
    des boîtes sont AJOUTÉES. « \\n » force un retour à la ligne dans une boîte.
  - AUTRE (fenêtre fixe) : lignes séparées par « \\n », gardées telles quelles ; la largeur de chaque
    ligne est contrôlée contre la limite de la chaîne (voir limite()).
Variables : largeur estimée VAR_PX.
"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import police  # noqa: E402

LARG_DLG = 136
VAR_PX = {0x10: 40, 0x11: 40, 0x12: 72, 0x13: 72, 0x14: 64, 0x15: 80, 0x16: 64, 0x18: 32, 0x19: 64}
_LARG = None


def init(rom):
    """Largeurs des glyphes, tirées de la police construite depuis la ROM japonaise."""
    global _LARG
    _LARG = police.construit(rom)[1]


def larg_table():
    if _LARG is None:
        raise RuntimeError("forme.init(rom) doit être appelé d'abord")
    return _LARG


def jetons(texte):
    """Découpe en jetons : ('c', car) / ('code', '{..}')."""
    out = []
    i = 0
    while i < len(texte):
        if texte[i] == '{':
            j = texte.index('}', i)
            out.append(('code', texte[i:j + 1])); i = j + 1
        else:
            out.append(('c', texte[i])); i += 1
    return out


def px(texte):
    """Largeur en pixels d'un morceau de ligne (sans \\n)."""
    L = larg_table()
    w = 0
    for k, v in jetons(texte):
        if k == 'c':
            if v == '@':
                w = (w + 7) // 8 * 8 + 8
            else:
                w += L[police.code_de(v)]
        else:
            corps = v[1:-1].split()
            if len(corps) == 1 and len(corps[0]) == 3:          # glyphe {1EC} : tuile entière
                w = (w + 7) // 8 * 8 + 8
            elif len(corps) == 1 and int(corps[0], 16) in VAR_PX:
                w = (w + 7) // 8 * 8 + VAR_PX[int(corps[0], 16)]
    return w


def coupe(boite, largeur=LARG_DLG):
    """Coupe une boîte en lignes <= largeur (mots entiers ; \\n forcé respecté)."""
    lignes = []
    boite = re.sub(r'\{[^}]*\}', lambda m: m.group(0).replace(' ', '\x01'), boite)
    # espaces insécables de la ponctuation française
    boite = re.sub(r' ([?!:;»])', '\x01\\1', boite).replace('« ', '«\x01')
    for para in boite.split('\\n'):
        mots = [m.replace('\x01', ' ') for m in para.split(' ')]
        cur = ''
        for m in mots:
            essai = m if not cur else cur + ' ' + m
            if px(essai) <= largeur or not cur:
                cur = essai
            else:
                lignes.append(cur); cur = m
        lignes.append(cur)
    return lignes


def dialogue(fr, largeur=LARG_DLG):
    """Texte FR « {08 xx}boîte¶boîte » -> texte final à \\n (boîtes de 3 lignes)."""
    tete = ''
    m = re.match(r'^(\{(?:08|17) [0-9A-Fa-f]{2}\})+', fr)
    if m:
        tete = m.group(0); fr = fr[len(tete):]
    sortie = []
    for b in fr.split('¶'):
        b = b.strip()
        lignes = coupe(b, largeur)
        while lignes:
            bloc = lignes[:3]; lignes = lignes[3:]
            sortie.append(bloc)
    texte = []
    for i, bloc in enumerate(sortie):
        if i < len(sortie) - 1:
            bloc = bloc + [''] * (3 - len(bloc))
        texte += bloc
    return tete + '\\n'.join(texte)


def trop_larges(texte, largeur):
    """Lignes d'un texte final dont la largeur dépasse."""
    return [(l, px(l)) for l in texte.split('\\n') if px(re.sub(r'\{[MI] [^}]*\}', '', l)) > largeur]


if __name__ == '__main__':
    for t in sys.argv[1:]:
        print(dialogue(t))
