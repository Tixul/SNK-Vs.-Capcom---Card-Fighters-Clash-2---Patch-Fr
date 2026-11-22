"""Contrôle d'une traduction contre le japonais de la ROM :

    python tools/controle.py --rom "SNK vs. Capcom - Card Fighters 2 - Expand Edition (Japan).ngc" --lang fr

- index connus, une seule fois ; codes identiques (multiensemble) : {08 xx}, {17 xx}, {10}..{1F},
  {0C} {0D} {09} {0A}, {M ..} {I ..}, glyphes {1xx}/{2xx} (sauf kanji non identifiés au milieu du japonais) ;
- D (dialogue) : mise en forme automatique possible ; nombre de « ¶ » (avertissement seulement) ;
- F n : au plus n lignes, chaque ligne <= 136 px (lexique 3100-3199 : coupé aux mots par le build) ;
  N : <= 80 px ; M : lignes <= 144 px, pas plus de tuiles que le japonais, colonnes des @ identiques ;
- noms des cartes (lot_25*) : 15 octets au plus par champ, nom <= 55 px (face de la carte) ;
- caractères encodables par la police.
Code de sortie 1 s'il reste une erreur (hors EXCEPTIONS, vérifiées à l'écran).
"""
import glob, os, re, sys, collections
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import police, forme, rom_jp  # noqa: E402
NL = chr(92) + 'n'
CODES = re.compile(r'\{(?:08|17) [0-9A-Fa-f]{2}\}|\{1[0-9A-F]\}|\{0[9ACD]\}|\{[MI] [^}]*\}|\{[12][0-9A-E][0-9A-F]\}')
KANJI_INCONNUS = {'101', '1B7', '270', '279', '29F', '2B0', '1E7'}


def codes(t):
    c = collections.Counter(CODES.findall(t))
    for k in list(c):
        if k[1:-1] in KANJI_INCONNUS:
            del c[k]
    return c


def _segments(l):
    l = re.sub(r'\{(?:08|17) ..\}|\{[MI] [^}]*\}', '', l)
    return l


def colonnes_jp(l):
    """Colonnes (tuiles) où commence chaque morceau qui suit une suite de @ (1 car. JP = 1 tuile)."""
    l = _segments(l)
    col, out, prev = 0, [], ''
    for k, v in forme.jetons(l):
        if prev == '@' and v != '@':
            out.append(col)
        col += 1
        prev = v
    return out


