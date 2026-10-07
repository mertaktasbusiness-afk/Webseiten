"""GTS Herbst-Flyer beidseitig: Seite 1 = Herbst-Angebot (herbst.py), Seite 2 = Leistungen/Kunden/Kontakt."""
import os, subprocess, sys
import numpy as np, cv2, cairosvg, pymupdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
import flyer
from flyer import t, icon, filled_icon, globe, uri, upscale, F, W, H, B, PX
from flyer import C_CREAM, C_DARK, C_GOLD, C_GOLD_LT, C_FOOT, C_TEXT
from gts import logo_svg, gold_gradient, ink_width
from herbst import herbst_svg, qr_code, leaf, C_COPPER, C_WHITE

OUT = sys.argv[1] if len(sys.argv) > 1 else 'herbst_out'
os.makedirs(OUT, exist_ok=True)
URL = 'https://www.gts-boeblingen.de'

SERVICES = [                                       # Texte gemäß Korrektur des Kunden (herbst_rueckseite_kunde.jpg)
    ('gebaeude', ['GEBÄUDEREINIGUNG'], ['Unterhalts-, Grund-, Glas-', 'und Fassadenreinigung']),
    ('haus', ['HAUSMEISTERSERVICE'], ['Objektbetreuung und', 'Instandhaltung']),
    ('schild', ['SICHERHEIT'], ['Objektschutz und', 'Betreuung von Liegenschaften']),
    ('schluessel', ['SCHLIESSTECHNIK'], ['Zylinderwechsel und', 'Schließanlagen']),
    ('sterne', ['SPEZIALREINIGUNG'], ['Praxen, Kirchen, Studios', 'und Baustellen']),
    ('dampf', ['UNTERHALTSREINIGUNG'], ['Regelmäßige Reinigung für', 'ein gepflegtes Umfeld']),
    ('diamant', ['SONDER- & INTENSIVREINIGUNG'], ['Oberflächenveredelung', 'und Intensivpflege']),
    ('thermometer', ['TROCKENDAMPFTECHNOLOGIE'], ['Hygienisch. Chemiefrei.', 'Tiefenwirksam.']),
    ('blatt', ['NACHHALTIGE', 'REINIGUNGSSYSTEME'], ['Umweltschonend und effektiv']),
    ('tablet', ['DIGITALE', 'QUALITÄTSKONTROLLE'], ['Transparenz und Kontrolle', 'in Echtzeit']),
    ('chip', ['KI-GESTÜTZTE', 'VERWALTUNGSPROZESSE'], ['Effizient. Organisiert.', 'Zukunftsorientiert.']),
    ('chart', ['WIRTSCHAFTLICHE', 'LÖSUNGEN'], ['Effiziente Lösungen für', 'nachhaltigen Werterhalt']),
]


def lounge(tw, th):
    src = flyer.mock[1250:1452, 0:320]
    big = upscale(src, 12 * PX)
    big = cv2.copyMakeBorder(big, 0, 0, 36, 0, cv2.BORDER_REFLECT)        # 3 mm Beschnitt links
    nw, nh = int(round(tw * 12)), int(round(th * 12))
    sc = max(nw / big.shape[1], nh / big.shape[0])
    big = cv2.resize(big, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC)
    ox, oy = (big.shape[1] - nw) // 2, (big.shape[0] - nh) // 2
    return big[oy:oy + nh, ox:ox + nw]


