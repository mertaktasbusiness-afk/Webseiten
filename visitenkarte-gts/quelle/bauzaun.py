"""GTS Bauzaunbanner 340 x 173 cm (+1 cm Beschnitt), reine Vektorgrafik, CMYK-PDF im Maßstab 1:1.
Zeichnungseinheit = 1 cm; Sicherheitsabstand 5 cm (Saum/Ösen)."""
import os, subprocess, sys
import numpy as np, cv2, cairosvg, pymupdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
from flyer import t, icon, filled_icon, badge, F, C_CREAM, C_DARK, C_GOLD, C_GOLD_LT, C_FOOT, C_TEXT
from gts import logo_svg, gold_gradient
from herbst import qr_code, C_WHITE

OUT = sys.argv[1] if len(sys.argv) > 1 else 'bauzaun_out'
os.makedirs(OUT, exist_ok=True)
W, H, B = 340.0, 173.0, 1.0            # cm
URL = 'https://www.gts-boeblingen.de'


def banner_svg():
    o = [f'<rect x="-1" y="-1" width="{W + 2}" height="{H + 2}" fill="{C_FOOT}"/>']
    # Creme-Feld rechts mit goldener Diagonale (wie Visitenkarte)
    x_top, x_bot = 236.0, 207.0
    o.append(f'<path d="M{x_top - (x_bot - x_top) / H},-1 H{W + 1} V{H + 1} H{x_bot + (x_bot - x_top) / H} Z" fill="{C_CREAM}"/>')
    o.append(f'<path d="M{x_top - (x_bot - x_top) / H * 1},-1 L{x_bot + (x_bot - x_top) / H},{H + 1}" '
             f'stroke="{C_GOLD_LT}" stroke-width="1.3"/>')

    # --- links: Logo, Slogan, Leistungen
    s = 150 / (44.95 - 7.2)
    o.append(logo_svg(F, f'translate({20 - 7.2 * s:.3f},{15 - 3.25 * s:.3f}) scale({s:.4f})',
                      C_WHITE, C_WHITE, C_WHITE, 'goldDark'))
    o.append(t('Ihr Partner für', 6.0, 20.5, 93.0, C_WHITE, 'serif_med'))
    o.append(t('Sauberkeit. Technik.', 9.0, 20.0, 108.5, C_GOLD_LT, 'serif_logo'))
    o.append(t('Zuverlässigkeit.', 9.0, 20.0, 122.5, C_WHITE, 'serif_logo'))
    o.append(f'<path d="M20.5,129.5 H55" stroke="{C_GOLD_LT}" stroke-width="0.6"/>')
    svc = [('gebaeude', ['GEBÄUDE-', 'REINIGUNG']), ('haus', ['HAUSMEISTER-', 'SERVICE']),
           ('schild', ['SICHERHEIT']), ('schluessel', ['SCHLIESS-', 'TECHNIK']),
           ('sterne', ['SONDER-', 'REINIGUNG'])]
    for i, (ic, lab) in enumerate(svc):
        cx = 33 + i * 37
        o.append(f'<circle cx="{cx}" cy="144" r="8.6" fill="none" stroke="{C_GOLD_LT}" stroke-width="0.35"/>')
        o.append(icon(ic, cx, 144, 10.5, C_GOLD_LT, sw=1.2))
        for j, ln in enumerate(lab):
            o.append(t(ln, 2.3, cx, 158.0 + j * 3.6, C_WHITE, 'sans_semi', anchor='middle', tr=0.25))

    # --- rechts: Siegel, Telefon, Web, QR
    o.append(badge(303.0, 33.0, 21.5))
    cx = 280.0
    o.append(t('JETZT UNVERBINDLICH ANFRAGEN', 3.0, cx, 70.0, C_GOLD, 'sans_semi', anchor='middle', tr=0.5))
    o.append(filled_icon('phone', 236.0, 84.5, 9.5, C_GOLD))
    o.append(t('0170 1601830', 8.8, 244.0, 89.0, C_DARK, 'sans_semi'))
    o.append(t('www.gts-boeblingen.de', 4.4, cx, 102.0, C_DARK, 'sans_medium', anchor='middle'))
    o.append(f'<path d="M{cx - 20},108.5 H{cx + 20}" stroke="{C_GOLD}" stroke-width="0.5"/>')
    o.append(qr_code(229.0, 114.0, 42.0, URL).replace(f'stroke="{C_GOLD_LT}"', f'stroke="{C_GOLD}"'))
    o.append(t('QR-Code scannen', 3.0, 279.0, 124.0, C_DARK, 'sans_semi'))
    o.append(t('& Webseite besuchen', 3.0, 279.0, 129.5, C_DARK, 'sans_semi'))
    o.append(filled_icon('mail', 281.5, 140.2, 4.4, C_GOLD))
    o.append(t('info@gts-boeblingen.de', 2.5, 286.0, 141.3, C_TEXT))
    o.append(filled_icon('pin', 281.5, 148.6, 4.6, C_GOLD))
    o.append(t('Böblingen und Umgebung', 2.5, 286.0, 149.7, C_TEXT))

    defs = (gold_gradient('goldDark', 6, 5, 20, 20, [(0, '#D8BC8A'), (0.45, '#A9844E'), (0.75, '#CDAE78'), (1, '#B08D58')])
            + gold_gradient('shieldGold', -4, -5, 4, 5, [(0, '#CDAA6E'), (0.5, '#A8844D'), (1, '#86653A')]))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{(W + 2 * B) * 10}mm" height="{(H + 2 * B) * 10}mm" viewBox="-1 -1 {W + 2 * B} {H + 2 * B}">'
            f'<defs>{defs}</defs>{"".join(o)}</svg>')


if __name__ == '__main__':
    svg = banner_svg()
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to='bauzaun_rgb.pdf')
    raw = 'bauzaun_cmyk_raw.pdf'
    subprocess.run(['gs', '-q', '-dNOPAUSE', '-dBATCH', '-dSAFER', '-sDEVICE=pdfwrite', '-o', raw,
                    '-dCompatibilityLevel=1.6', '-dPDFSETTINGS=/prepress', '-sColorConversionStrategy=CMYK',
                    '-sProcessColorModel=DeviceCMYK', '-dAutoRotatePages=/None', '-f', 'bauzaun_rgb.pdf'], check=True)
    PT = 72 / 2.54                                     # pt pro cm
    w = PdfWriter()
    w.add_page(PdfReader(raw).pages[0])
    pg = w.pages[0]
    media = RectangleObject([0, 0, (W + 2 * B) * PT, (H + 2 * B) * PT])
    pg.mediabox = pg.cropbox = pg.bleedbox = media
    pg.trimbox = RectangleObject([B * PT, B * PT, (W + B) * PT, (H + B) * PT])
    w.add_metadata({'/Title': 'GTS Bauzaunbanner 340 x 173 cm (1:1, +1 cm Beschnitt, CMYK)',
                    '/Author': 'GTS Gebäude Technik Service'})
    pdf = os.path.join(OUT, 'GTS_Bauzaunbanner_340x173cm.pdf')
    w.write(pdf)
    p = pymupdf.open(pdf)[0]
    assert not p.get_fonts()
    print('Trim cm', round(p.trimbox.width / PT, 1), 'x', round(p.trimbox.height / PT, 1))
    pix = p.get_pixmap(dpi=10, clip=p.trimbox)                 # ~1340 px breit
    pix.save(os.path.join(OUT, 'Vorschau_Bauzaunbanner.png'))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)[..., :3]
    val, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print('QR ->', repr(val))
    assert val == URL