def colonnes_fr(l):
    """Idem en français : texte proportionnel arrondi à la tuile, chaque @ = une tuile entière."""
    l = _segments(l)
    out, prev, w = [], '', 0
    for k, v in forme.jetons(l):
        if prev == '@' and v != '@':
            out.append(w // 8)
        w += forme.px(v) if v != '@' else 0
        if v == '@':
            w = (w + 7) // 8 * 8 + 8
        prev = v
    return out


def controle(src, fr):
    err = []
    av = []
    for i, t in fr.items():
        if i not in src:
            continue
        typ, jp = src[i]
        cj, cf = codes(jp), codes(t)
        if cj != cf:
            err.append('%s codes : JP %s / FR %s' % (i, dict(cj - cf), dict(cf - cj)))
        brut = re.sub(r'\{[^}]*\}', '', t).replace(NL, '').replace('¶', '')
        for ch in brut:
            if ch == '@':
                continue
            try:
                police.code_de(ch)
            except KeyError:
                err.append('%s caractère interdit %r' % (i, ch))
        if typ == 'D':
            if jp.count('¶') != t.count('¶'):
                av.append('%s ¶ : JP %d / FR %d' % (i, jp.count('¶'), t.count('¶')))
            try:
                final = forme.dialogue(t)
            except Exception as e:
                err.append('%s mise en forme : %s' % (i, e)); continue
            for l in final.split(NL):
                if forme.px(l) > forme.LARG_DLG:
                    err.append('%s mot trop long pour une ligne : %s' % (i, l))
        elif typ.startswith('F') or typ in ('N', 'M'):
            n = int(typ.split()[1]) if typ.startswith('F') else 99
            lim = 136 if typ.startswith('F') else (80 if typ == 'N' else 144)
            ls = t.split(NL)
            if len(ls) > n:
                err.append('%s %d lignes > %d' % (i, len(ls), n))
            for l in ls:
                w = forme.px(re.sub(r'\{[MI] [^}]*\}', '', l))
                if 3100 <= int(i) <= 3199:
                    break                       # lexique : coupé aux mots par le build
                if w > lim:
                    err.append('%s ligne %d px > %d : %s' % (i, w, lim, l))
            if typ == 'M' and '@' in jp and not 3100 <= int(i) <= 3199:
                jl = jp.split(NL)
                tj = max(len(forme.jetons(_segments(x))) for x in jl)
                for k, l in enumerate(ls):
                    if k < len(jl):
                        tf = (forme.px(_segments(l)) + 7) // 8
                        if tf > tj:
                            err.append('%s ligne %d : %d tuiles > %d (japonais) : %s' % (i, k + 1, tf, tj, l))
                for k, l in enumerate(ls):
                    if k < len(jl) and colonnes_jp(jl[k]) != colonnes_fr(l):
                        err.append('%s alignement @ ligne %d : JP colonnes %s / FR %s : %s' % (
                            i, k + 1, colonnes_jp(jl[k]), colonnes_fr(l), l))
    return err, av


# Vérifiées à l'écran : le japonais compte la variable {12} (nom de carte) à 0 tuile, le français est plus court.
EXCEPTIONS = {'0225'}


def lit(f):
    out, err = {}, []
    for k, ln in enumerate(open(f, encoding='utf-8')):
        ln = ln.rstrip('\n')
        if not ln or ln.startswith('#'):
            continue
        p = ln.split('\t')
        out[p[0]] = p[1:]
        if len(p) < 2:
            err.append('%s ligne %d : %d colonnes' % (os.path.basename(f), k + 1, len(p)))
    return out, err


def noms_cartes(fr):
    err = []
    for k, champs in fr.items():
        for t in champs[:2]:
            try:
                n = len(bytes(0x40 if c == '@' else police.code_de(c) for c in t))
            except KeyError as e:
                err.append('carte %s caractère interdit %s' % (k, e)); continue
            if n > 15:
                err.append('carte %s : %r > 15 caractères' % (k, t))
        if champs and forme.px(champs[0]) > 55:
            err.append('carte %s : nom %d px > 55 : %s' % (k, forme.px(champs[0]), champs[0]))
    return err


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Contrôle une traduction.')
    ap.add_argument('--rom', required=True)
    ap.add_argument('--lang', default='fr')
    a = ap.parse_args()
    jp = rom_jp.charge(a.rom)
    forme.init(jp)
    src = {'%04d' % i: v for i, v in rom_jp.source(jp).items()}
    fichiers = sorted(glob.glob(os.path.join(os.path.dirname(ICI), 'lang', a.lang, 'lot_*.tsv')))
    tout, err, vus = {}, [], set()
    for f in fichiers:
        d, e = lit(f)
        err += e
        if os.path.basename(f).startswith('lot_25'):
            err += noms_cartes(d)
            continue
        for k, v in d.items():
            if k in vus:
                err.append('%s : %s en double' % (os.path.basename(f), k))
            vus.add(k)
            if k not in src:
                err.append('%s : index %s inconnu' % (os.path.basename(f), k))
            elif v:
                tout[k] = v[0]
    e2, av = controle(src, tout)
    err += [x for x in e2 if x.split()[0] not in EXCEPTIONS]
    manque = [k for k in src if k not in tout]
    print('%d textes traduits, %d non traduits (restent en japonais), %d erreurs, %d avertissements'
          % (len(tout), len(manque), len(err), len(av)))
    for x in err:
        print('  E', x)
    for x in av[:40]:
        print('  A', x)
    if manque:
        print('  non traduits :', ' '.join(manque[:40]), '...' if len(manque) > 40 else '')
    sys.exit(1 if err else 0)


if __name__ == '__main__':
    main()
