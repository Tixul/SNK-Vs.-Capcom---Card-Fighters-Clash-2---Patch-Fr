"""ROM japonaise d'origine : contrôle, textes de la table 0xE0000, type de chaque texte.

« SNK vs. Capcom - Card Fighters 2 - Expand Edition (Japan).ngc » : 2 097 152 octets, CRC32 CCBCFDA7,
SHA-1 2c4fc8594f8ba2bf39e62fe8bcb79fc2df5a83b6. La sauvegarde est écrite dans la cartouche à partir de
0x1F8000 : ce bloc est ignoré par le contrôle (une ROM qui contient déjà une partie est acceptée).
"""
import hashlib
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import table  # noqa: E402

TAILLE = 0x200000
SAUVEGARDE = 0x1F8000
SHA1_SANS_SAUVEGARDE = '98fca93eebd986d4244c6612a58a872710e4afeb'
TABLE, NB = 0xE0000, 6250
NL = chr(92) + 'n'


def charge(chemin):
    d = open(chemin, 'rb').read()
    if len(d) != TAILLE or hashlib.sha1(d[:SAUVEGARDE]).hexdigest() != SHA1_SANS_SAUVEGARDE:
        raise SystemExit('%s : ce n\'est pas la ROM japonaise attendue (voir README, section 1.1)' % chemin)
    return d


def esc(t):
    return t.replace(chr(92), '¥').replace('\n', NL).replace('\t', ' ')


def textes(jp):
    """index -> (adresse CPU, texte japonais décodé, \\n = ligne)."""
    out = {}
    for i in range(NB):
        a = int.from_bytes(jp[TABLE + 4 * i:TABLE + 4 * i + 4], 'little')
        if a == 0xFFFFFFFF:
            continue
        out[i] = (a, esc(table.decode(jp, a - 0x200000)[0]))
    return out


def type_de(i, jp):
    """D = dialogue (boîtes de 3 lignes, coupé automatiquement), F n = fenêtre de n lignes,
    N = nom de locuteur, M = menu / mise en page à colonnes (@)."""
    if '{M ' in jp or '@@' in jp:
        return 'M'
    if 3000 <= i <= 3099:
        return 'N'
    if i >= 3200:
        return 'D'
    n = len(jp.split(NL))
    if 2001 <= i <= 2999:
        n = 3
    return 'F %d' % n


def boites(jp):
    """Dialogue japonais -> boîtes de 3 lignes séparées par ¶ (⏎ = retour à la ligne japonais)."""
    tete = ''
    m = re.match(r'^(\{(?:08|17) [0-9A-F]{2}\})+', jp)
    if m:
        tete = m.group(0); jp = jp[len(tete):]
    ls = jp.split(NL)
    out = []
    for k in range(0, len(ls), 3):
        b = list(ls[k:k + 3])
        while b and b[-1] == '':
            b.pop()
        if b:
            out.append('⏎'.join(b))
    return tete + ' ¶ '.join(out)


def source(jp):
    """index -> (type, japonais tel que présenté dans les lots)."""
    out = {}
    for i, (a, t) in textes(jp).items():
        if not t:
            continue
        ty = type_de(i, t)
        out[i] = (ty, boites(t) if ty == 'D' else t)
    return out