def back_svg():
    """Rückseite nach der vom Kunden vergrößerten Vorlage (herbst_rueckseite_kunde.jpg)."""
    o = [f'<rect x="-3" y="-3" width="{W + 6}" height="{H + 6}" fill="{C_CREAM}"/>']
    # --- Kopf
    o.append(f'<rect x="-3" y="-3" width="{W + 6}" height="45" fill="{C_FOOT}"/>')
    s = 72 / (44.95 - 7.2)
    o.append(logo_svg(F, f'translate({12 - 7.2 * s:.3f},{9.0 - 3.25 * s:.3f}) scale({s:.4f})',
                      C_WHITE, C_WHITE, C_WHITE, 'goldDark'))
    o.append(t('Ihr Partner für', 3.9, 199, 18.9, C_WHITE, 'serif_med', anchor='end'))
    o.append(t('Sauberkeit. Technik.', 5.9, 199, 27.4, C_GOLD_LT, 'serif_logo', anchor='end'))
    o.append(t('Zuverlässigkeit.', 5.9, 199, 35.8, C_WHITE, 'serif_logo', anchor='end'))
    o.append(f'<path d="M-3,42.2 H{W + 3}" stroke="{C_GOLD_LT}" stroke-width="0.8"/>')

    # --- Leistungen
    o.append(t('UNSERE LEISTUNGEN', 4.9, 105, 57.2, C_DARK, 'serif_logo', anchor='middle', tr=0.75))
    o.append(f'<path d="M29.5,54.4 H52 M158,54.4 H180.5" stroke="{C_GOLD}" stroke-width="0.35"/>')
    cols = [27.9, 79.0, 130.2, 181.5]
    rows_y = [73.6, 115.4, 155.6]
    for i, (ic, title, desc) in enumerate(SERVICES):
        cx, iy = cols[i % 4], rows_y[i // 4]
        o.append(f'<circle cx="{cx}" cy="{iy}" r="9.5" fill="none" stroke="{C_GOLD}" stroke-width="0.35"/>')
        o.append(icon(ic, cx, iy, 11.0, C_GOLD, sw=1.15))
        ty = iy + 15.3
        for j, tl in enumerate(title):
            f = F['sans_semi']
            wi, _ = ink_width(f, tl, f.size_for_cap(2.4), 0.06)
            cap = 2.4 * min(1.0, 45.5 / wi)             # lange Titel passend verkleinern (max. 45,5 mm)
            o.append(t(tl, cap, cx, ty + j * 4.35, C_DARK, 'sans_semi', anchor='middle', tr=0.06))
        dy = ty + (len(title) - 1) * 4.35 + 5.0
        for j, dl in enumerate(desc):
            o.append(t(dl, 2.15, cx, dy + j * 4.4, C_TEXT, anchor='middle'))

    # --- Kunden & Partner
    o.append(f'<path d="M-3,189.5 H{W + 3}" stroke="#D8CDB9" stroke-width="0.3"/>')
    img = lounge(93.5, 48.0)
    o.append(f'<image x="-3" y="190.5" width="93.5" height="48" preserveAspectRatio="none" xlink:href="{uri(img)}"/>')
    o.append(t('UNSERE KUNDEN & PARTNER', 3.55, 95.3, 201.0, C_DARK, 'serif_logo', tr=0.2))
    o.append(f'<path d="M95.3,204.5 H116.6" stroke="{C_GOLD}" stroke-width="0.5"/>')
    kund = ['Wir betreuen Unternehmen und Einrichtungen', 'aus unterschiedlichsten Branchen – von',
            'Büroimmobilien und Business-Center über', 'Praxen und medizinische Versorgungszentren',
            'bis hin zu Kanzleien, IT-Unternehmen, Studios', 'und weiteren gewerblichen Kunden.']
    for i, ln in enumerate(kund):
        o.append(t(ln, 2.05, 95.3, 211.4 + i * 4.38, C_TEXT))
    o.append(f'<circle cx="186.7" cy="219.6" r="13.2" fill="none" stroke="{C_GOLD}" stroke-width="0.4"/>')
    o.append(icon('personen', 186.7, 220.0, 15.5, C_GOLD, sw=1.1))
    o.append(f'<rect x="7" y="239.8" width="196" height="7" rx="3.5" fill="{C_DARK}"/>')
    o.append(t('QUALITÄT   •   VERTRAUEN   •   ZUVERLÄSSIGKEIT   •   NACHHALTIGKEIT   •   INNOVATION   •   PARTNERSCHAFT',
               1.85, 105, 244.25, C_WHITE, 'sans_medium', anchor='middle', tr=0.22))

    # --- Fußbereich (Inhalt leicht nach unten zentriert)
    FY = 3.0
    o.append(f'<rect x="-3" y="249.2" width="{W + 6}" height="{H - 249.2 + 3}" fill="{C_FOOT}"/>')
    o.append(f'<path d="M153.5,249.2 H{W + 3} V{H + 3} H145.5 Z" fill="{C_CREAM}"/>')
    o.append(t('KONTAKT', 3.4, 9.6, 257.7 + FY, C_WHITE, 'serif_logo', tr=0.3))
    for i, (k, txt) in enumerate((('pin', 'Böblingen und Umgebung'), ('phone', '0170 1601830'),
                                  ('mail', 'info@gts-boeblingen.de'), ('globe', 'www.gts-boeblingen.de'))):
        yy = 265.4 + FY + i * 6.0
        cap = 2.3 if k == 'pin' else 2.5              # Telefon / E-Mail / Web etwas größer
        o.append(globe(12.1, yy - 1.2, 1.55, C_GOLD_LT) if k == 'globe'
                 else filled_icon(k, 12.1, yy - 1.2, 3.7, C_GOLD_LT))
        o.append(t(txt, cap, 16.8, yy, C_WHITE, 'sans' if k == 'pin' else 'sans_medium'))
    o.append(qr_code(65.0, 254.6 + FY, 22.5, URL))
    o.append(t('QR-Code scannen', 1.6, 76.25, 282.4 + FY, C_WHITE, 'sans_medium', anchor='middle'))
    o.append(f'<path d="M92.0,{253.7 + FY} V{283.6 + FY}" stroke="{C_GOLD_LT}" stroke-width="0.3"/>')
    o.append(t('\u201C', 13.0, 94.8, 268.5 + FY, C_GOLD_LT, 'serif_logo'))
    for i, (ln, col) in enumerate((('Vertrauen ist der Anfang', C_WHITE), ('jeder erfolgreichen', C_WHITE),
                                   ('Zusammenarbeit.', C_WHITE), ('Lassen Sie uns gemeinsam', C_GOLD_LT),
                                   ('Maßstäbe setzen.', C_GOLD_LT))):
        o.append(t(ln, 2.05, 103.8, 262.0 + FY + i * 4.45, col, skew=-11))
    o.append(t('LASSEN SIE UNS INS', 2.85, 157.5, 257.3 + FY, C_DARK, 'serif_logo', tr=0.2))
    o.append(t('GESPRÄCH KOMMEN.', 2.85, 157.5, 262.8 + FY, C_DARK, 'serif_logo', tr=0.2))
    o.append(t('Wir beraten Sie persönlich und finden', 1.5, 157.5, 268.4 + FY, C_TEXT))
    o.append(t('die passende Lösung für Ihre Anforderungen.', 1.5, 157.5, 272.2 + FY, C_TEXT))
    o.append(f'<rect x="157.5" y="{275.8 + FY}" width="47.5" height="6.6" rx="3.3" fill="{C_GOLD}"/>')
    o.append(t('JETZT TERMIN VEREINBAREN', 1.55, 181.25, 279.9 + FY, '#FFFFFF', 'sans_semi', anchor='middle', tr=0.2))

    defs = gold_gradient('goldDark', 6, 5, 20, 20, [(0, '#D8BC8A'), (0.45, '#A9844E'), (0.75, '#CDAE78'), (1, '#B08D58')])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W + 2 * B}mm" height="{H + 2 * B}mm" viewBox="-3 -3 {W + 2 * B} {H + 2 * B}">'
            f'<defs>{defs}</defs>{"".join(o)}</svg>')


