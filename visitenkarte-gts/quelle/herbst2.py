"""GTS Herbst-Flyer beidseitig: Seite 1 = Herbst-Angebot (herbst.py), Seite 2 = Leistungen/Kunden/Kontakt."""
import os, subprocess, sys
import numpy as np, cv2, cairosvg, pymupdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
import flyer
from flyer import t, icon, filled_icon, globe, uri, upscale, F, W, H, B, PX
from flyer import C_CREAM, C_DARK, C_GOLD, C_GOLD_LT, C_FOOT, C_TEXT
from gts import logo_svg, gold_gradient
from herbst import herbst_svg, qr_code, leaf, C_COPPER, C_WHITE

OUT = sys.argv[1] if len(sys.argv) > 1 else 'herbst_out'
os.makedirs(OUT, exist_ok=True)
URL = 'https://www.gts-boeblingen.de'

SERVICES = [
    ('gebaeude', ['GEBÄUDEREINIGUNG'], ['Unterhalts-, Grund-, Glas-', 'und Fassadenreinigung']),
    ('haus', ['HAUSMEISTERSERVICE'], ['Objektbetreuung und', 'Instandhaltung']),
    ('schild', ['SICHERHEIT'], ['Objektsicherung und', 'Betreuung von Ortschaften']),
    ('schluessel', ['SCHLIESSTECHNIK'], ['Zylinderwechsel und', 'Schließanlagen']),
    ('sterne', ['SPEZIALREINIGUNG'], ['Praxen, Kirchen, Studios', 'und Baustellen']),
    ('dampf', ['UNTERHALTSREINIGUNG'], ['Regelmäßige Reinigung für', 'ein gepflegtes Umfeld']),
    ('diamant', ['SONDER- & INTENSIV-', 'REINIGUNG'], ['Oberflächenveredelung', 'und Intensivpflege']),
    ('thermometer', ['TROCKENDAMPF-', 'TECHNOLOGIE'], ['Hygienisch. Chemiefrei.', 'Tiefenwirksam.']),
    ('blatt', ['NACHHALTIGE', 'REINIGUNGSSYSTEME'], ['Umweltschonend & effektiv']),
    ('tablet', ['DIGITALE', 'QUALITÄTSKONTROLLE'], ['Transparenz & Kontrolle', 'in Echtzeit']),
    ('chip', ['KI-GESTÜTZTE', 'VERWALTUNGSPROZESSE'], ['Effizient. Organisiert.', 'Zukunftsorientiert.']),
    ('chart', ['WIRTSCHAFTLICH', 'SINNVOLL'], ['Effiziente Lösungen für', 'nachhaltigen Werterhalt']),
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
    o = [f'<rect x="-3" y="-3" width="{W + 6}" height="{H + 6}" fill="{C_CREAM}"/>']
    # --- Kopf
    o.append(f'<rect x="-3" y="-3" width="{W + 6}" height="41" fill="{C_FOOT}"/>')
    s = 62 / (44.95 - 7.2)
    o.append(logo_svg(F, f'translate({12 - 7.2 * s:.3f},{9.5 - 3.25 * s:.3f}) scale({s:.4f})',
                      C_WHITE, C_WHITE, C_WHITE, 'goldDark'))
    o.append(t('Ihr Partner für', 3.0, 198, 17.5, C_WHITE, 'serif_med', anchor='end'))
    o.append(t('Sauberkeit. Technik.', 4.6, 198, 25.5, C_GOLD_LT, 'serif_logo', anchor='end'))
    o.append(t('Zuverlässigkeit.', 4.6, 198, 32.0, C_WHITE, 'serif_logo', anchor='end'))
    o.append(f'<path d="M-3,38 H{W + 3}" stroke="{C_GOLD_LT}" stroke-width="0.6"/>')

    # --- Leistungen
    o.append(t('UNSERE LEISTUNGEN', 3.8, 105, 53.0, C_DARK, 'serif_logo', anchor='middle', tr=0.6))
    o.append(f'<path d="M38,51.2 H60 M150,51.2 H172" stroke="{C_GOLD}" stroke-width="0.3"/>')
    cols = [31.5, 80.5, 129.5, 178.5]
    for i, (ic, title, desc) in enumerate(SERVICES):
        cx, iy = cols[i % 4], 70 + (i // 4) * 40.5
        o.append(f'<circle cx="{cx}" cy="{iy}" r="8.2" fill="none" stroke="{C_GOLD}" stroke-width="0.3"/>')
        o.append(icon(ic, cx, iy, 9.4, C_GOLD, sw=1.15))
        ty = iy + 14.5
        for j, tl in enumerate(title):
            o.append(t(tl, 1.8, cx, ty + j * 3.6, C_DARK, 'sans_semi', anchor='middle', tr=0.1))
        dy = ty + (len(title) - 1) * 3.6 + 4.6
        for j, dl in enumerate(desc):
            o.append(t(dl, 1.68, cx, dy + j * 3.75, C_TEXT, anchor='middle'))

    # --- Kunden & Partner
    o.append(f'<path d="M-3,186 H{W + 3}" stroke="#D8CDB9" stroke-width="0.3"/>')
    img = lounge(81.0, 58.0)
    o.append(f'<image x="-3" y="186" width="81" height="58" preserveAspectRatio="none" xlink:href="{uri(img)}"/>')
    o.append(t('UNSERE KUNDEN & PARTNER', 3.2, 86.0, 197.0, C_DARK, 'serif_logo', tr=0.25))
    o.append(f'<path d="M86,200.6 H106" stroke="{C_GOLD}" stroke-width="0.4"/>')
    kund = ['Wir betreuen unter anderem Unternehmen aus der',
            'Automobilbranche wie McLaren und Porsche, Bau-',
            'gesellschaften, Praxen, Kirchen, Studios, Gemein-',
            'schaftspraxen, Ärztehäuser, Medizinische Versor-',
            'gungszentren, Co-Working-Büros, Business-Center,',
            'hochwertige Büromobilien, Kanzleien, Ingenieur- und',
            'Architekturbüros, IT-Unternehmen und weitere',
            'gewerbliche Kunden.']
    for i, ln in enumerate(kund):
        o.append(t(ln, 1.75, 86.0, 207.0 + i * 4.1, C_TEXT))
    o.append(f'<circle cx="182" cy="222" r="12" fill="none" stroke="{C_GOLD}" stroke-width="0.35"/>')
    o.append(icon('personen', 182, 222.4, 14, C_GOLD, sw=1.1))
    o.append(f'<rect x="10" y="247" width="190" height="5.4" rx="2.7" fill="{C_DARK}"/>')
    o.append(t('QUALITÄT  ·  VERTRAUEN  ·  ZUVERLÄSSIGKEIT  ·  NACHHALTIGKEIT  ·  INNOVATION  ·  PARTNERSCHAFT',
               1.4, 105, 250.35, C_WHITE, 'sans_semi', anchor='middle', tr=0.15))

    # --- Fußbereich
    o.append(f'<rect x="-3" y="257" width="{W + 6}" height="{H - 257 + 3}" fill="{C_FOOT}"/>')
    o.append(f'<path d="M148,257 H{W + 3} V{H + 3} H142 Z" fill="{C_CREAM}"/>')
    o.append(t('KONTAKT', 2.7, 10.2, 266.0, C_WHITE, 'serif_logo', tr=0.3))
    for i, (k, txt) in enumerate((('pin', 'Böblingen und Umgebung'), ('phone', '0170 1601830'),
                                  ('mail', 'info@gts-boeblingen.de'), ('globe', 'www.gts-boeblingen.de'))):
        yy = 272.5 + i * 4.8
        o.append(globe(12.3, yy - 0.95, 1.3, C_GOLD_LT) if k == 'globe' else filled_icon(k, 12.3, yy - 0.95, 3.1, C_GOLD_LT))
        o.append(t(txt, 1.85, 17.0, yy, C_WHITE))
    o.append(qr_code(64.0, 263.5, 22.0, URL))
    o.append(t('Webseite scannen', 1.35, 75.0, 289.8, C_GOLD_LT, 'sans_semi', anchor='middle', tr=0.1))
    o.append(f'<path d="M92,262 V288" stroke="{C_GOLD_LT}" stroke-width="0.25"/>')
    o.append(t('“', 13.0, 96.5, 275.0, C_GOLD_LT, 'serif_logo'))
    for i, (ln, col) in enumerate((('Vertrauen ist der Anfang', C_WHITE), ('jeder erfolgreichen', C_WHITE),
                                   ('Zusammenarbeit.', C_WHITE), ('Lassen Sie uns gemeinsam', C_GOLD_LT),
                                   ('Maßstäbe setzen.', C_GOLD_LT))):
        o.append(t(ln, 1.85, 106.5, 266.0 + i * 4.1, col, skew=-11))
    o.append(t('LASSEN SIE UNS INS', 2.5, 152.0, 266.0, C_DARK, 'serif_logo', tr=0.2))
    o.append(t('GESPRÄCH KOMMEN.', 2.5, 152.0, 270.3, C_DARK, 'serif_logo', tr=0.2))
    o.append(t('Wir beraten Sie persönlich und finden', 1.45, 152.0, 275.3, C_TEXT))
    o.append(t('die passende Lösung für Ihre Anforderungen.', 1.45, 152.0, 278.2, C_TEXT))
    o.append(f'<rect x="152" y="282" width="50" height="5.2" rx="2.6" fill="{C_GOLD}"/>')
    o.append(t('JETZT TERMIN VEREINBAREN', 1.4, 177.0, 285.3, '#FFFFFF', 'sans_semi', anchor='middle', tr=0.2))

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
        big = p.get_pixmap(dpi=200, clip=p.trimbox)
        img = np.frombuffer(big.samples, np.uint8).reshape(big.h, big.w, big.n)[..., :3]
        val, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        cm = p.get_pixmap(dpi=100, colorspace=pymupdf.csCMYK)
        a = np.frombuffer(cm.samples, np.uint8).reshape(cm.h, cm.w, cm.n)[..., :4].astype(float) / 2.55
        print(name, 'QR ->', repr(val), '| max ink %.0f%%' % a.sum(2).max())
        assert val == URL
