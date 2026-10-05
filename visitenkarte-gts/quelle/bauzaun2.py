"""GTS Bauzaunbanner – Entwurf 2: heller, ruhiger, große Telefonnummer, QR mit Fehlerkorrektur H.
340 x 173 cm (+1 cm Beschnitt), Einheit = 1 cm, reine Vektorgrafik, CMYK 1:1."""
import os, subprocess, sys
import numpy as np, cv2, cairosvg, pymupdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
from flyer import t, icon, filled_icon, badge, F, C_CREAM, C_DARK, C_GOLD, C_GOLD_LT, C_FOOT, C_TEXT
from gts import logo_svg, gold_gradient
from herbst import qr_code, C_WHITE

OUT = sys.argv[1] if len(sys.argv) > 1 else 'bauzaun2_out'
os.makedirs(OUT, exist_ok=True)
W, H, B = 340.0, 173.0, 1.0
URL = 'https://www.gts-boeblingen.de'
BAR = 116.0                                         # Oberkante der dunklen Kontaktleiste


def banner2_svg():
    o = [f'<rect x="-1" y="-1" width="{W + 2}" height="{H + 2}" fill="{C_CREAM}"/>']
    # großes Logo-Wasserzeichen hinter dem Siegel (nur Bogen + Ring, sehr dezent)
    s = 6.4                                         # Bogenmitte = Siegelmitte
    o.append(logo_svg(F, f'translate({298 - 14.2 * s:.2f},{53 - 11.1 * s:.2f}) scale({s})',
                      '#E7DFD1', C_CREAM, C_CREAM, 'wmLight', tagline=False))

    # --- oben links: Logo, Claim, Leistungen
    s = 118 / (44.95 - 7.2)
    o.append(logo_svg(F, f'translate({20 - 7.2 * s:.3f},{14 - 3.25 * s:.3f}) scale({s:.4f})',
                      C_DARK, C_DARK, C_DARK, 'goldCream'))
    o.append(t('Gebäude in besten Händen.', 10.5, 20.0, 86.0, C_DARK, 'serif_logo'))
    o.append(f'<path d="M20.5,93 H58" stroke="{C_GOLD}" stroke-width="0.7"/>')
    o.append(t('REINIGUNG  ·  HAUSMEISTERSERVICE  ·  SICHERHEIT  ·  SCHLIESSTECHNIK', 3.0, 20.3, 103.0,
               C_GOLD, 'sans_semi', tr=0.45))

    # --- oben rechts: Siegel
    o.append(badge(298.0, 53.0, 30.0))

    # --- Kontaktleiste
    o.append(f'<rect x="-1" y="{BAR}" width="{W + 2}" height="{H - BAR + 1}" fill="{C_FOOT}"/>')
    o.append(f'<path d="M-1,{BAR} H{W + 1}" stroke="{C_GOLD_LT}" stroke-width="0.9"/>')
    o.append(t('JETZT UNVERBINDLICH ANFRAGEN', 2.9, 20.3, 129.5, C_GOLD_LT, 'sans_semi', tr=0.5))
    o.append(filled_icon('phone', 26.0, 145.3, 12.5, C_GOLD_LT))
    o.append(t('0170 1601830', 10.5, 36.5, 150.5, C_WHITE, 'sans_semi'))
    o.append(t('www.gts-boeblingen.de', 4.6, 20.3, 163.5, C_GOLD_LT, 'sans_medium', tr=0.1))

    o.append(f'<path d="M158,128 V162" stroke="{C_GOLD_LT}" stroke-width="0.3"/>')
    o.append(filled_icon('mail', 171.0, 136.6, 5.0, C_GOLD_LT))
    o.append(t('info@gts-boeblingen.de', 3.0, 177.0, 138.0, C_WHITE))
    o.append(filled_icon('pin', 171.0, 147.4, 5.2, C_GOLD_LT))
    o.append(t('Böblingen und Umgebung', 3.0, 177.0, 148.8, C_WHITE))
    o.append(icon('haken', 171.0, 158.2, 5.0, C_GOLD_LT, sw=2.2))
    o.append(t('Meisterbetrieb für Privat- & Geschäftskunden', 2.4, 177.0, 159.4, '#D9D4C8'))

    # QR-Karte, ragt aus der Leiste nach oben
    qx, qy, qs = 268.0, 101.0, 48.0
    o.append(f'<rect x="{qx - 4}" y="{qy - 4}" width="{qs + 8}" height="{qs + 15}" rx="2" fill="{C_GOLD}"/>')
    o.append(qr_code(qx, qy, qs, URL, ecc='H').replace(f'stroke="{C_GOLD_LT}"', 'stroke="#FFFFFF"'))
    o.append(t('SCANNEN & WEBSEITE BESUCHEN', 1.9, qx + qs / 2, qy + qs + 6.6, '#FFFFFF', 'sans_semi',
               anchor='middle', tr=0.2))

    defs = (gold_gradient('goldCream', 7, 8, 16, 18, [(0, '#B8935C'), (0.45, '#8C6A3B'), (0.75, '#B99661'), (1, '#9B7845')])
            + gold_gradient('wmLight', 0, 0, 1, 1, [(0, '#E3D6BF'), (1, '#E3D6BF')])
            + gold_gradient('shieldGold', -4, -5, 4, 5, [(0, '#CDAA6E'), (0.5, '#A8844D'), (1, '#86653A')]))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{(W + 2 * B) * 10}mm" height="{(H + 2 * B) * 10}mm" viewBox="-1 -1 {W + 2 * B} {H + 2 * B}">'
            f'<defs>{defs}</defs>{"".join(o)}</svg>')


if __name__ == '__main__':
    cairosvg.svg2pdf(bytestring=banner2_svg().encode(), write_to='bauzaun2_rgb.pdf')
    raw = 'bauzaun2_cmyk_raw.pdf'
    subprocess.run(['gs', '-q', '-dNOPAUSE', '-dBATCH', '-dSAFER', '-sDEVICE=pdfwrite', '-o', raw,
                    '-dCompatibilityLevel=1.6', '-dPDFSETTINGS=/prepress', '-sColorConversionStrategy=CMYK',
                    '-sProcessColorModel=DeviceCMYK', '-dAutoRotatePages=/None', '-f', 'bauzaun2_rgb.pdf'], check=True)
    PT = 72 / 2.54
    w = PdfWriter()
    w.add_page(PdfReader(raw).pages[0])
    pg = w.pages[0]
    media = RectangleObject([0, 0, (W + 2 * B) * PT, (H + 2 * B) * PT])
    pg.mediabox = pg.cropbox = pg.bleedbox = media
    pg.trimbox = RectangleObject([B * PT, B * PT, (W + B) * PT, (H + B) * PT])
    w.add_metadata({'/Title': 'GTS Bauzaunbanner Entwurf 2 – 340 x 173 cm (1:1, +1 cm Beschnitt, CMYK)',
                    '/Author': 'GTS Gebäude Technik Service'})
    pdf = os.path.join(OUT, 'GTS_Bauzaunbanner_Entwurf2_340x173cm.pdf')
    w.write(pdf)
    p = pymupdf.open(pdf)[0]
    assert not p.get_fonts()
    print('Trim cm', round(p.trimbox.width / PT, 1), 'x', round(p.trimbox.height / PT, 1))
    pix = p.get_pixmap(dpi=10, clip=p.trimbox)
    pix.save(os.path.join(OUT, 'Vorschau_Bauzaunbanner_Entwurf2.png'))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)[..., :3]
    val, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print('QR ->', repr(val))
    assert val == URL
