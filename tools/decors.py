"""Décors (images de fond) : répertoire en 0x104000.

Enregistrement de 16 octets : carte (ptr 32 bits), tuiles (ptr), largeur, hauteur, nb de tuiles, ?
Carte : mots (tuile relative à la 1re tuile de l'image | attributs : bit 15 miroir H, bit 14 miroir V,
bits 9-12 palette). Les tuiles sont chargées en VRAM à partir de 0x118 (décor du club).

    python tools/decors.py ROM_JP       -> out/decors.png (haut de chaque décor, plaque de lieu ; Pillow)
"""
import os, sys


def u(d, a, n):
    return int.from_bytes(d[a:a + n], 'little')


def fichier(a):
    """Adresse CPU -> fichier (puce 1 en 0x200000, puce 2 en 0x800000)."""
    return a - 0x200000 if a < 0x800000 else a - 0x800000 + 0x200000


def enregistrements(d):
    out = []
    a = 0x104044
    while True:
        m, t, w, h, n = u(d, a, 4), u(d, a + 4, 4), u(d, a + 8, 2), u(d, a + 10, 2), u(d, a + 12, 2)
        if not (0x200000 <= m < 0xA00000 and 0x200000 <= t < 0xA00000 and 0 < w <= 32 and 0 < h <= 32):
            break
        out.append(dict(adr=a, carte=fichier(m), tuiles=fichier(t), w=w, h=h, n=n))
        a += 16
    return out


def rendu(d, r, lignes=None):
    from PIL import Image
    w, h = r['w'], r['h'] if lignes is None else lignes
    im = Image.new('L', (w * 8, h * 8))
    for row in range(h):
        for c in range(w):
            mw = u(d, r['carte'] + (row * w + c) * 2, 2)
            t = mw & 0x1FF
            hf, vf = mw >> 15 & 1, mw >> 14 & 1
            g = d[r['tuiles'] + t * 16:r['tuiles'] + t * 16 + 16]
            for y in range(8):
                ww = g[2 * y] | g[2 * y + 1] << 8
                for x in range(8):
                    p = (ww >> (14 - 2 * x)) & 3
                    im.putpixel((c * 8 + (7 - x if hf else x), row * 8 + (7 - y if vf else y)), 255 - p * 80)
    return im


if __name__ == '__main__':
    from PIL import Image, ImageDraw
    d = open(sys.argv[1], 'rb').read()
    os.makedirs('out', exist_ok=True)
    R = enregistrements(d)
    print(len(R), 'décors')
    H = 4
    sh = Image.new('L', (2 * 170, ((len(R) + 1) // 2) * (H * 8 + 12)), 255)
    dr = ImageDraw.Draw(sh)
    for i, r in enumerate(R):
        x0, y0 = (i % 2) * 170, (i // 2) * (H * 8 + 12)
        sh.paste(rendu(d, r, H), (x0, y0 + 10))
        dr.text((x0, y0), '%d %X %dx%d n%d' % (i, r['adr'], r['w'], r['h'], r['n']), fill=0)
    sh.save(os.path.join('out', 'decors.png'))
