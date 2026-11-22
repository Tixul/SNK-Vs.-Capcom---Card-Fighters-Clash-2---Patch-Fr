"""Extrait le texte de SA ROM japonaise en lots de traduction (le texte d'origine n'est pas distribué).

    python tools/extraire.py "SNK vs. Capcom - Card Fighters 2 - Expand Edition (Japan).ngc" [ROM_EN]

-> out/src/lot_NN.tsv : index <TAB> type <TAB> japonais <TAB> anglais (aide, si ROM_EN est donnée)
   types : D dialogue (boîtes séparées par ¶, ⏎ = retour à la ligne japonais, à ne pas recopier),
           F n fenêtre de n lignes, N nom de locuteur, M menu / colonnes (recopier {M ..} {I ..} et les @)
-> out/src/lot_25.tsv : carte <TAB> nom <TAB> capacité <TAB> (anglais) <TAB> texte de capacité <TAB> ambiance
ROM_EN (facultative) : une version traduite en anglais qui garde la même table de textes (0xE0000).
Les lots ont les mêmes numéros et les mêmes index que lang/fr/lot_NN_fr.tsv.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rom_jp, cartes, table  # noqa: E402

# (début, fin) ; les lots sont coupés à ~CIBLE caractères japonais dans chaque plage
PLAGES = [(3550, 6300), (3200, 3549), (2501, 2999), (2001, 2499), (3100, 3199), (3000, 3099),
          (0, 999), (1000, 1999)]
CIBLE = 5200
TEN = {c: chr(c) for c in range(0x20, 0x7F)}
TEN[0x40] = ' '


def textes_en(en):
    out = {}
    for i in range(rom_jp.NB):
        a = int.from_bytes(en[rom_jp.TABLE + 4 * i:rom_jp.TABLE + 4 * i + 4], 'little')
        if a != 0xFFFFFFFF:
            out[i] = rom_jp.esc(table.decode(en, a - 0x200000, TEN)[0]).strip()
    return out


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    jp = rom_jp.charge(sys.argv[1])
    en = open(sys.argv[2], 'rb').read() if len(sys.argv) > 2 else None
    ten = textes_en(en) if en else {}
    src = rom_jp.source(jp)
    brut = {i: t for i, (a, t) in rom_jp.textes(jp).items()}
    d = os.path.join('out', 'src')
    os.makedirs(d, exist_ok=True)
    n = 0
    for a, b in PLAGES:
        sel = [i for i in sorted(src) if a <= i <= b]
        lot, tot = [], 0
        def ecrit():
            nonlocal n, lot, tot
            if not lot:
                return
            n += 1
            with open(os.path.join(d, 'lot_%02d.tsv' % n), 'w', encoding='utf-8') as o:
                for i in lot:
                    o.write('%04d\t%s\t%s\t%s\n' % (i, src[i][0], src[i][1], ten.get(i, '')))
            lot, tot = [], 0
        for i in sel:
            lot.append(i); tot += len(brut[i])
            if tot >= CIBLE:
                ecrit()
        ecrit()
    with open(os.path.join(d, 'lot_25.tsv'), 'w', encoding='utf-8') as f:
        for k in range(cartes.NB):
            _, nm, c = cartes.champs(jp, k)
            ne, ce = ('', '') if not en else (cartes.dec(cartes.champs(en, k)[1], TEN), cartes.dec(cartes.champs(en, k)[2], TEN))
            f.write('%03d\t%s\t%s\t%s\t%s\t%s\t%s\n' % (k, cartes.dec(nm, table.T), cartes.dec(c, table.T), ne, ce,
                                                       brut.get(2001 + k, ''), brut.get(2501 + k, '')))
    print('%d lots + lot_25 (noms des cartes) dans %s' % (n, d))


if __name__ == '__main__':
    main()