if __name__ == '__main__':
    pages = [('Vorderseite', herbst_svg()), ('Rueckseite', back_svg())]
    merged = PdfWriter()
    for name, svg in pages:
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=f'herbst2_{name}_rgb.pdf')
        merged.add_page(PdfReader(f'herbst2_{name}_rgb.pdf').pages[0])
    merged.write('herbst2_rgb.pdf')
    raw = 'herbst2_cmyk_raw.pdf'
    subprocess.run(['gs', '-q', '-dNOPAUSE', '-dBATCH', '-dSAFER', '-sDEVICE=pdfwrite', '-o', raw,
                    '-dCompatibilityLevel=1.6', '-dPDFSETTINGS=/prepress', '-sColorConversionStrategy=CMYK',
                    '-sProcessColorModel=DeviceCMYK', '-dAutoRotatePages=/None', '-dAutoFilterColorImages=false',
                    '-dColorImageFilter=/DCTEncode', '-dDownsampleColorImages=false', '-f', 'herbst2_rgb.pdf'], check=True)
    MM = 72 / 25.4
    media = RectangleObject([0, 0, (W + 2 * B) * MM, (H + 2 * B) * MM])
    trim = RectangleObject([B * MM, B * MM, (W + B) * MM, (H + B) * MM])
    w = PdfWriter()
    for pg_ in PdfReader(raw).pages:
        w.add_page(pg_)
        pg = w.pages[-1]
        pg.mediabox = pg.cropbox = pg.bleedbox = media
        pg.trimbox = trim
    w.add_metadata({'/Title': 'GTS Herbst-Flyer A4 beidseitig (Seite 1 vorne, Seite 2 hinten; 3 mm Beschnitt, CMYK)',
                    '/Author': 'GTS Gebäude Technik Service'})
    pdf = os.path.join(OUT, 'GTS_Herbst-Flyer_A4_beidseitig.pdf')
    w.write(pdf)
    doc = pymupdf.open(pdf)
    for i, (name, _) in enumerate(pages):
        p = doc[i]
        assert not p.get_fonts()
        pix = p.get_pixmap(dpi=150, clip=p.trimbox)
        pix.save(os.path.join(OUT, f'Vorschau_Herbst-Flyer_{name}.png'))
        MMp = 72 / 25.4                                 # QR-Bereich der jeweiligen Seite (mm, Endformat)
        qx0, qy0, qx1, qy1 = [(120, 267, 148, 295), (60, 255, 93, 288)][i]
        big = p.get_pixmap(dpi=200, clip=pymupdf.Rect((qx0 + B) * MMp, (qy0 + B) * MMp, (qx1 + B) * MMp, (qy1 + B) * MMp))
        img = np.frombuffer(big.samples, np.uint8).reshape(big.h, big.w, big.n)[..., :3]
        val, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        cm = p.get_pixmap(dpi=100, colorspace=pymupdf.csCMYK)
        a = np.frombuffer(cm.samples, np.uint8).reshape(cm.h, cm.w, cm.n)[..., :4].astype(float) / 2.55
        print(name, 'QR ->', repr(val), '| max ink %.0f%%' % a.sum(2).max())
        assert val == URL
