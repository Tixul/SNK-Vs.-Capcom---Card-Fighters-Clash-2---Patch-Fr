"""Logo de l'écran-titre : « カードファイターズ » -> « CARD FIGHTERS ».

Le logo français a été dessiné puis retouché à la main ; le résultat est livré tel quel dans
tools/data/logo_fr.bin (cartes des plans 1 et 2 en 0x94243 / 0x9453F, tuiles en 0xA60B3, sprites du
« ズ » en 0xC31CB vidés). Format : « LOGO », puis des enregistrements (adresse fichier 32 bits, longueur
16 bits, octets), petit-boutiste.
"""
import os

ICI = os.path.dirname(os.path.abspath(__file__))
DONNEES = os.path.join(ICI, 'data', 'logo_fr.bin')


def logo(rom):
    d = open(DONNEES, 'rb').read()
    assert d[:4] == b'LOGO', 'logo_fr.bin invalide'
    k = 4
    while k < len(d):
        a = int.from_bytes(d[k:k + 4], 'little')
        n = int.from_bytes(d[k + 4:k + 6], 'little')
        rom[a:a + n] = d[k + 6:k + 6 + n]
        k += 6 + n
