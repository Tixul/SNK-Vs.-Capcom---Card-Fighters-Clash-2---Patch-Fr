"""Table de caractères du JP (police 0x8D00C, code = octet >= 0x20 ou 0p xx -> p*256+xx)."""
KANA = ('あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみ'
        'むめもやゆよらりるれろわをんぁぃぅぇぉゃゅょっがぎぐげござじずぜ'
        'ぞだぢづでどばびぶべぼぱぴぷぺぽアイウエオカキクケコサシスセソタ'
        'チツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンァィ'
        'ゥェォャュョッガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ')
T = {}
for i, c in enumerate(KANA):
    T[0x60 + i] = c
for c in range(0x20, 0x60):
    T[c] = chr(c)
T.update({0x22: '「', 0x23: '」', 0x24: 'Ⓥ', 0x2D: 'ー', 0x3B: 'ヴ', 0x3C: 'ʳ', 0x3D: 'º', 0x5B: '。', 0x5C: '、', 0x5D: '゛', 0x5E: '゜', 0x5F: '■'})
import os
K = os.path.join(os.path.dirname(__file__), 'kanji.txt')
if os.path.exists(K):
    for ln in open(K, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln or ln.startswith('#'):
            continue
        code, s = ln.split('\t')[:2]
        base = int(code, 16)
        for i, ch in enumerate(s):
            if ch != '?':
                T[base + i] = ch


NL = chr(10)


def decode(d, p, tab=None):
    """Décode depuis p jusqu'à 00 ; renvoie (texte, p_fin). Codes :
    {08 xx} visage/locuteur, {17 xx}, {0C} {0D} {09} {0A}, {10}..{1F} variables,
    {M n b c d} en-tête de menu 0E, {I x y a b c e} article de menu (libellé jusqu'au \n)."""
    tab = tab or T
    out = []
    while True:
        c = d[p]; p += 1
        if c == 0:
            break
        if c == 0x0B:
            out.append(NL); continue
        if c in (0x08, 0x17):
            out.append('{%02X %02X}' % (c, d[p])); p += 1; continue
        if c == 0x0E:
            n = d[p]
            out.append('{M %s}' % d[p:p + 4].hex(' ')); p += 4
            for i in range(n):
                out.append('{I %s}' % d[p:p + 6].hex(' ')); p += 6
                while d[p] != 0x0B:
                    c2 = d[p]; p += 1
                    if 1 <= c2 <= 7:
                        k = c2 * 256 + d[p]; p += 1
                        out.append(tab.get(k, '{%03X}' % k))
                    elif c2 < 0x20:
                        out.append('{%02X}' % c2)
                    else:
                        out.append(tab.get(c2, '{%02X}' % c2))
                p += 1
                out.append(NL)
            continue
        if 1 <= c <= 7:
            k = c * 256 + d[p]; p += 1
            out.append(tab.get(k, '{%03X}' % k)); continue
        if c < 0x20:
            out.append('{%02X}' % c); continue
        out.append(tab.get(c, '{%02X}' % c))
    return ''.join(out), p
