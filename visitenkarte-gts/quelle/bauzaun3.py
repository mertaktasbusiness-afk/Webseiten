"""GTS Bauzaunbanner – Entwurf 3: nur Logo (mit Schriftzug) + QR-Code. 340 x 173 cm (+1 cm), Einheit 1 cm."""
import os, subprocess, sys
import numpy as np, cv2, cairosvg, pymupdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
from flyer import F, C_GOLD_LT, C_FOOT, t, filled_icon, globe
from gts import logo_svg, gold_gradient
from herbst import qr_code, C_WHITE

OUT = sys.argv[1] if len(sys.argv) > 1 else 'bauzaun3_out'
os.makedirs(OUT, exist_ok=True)
W, H, B = 340.0, 173.0, 1.0
URL = 'https://www.gts-boeblingen.de'


def banner3_svg():
    o = [f'<rect x="-1" y="-1" width="{W + 2}" height="{H + 2}" fill="{C_FOOT}"/>']
    MID = 76.0                                        # vertikale Mitte von Logo und QR
    lw = 175.0                                        # Logobreite
    s = lw / (44.95 - 7.2)
    lh = (18.1 - 3.25) * s
    o.append(logo_svg(F, f'translate({22 - 7.2 * s:.3f},{MID - lh / 2 - 3.25 * s:.3f}) scale({s:.4f})',
                      C_WHITE, C_WHITE, C_WHITE, 'goldDark'))
    o.append(f'<path d="M218,{MID - 48} V{MID + 48}" stroke="{C_GOLD_LT}" stroke-width="0.5"/>')
    qs = 88.0
    o.append(qr_code(236.0, MID - qs / 2, qs, URL, ecc='H').replace('stroke-width="0.35"', 'stroke-width="1.2"'))

    # Kontaktzeile unten: Telefon (links) – E-Mail (Mitte) – Webseite (rechts)
    o.append(f'<path d="M22,136 H{W - 22}" stroke="{C_GOLD_LT}" stroke-width="0.5"/>')
    cap, yb = 4.6, 155.0
    ic = yb - cap / 2
    from gts import ink_width
    f = F['sans_medium']
    size = f.size_for_cap(cap)
    items = [('phone', '0170 1601830'), ('mail', 'info@gts-boeblingen.de'), ('globe', 'www.gts-boeblingen.de')]
    ICON_W = 9.0                                         # Icon + Abstand zum Text
    widths = [ICON_W + ink_width(f, txt, size, 0.15)[0] for _, txt in items]
    gap = (W - 44 - sum(widths)) / 2                     # gleiche Abstände, bündig 22 cm links/rechts
    x = 22.0
    for (k, txt), wdt in zip(items, widths):
        cx = x + 3.6
        o.append(globe(cx, ic, 3.2, C_GOLD_LT) if k == 'globe' else filled_icon(k, cx, ic, 8.8, C_GOLD_LT))
        o.append(t(txt, cap, x + ICON_W, yb, C_WHITE, 'sans_medium', tr=0.15))
        x += wdt + gap
    defs = gold_gradient('goldDark', 6, 5, 20, 20, [(0, '#D8BC8A'), (0.45, '#A9844E'), (0.75, '#CDAE78'), (1, '#B08D58')])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{(W + 2 * B) * 10}mm" height="{(H + 2 * B) * 10}mm" viewBox="-1 -1 {W + 2 * B} {H + 2 * B}">'
            f'<defs>{defs}</defs>{"".join(o)}</svg>')


if __name__ == '__main__':
    cairosvg.svg2pdf(bytestring=banner3_svg().encode(), write_to='bauzaun3_rgb.pdf')
    raw = 'bauzaun3_cmyk_raw.pdf'
    subprocess.run(['gs', '-q', '-dNOPAUSE', '-dBATCH', '-dSAFER', '-sDEVICE=pdfwrite', '-o', raw,
                    '-dCompatibilityLevel=1.6', '-dPDFSETTINGS=/prepress', '-sColorConversionStrategy=CMYK',
                    '-sProcessColorModel=DeviceCMYK', '-dAutoRotatePages=/None', '-f', 'bauzaun3_rgb.pdf'], check=True)
    PT = 72 / 2.54
    w = PdfWriter()
    w.add_page(PdfReader(raw).pages[0])
    pg = w.pages[0]
    media = RectangleObject([0, 0, (W + 2 * B) * PT, (H + 2 * B) * PT])
    pg.mediabox = pg.cropbox = pg.bleedbox = media
    pg.trimbox = RectangleObject([B * PT, B * PT, (W + B) * PT, (H + B) * PT])
    w.add_metadata({'/Title': 'GTS Bauzaunbanner Entwurf 3 – 340 x 173 cm (1:1, +1 cm Beschnitt, CMYK)',
                    '/Author': 'GTS Gebäude Technik Service'})
    pdf = os.path.join(OUT, 'GTS_Bauzaunbanner_Entwurf3_340x173cm.pdf')
    w.write(pdf)
    p = pymupdf.open(pdf)[0]
    assert not p.get_fonts()
    pix = p.get_pixmap(dpi=10, clip=p.trimbox)
    pix.save(os.path.join(OUT, 'Vorschau_Bauzaunbanner_Entwurf3.png'))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)[..., :3]
    val, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print('QR ->', repr(val))
    assert val == URL
