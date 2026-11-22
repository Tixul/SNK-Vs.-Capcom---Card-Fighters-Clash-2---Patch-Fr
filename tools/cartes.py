"""Base des cartes : 424 enregistrements de 64 octets en 0x806E4 (nom 16 octets, nom de capacité 16, stats).

Extraction : tools/extraire.py (out/src/lot_25.tsv). Traduction (lang/<code>/lot_25_*.tsv) :
carte <TAB> nom <TAB> capacité (15 caractères au plus chacun ; nom <= 55 px pour la face de la carte).
"""
import os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import table  # noqa: E402
BASE, NB, TAILLE = 0x806E4, 424, 64
TEN = {c: chr(c) for c in range(0x20, 0x7F)}
TEN[0x40] = ' '


def dec(b, t):
    out = []
    i = 0
    while i < len(b):
        c = b[i]
        if c == 0:
            break
        if 1 <= c <= 7:
            out.append(t.get(c * 256 + b[i + 1], '{%03X}' % (c * 256 + b[i + 1]))); i += 2
        else:
            out.append(t.get(c, '{%02X}' % c)); i += 1
    return ''.join(out)


def champs(rom, k):
    o = BASE + TAILLE * k
    return o, rom[o:o + 16], rom[o + 16:o + 32]


def ecrit_noms(rom, fichier):
    """lang/<code>/lot_25_*.tsv (carte, nom, capacité) -> champs de 16 octets (15 car. + 00)."""
    import police
    n = 0
    for ln in open(fichier, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln:
            continue
        p = (ln.split('\t') + ['', ''])[:3]
        k = int(p[0])
        o = BASE + TAILLE * k
        for champ, txt in ((o, p[1]), (o + 16, p[2])):
            if rom[champ] == 0 and not txt:
                continue
            b = bytes(0x40 if c == '@' else police.code_de(c) for c in txt)
            assert len(b) <= 15, (k, txt)
            rom[champ:champ + 16] = b + b'\x00' * (16 - len(b))
        n += 1
    return n

