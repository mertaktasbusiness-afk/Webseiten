"""GTS Herbst-Flyer A4 (Laubentfernung + Regenrinnenreinigung), Design wie flyer.py."""
import math, os, subprocess, sys
import numpy as np, cairosvg, pymupdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
import flyer
from flyer import t, icon, IC, filled_icon, globe, hero_image, uri, F, W, H, B
from flyer import C_CREAM, C_DARK, C_GOLD, C_GOLD_LT, C_BAND, C_PANEL, C_FOOT, C_TEXT
from gts import logo_svg, gold_gradient, arc_text

OUT = sys.argv[1] if len(sys.argv) > 1 else 'herbst_out'
os.makedirs(OUT, exist_ok=True)
C_COPPER, C_RED, C_WHITE = '#B5622A', '#8E3B1F', '#F5F2EB'


# Variante B (GTS_VARIANT=B): Fließtexte etwas größer, Kontaktdaten groß & fett
VARIANT_B = os.environ.get('GTS_VARIANT') == 'B'
if VARIANT_B:
    _t = t

    def t(text, cap, *a, **k):
        return _t(text, cap * 1.05 if cap < 2.1 else cap, *a, **k)


def big_contact(o, top, qr_top, title=False):
    """Variante B: große, fette Kontaktzeilen + QR-Code mit Hinweis daneben."""
    from gts import ink_width as _iw
    y = top
    if title:
        o.append(_t('KONTAKT', 3.2, 10.2, y, C_WHITE, 'serif_logo', tr=0.3))
        y += 6.6
    for k, txt, cap, font in (('phone', '0170 1601830', 3.4, 'sans_semi'),
                              ('mail', 'info@gts-boeblingen.de', 2.85, 'sans_semi'),
                              ('globe', 'www.gts-boeblingen.de', 2.85, 'sans_semi'),
                              ('pin', 'Böblingen und Umgebung', 2.3, 'sans')):
        ic = y - cap / 2
        sz = cap * 1.75
        o.append(globe(12.6, ic, sz * 0.42, C_GOLD_LT) if k == 'globe' else filled_icon(k, 12.6, ic, sz, C_GOLD_LT))
        o.append(_t(txt, cap, 18.5, y, C_WHITE, font, tr=0.02))
        y += cap + 2.75
    o.append(f'<path d="M84,{qr_top - 1} V{qr_top + 25}" stroke="{C_GOLD_LT}" stroke-width="0.3"/>')
    o.append(qr_code(90.0, qr_top, 24.0))
    for i, ln in enumerate(('QR-Code scannen', '& Webseite', 'besuchen')):
        o.append(_t(ln, 2.0, 118.5, qr_top + 9.5 + i * 4.3, C_GOLD_LT if i == 0 else C_WHITE, 'sans_medium'))


IC.update({
    'rechen': ['M12 2v13', 'M5 15h14', 'M5 15v5M8.5 15v5M12 15v5M15.5 15v5M19 15v5'],
    'rinne': ['M2 10l10-7 10 7', 'M3 12h18v2.5a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 14.5z',
              'M18 16v5', 'M7 19v1M11 19v2'],
    'tropfen': ['M12 2.5s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z'],
    'schnee': ['M12 2v20M3.3 7l17.4 10M3.3 17L20.7 7', 'M9.5 3.5L12 6l2.5-2.5M9.5 20.5L12 18l2.5 2.5'],
    'warn': ['M12 3l10 18H2z', 'M12 10v5', 'M12 18h.01'],
})


def leaf(cx, cy, size, rot, color):
    """Stilisiertes Blatt (Fläche + Blattader), size = Länge in mm."""
    k = size / 10
    return (f'<g transform="translate({cx},{cy}) rotate({rot}) scale({k:.4f})">'
            f'<path d="M0,-5 C3.2,-3 3.4,2.2 0,5 C-3.4,2.2 -3.2,-3 0,-5 Z" fill="{color}"/>'
            f'<path d="M0,-4.2 V6.2 M0,-1 L1.6,-2.4 M0,1 L-1.7,-0.4 M0,2.8 L1.5,1.5" stroke="{C_CREAM}" '
            f'stroke-width="0.35" fill="none" stroke-linecap="round" opacity="1"/></g>')


def autumn_badge(cx, cy, R):
    s = R / 9.5
    sans = F['sans_medium']
    o = [f'<g transform="translate({cx},{cy}) scale({s:.5f})">', f'<circle r="9.5" fill="{C_PANEL}"/>',
         f'<circle r="9.3" fill="none" stroke="#D9C7A0" stroke-width="0.26"/>']
    cap, rb = 1.3, 7.3
    size = sans.size_for_cap(cap)
    for txt, ang, bottom, span in (('HERBST-AKTION', -90, False, 150), ('LAUB · REGENRINNE', 90, True, 150)):
        r = rb + cap if bottom else rb
        gl = sans.shape(txt)
        w0 = sum(g[1] for g in gl) * size / sans.upm
        tr = (math.radians(span) * r - w0) / (len(gl) - 1)
        d, _ = arc_text(sans, txt, size, 0, 0, r, ang, tracking=tr, bottom=bottom)
        o.append(f'<path d="{d}" fill="{C_WHITE}"/>')
    for a in (180, 0):
        o.append(f'<circle cx="{(rb + cap / 2) * math.cos(math.radians(a)):.3f}" cy="0" r="0.26" fill="{C_GOLD_LT}"/>')
    o.append(leaf(-1.3, 0.3, 8.5, -28, C_COPPER))
    o.append(leaf(1.9, 0.6, 6.5, 32, '#C9A66B'))
    o.append('</g>')
    return ''.join(o)


def qr_code(x, y, size, url='https://www.gts-boeblingen.de', ecc='Q'):
    """Weißes Feld mit Goldrand + QR-Code (Fehlerkorrektur Q, 2 Module Ruhezone)."""
    import qrcode
    q = qrcode.QRCode(error_correction=getattr(qrcode.constants, 'ERROR_CORRECT_' + ecc), border=0)
    q.add_data(url)
    q.make(fit=True)
    m = q.get_matrix()
    n = len(m)
    mod = size / (n + 4)
    x0, y0 = x + 2 * mod, y + 2 * mod
    d = []
    for r in range(n):
        c = 0
        while c < n:
            if m[r][c]:
                c2 = c
                while c2 < n and m[r][c2]:
                    c2 += 1
                d.append(f'M{x0 + c * mod:.4f},{y0 + r * mod:.4f}h{(c2 - c) * mod:.4f}v{mod:.4f}h{-(c2 - c) * mod:.4f}z')
                c = c2
            else:
                c += 1
    return (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="1" fill="#FFFFFF" stroke="{C_GOLD_LT}" '
            f'stroke-width="0.35"/><path d="{"".join(d)}" fill="#000000"/>')


def herbst_svg():
    o = [f'<rect x="-3" y="-3" width="{W + 6}" height="{H + 6}" fill="{C_CREAM}"/>']
    img, x, y, w, h = hero_image()
    X = np.arange(img.shape[1]) / 12 + x                         # mm, wie in hero_image
    a = np.clip((X - 86) / 26, 0, 1)
    a = (a * a * (3 - 2 * a))[None, :, None]                      # Creme-Übergang bleibt neutral
    img = np.clip(img * (1 + a * (np.array([1.07, 1.0, 0.86], np.float32) - 1)), 0, 255)
    o.append(f'<image x="{x:.3f}" y="{y}" width="{w:.3f}" height="{h:.3f}" preserveAspectRatio="none" '
             f'xlink:href="{uri(img)}"/>')

    # --- Kopf
    s = 67.5 / (44.95 - 7.2)
    o.append(logo_svg(F, f'translate({9.8 - 7.2 * s:.3f},{8.0 - 3.25 * s:.3f}) scale({s:.4f})',
                      C_DARK, C_DARK, C_DARK, 'goldCream'))
    o.append(t('Ihr Herbst-Service:', 4.9, 10.2, 49.0, C_DARK, 'serif_med'))
    for txt, yy, col in (('Laub weg.', 60.6, C_DARK), ('Rinnen frei.', 71.8, C_COPPER), ('Winterfest.', 83.0, C_DARK)):
        o.append(t(txt, 8.1, 10.0, yy, col, 'serif_logo'))
    o.append(f'<path d="M10.2,89.8 H30.3" stroke="{C_GOLD}" stroke-width="0.45"/>')
    para = ['Wenn die Blätter fallen, sind wir für Sie da:', 'Wir befreien Rasen, Wege und Einfahrten von',
            'Laub und reinigen Regenrinnen und Fallrohre.', 'So vermeiden Sie Rutschgefahr, Verstopfungen',
            'und Feuchtigkeitsschäden – und Ihr Grundstück', 'ist bestens vorbereitet für den Winter.']
    for i, ln in enumerate(para):
        o.append(t(ln, 2.3, 10.2, 96.6 + i * 4.75, C_TEXT))
    o.append(autumn_badge(183.6, 23.9, 16.4))
    for lx, ly, ls, lr, lc in ((93, 30, 7.5, 35, C_COPPER), (101, 52, 5.0, -25, '#C9A66B'), (90, 74, 6.0, 70, C_RED),
                               (150, 50, 4.5, 15, '#C9A66B'), (160, 8, 5.5, -40, C_COPPER), (205.5, 52, 6.5, 120, C_RED)):
        o.append(leaf(lx, ly, ls, lr, lc))

    # --- Band + Checkliste
    o.append(f'<rect x="-3" y="124" width="{W + 6}" height="19" fill="{C_BAND}"/>')
    o.append(f'<path d="M120.5,106.5 H{W + 3} V143 H104.3 Z" fill="{C_PANEL}"/>')
    items = ['Laubentfernung auf Rasen, Wegen & Einfahrten', 'Reinigung von Regenrinnen & Fallrohren',
             'Auf Wunsch inkl. Abtransport des Laubs', 'Geschulte Teams & sichere Ausrüstung',
             'Für Privat- & Geschäftskunden']
    for i, it in enumerate(items):
        yy = 113.6 + i * 5.55
        o.append(icon('haken', 124.0, yy - 1.05, 3.4, C_GOLD_LT, sw=2.0))
        o.append(t(it, 2.15, 128.6, yy, C_WHITE))
    o.append(f'<circle cx="23.1" cy="133.5" r="6.2" fill="none" stroke="{C_GOLD_LT}" stroke-width="0.35"/>')
    o.append(icon('blatt', 23.1, 133.5, 6.6, C_GOLD_LT, sw=1.5))
    o.append(t('DER HERBST KOMMT.', 3.1, 34.8, 132.0, C_GOLD_LT, 'serif_logo', tr=0.12))
    o.append(t('WIR SIND BEREIT.', 3.1, 34.8, 138.0, C_WHITE, 'serif_logo', tr=0.12))
    o.append(f'<path d="M110.6,127.5 V139.5" stroke="{C_GOLD_LT}" stroke-width="0.25"/>')

    # --- Angebot: zwei Karten + Kombi
    o.append(t('UNSER HERBST-ANGEBOT', 3.8, 105, 150.8, C_DARK, 'serif_logo', anchor='middle', tr=0.55))
    o.append(f'<path d="M36,148.9 H57 M153,148.9 H174" stroke="{C_GOLD}" stroke-width="0.3"/>')
    cards = [('rechen', 'LAUBENTFERNUNG', 'Rasen · Beete · Wege · Einfahrten',
              ['Laub rechen, blasen & aufnehmen', 'Rasen und Beete schonend reinigen',
               'Gehwege, Höfe & Parkplätze', 'Auf Wunsch inkl. Abtransport']),
             ('rinne', 'REGENRINNEN-REINIGUNG', 'Dachrinnen · Fallrohre · Abläufe',
              ['Rinnen von Laub & Schmutz befreien', 'Fallrohre & Abläufe durchspülen',
               'Sichtprüfung auf Schäden', 'Sauber und ohne Rückstände'])]
    for i, (ic, title, sub, bullets) in enumerate(cards):
        x0 = 10 + i * 98
        o.append(f'<rect x="{x0}" y="155" width="92" height="50" rx="2.5" fill="#FBF8F2" stroke="{C_GOLD}" '
                 f'stroke-width="0.3"/>')
        o.append(f'<circle cx="{x0 + 12.5}" cy="167" r="7.4" fill="{C_DARK}"/>')
        o.append(icon(ic, x0 + 12.5, 167, 8.6, C_GOLD_LT, sw=1.3))
        o.append(t(title, 3.0, x0 + 24, 165.6, C_DARK, 'serif_logo', tr=0.12))
        o.append(t(sub, 1.8, x0 + 24, 171.2, C_COPPER, 'sans_semi', tr=0.05))
        for j, bl in enumerate(bullets):
            yy = 181.2 + j * 5.6
            o.append(icon('haken', x0 + 9.5, yy - 1.05, 3.4, C_GOLD, sw=2.0))
            o.append(t(bl, 2.05, x0 + 13.8, yy, C_TEXT))
    o.append(f'<rect x="10" y="208.5" width="190" height="15.5" rx="2.5" fill="{C_DARK}"/>')
    o.append(leaf(21, 216.2, 8.5, -30, C_COPPER))
    o.append(leaf(25.5, 217.2, 6.4, 25, '#C9A66B'))
    o.append(t('HERBST-KOMBI: LAUB + REGENRINNE', 2.9, 34, 214.9, C_GOLD_LT, 'serif_logo', tr=0.15))
    o.append(t('Beides zusammen buchen – ein Termin, ein Ansprechpartner, alles erledigt.', 2.0, 34, 220.5, C_WHITE))

    # --- Warum jetzt?
    o.append(f'<path d="M-3,227.5 H{W + 3}" stroke="#D8CDB9" stroke-width="0.3"/>')
    o.append(t('WARUM JETZT?', 3.3, 105, 234.8, C_DARK, 'serif_logo', anchor='middle', tr=0.5))
    o.append(f'<path d="M60,233.2 H78 M132,233.2 H150" stroke="{C_GOLD}" stroke-width="0.3"/>')
    why = [('warn', 'RUTSCHGEFAHR VERMEIDEN', ['Nasses Laub auf Wegen', 'wird schnell glatt.']),
           ('tropfen', 'WASSERSCHÄDEN VORBEUGEN', ['Verstopfte Rinnen führen', 'zu Feuchtigkeit am Haus.']),
           ('schnee', 'FIT FÜR DEN WINTER', ['Freie Abläufe, bevor', 'Frost und Schnee kommen.']),
           ('haus', 'GEPFLEGTER EINDRUCK', ['Ein sauberes Grundstück', 'für Bewohner & Kunden.'])]
    for c, (ic, title, desc) in enumerate(why):
        cx = [31.5, 80.5, 129.5, 178.5][c]
        o.append(icon(ic, cx, 242.6, 8.8, C_GOLD, sw=1.2))
        o.append(t(title, 1.8, cx, 252.2, C_DARK, 'sans_semi', anchor='middle', tr=0.06))
        for j, dl in enumerate(desc):
            o.append(t(dl, 1.8, cx, 256.7 + j * 3.85, C_TEXT, anchor='middle'))

    # --- Fußbereich
    o.append(f'<rect x="-3" y="266" width="{W + 6}" height="{H - 266 + 3}" fill="{C_FOOT}"/>')
    o.append(f'<path d="M151.5,266 H{W + 3} V{H + 3} H147.5 Z" fill="{C_CREAM}"/>')
    if VARIANT_B:
        big_contact(o, 273.4, 268.8)
    else:
        o.append(t('KONTAKT', 2.75, 10.2, 272.6, C_WHITE, 'serif_logo', tr=0.3))
        for i, (k, txt) in enumerate((('pin', 'Böblingen und Umgebung'), ('phone', '0170 1601830'),
                                      ('mail', 'info@gts-boeblingen.de'), ('globe', 'www.gts-boeblingen.de'))):
            yy = 278.4 + i * 4.45
            cap = 2.05 if k == 'pin' else 2.25            # Telefon / E-Mail / Web etwas größer
            o.append(globe(12.2, yy - 1.05, 1.4, C_GOLD_LT) if k == 'globe' else filled_icon(k, 12.2, yy - 1.05, 3.4, C_GOLD_LT))
            o.append(t(txt, cap, 17.0, yy, C_WHITE, 'sans' if k == 'pin' else 'sans_medium'))
        o.append(f'<path d="M68.5,269.5 V292.5" stroke="{C_GOLD_LT}" stroke-width="0.25"/>')
        o.append(leaf(76.0, 280.5, 9, -25, C_COPPER))
        q = [('Herbsttermine sind', C_WHITE), ('schnell vergeben.', C_WHITE), ('Sichern Sie sich jetzt', C_GOLD_LT),
             ('Ihren Wunschtermin.', C_GOLD_LT)]
        for i, (ln, col) in enumerate(q):
            o.append(t(ln, 2.25, 83.5, 275.6 + i * 4.75, col, skew=-11))
        o.append(qr_code(124.0, 270.0, 22.0))
    o.append(t('JETZT HERBSTTERMIN', 2.7, 156.0, 273.6, C_DARK, 'serif_logo', tr=0.2))
    o.append(t('SICHERN.', 2.7, 156.0, 278.3, C_DARK, 'serif_logo', tr=0.2))
    o.append(t('Rufen Sie an oder schreiben Sie uns –', 1.55, 156.0, 283.0, C_TEXT))
    o.append(t('wir melden uns schnell bei Ihnen.', 1.55, 156.0, 286.1, C_TEXT))
    o.append(f'<rect x="156" y="288.3" width="48" height="5.2" rx="2.6" fill="{C_GOLD}"/>')
    o.append(t('JETZT ANRUFEN: 0170 1601830', 1.5, 180.0, 291.65, '#FFFFFF', 'sans_semi', anchor='middle', tr=0.15))

    defs = gold_gradient('goldCream', 7, 8, 16, 18, [(0, '#B8935C'), (0.45, '#8C6A3B'), (0.75, '#B99661'), (1, '#9B7845')])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W + 2 * B}mm" height="{H + 2 * B}mm" viewBox="-3 -3 {W + 2 * B} {H + 2 * B}">'
            f'<defs>{defs}</defs>{"".join(o)}</svg>')


if __name__ == '__main__':
    svg = herbst_svg()
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to='herbst_rgb.pdf')
    raw = 'herbst_cmyk_raw.pdf'
    subprocess.run(['gs', '-q', '-dNOPAUSE', '-dBATCH', '-dSAFER', '-sDEVICE=pdfwrite', '-o', raw,
                    '-dCompatibilityLevel=1.6', '-dPDFSETTINGS=/prepress', '-sColorConversionStrategy=CMYK',
                    '-sProcessColorModel=DeviceCMYK', '-dAutoRotatePages=/None', '-dAutoFilterColorImages=false',
                    '-dColorImageFilter=/DCTEncode', '-dDownsampleColorImages=false', '-f', 'herbst_rgb.pdf'], check=True)
    MM = 72 / 25.4
    w = PdfWriter()
    w.add_page(PdfReader(raw).pages[0])
    pg = w.pages[0]
    media = RectangleObject([0, 0, (W + 2 * B) * MM, (H + 2 * B) * MM])
    pg.mediabox = pg.cropbox = pg.bleedbox = media
    pg.trimbox = RectangleObject([B * MM, B * MM, (W + B) * MM, (H + B) * MM])
    w.add_metadata({'/Title': 'GTS Herbst-Flyer A4 (210 x 297 mm + 3 mm Beschnitt, CMYK)',
                    '/Author': 'GTS Gebäude Technik Service'})
    pdf = os.path.join(OUT, 'GTS_Herbst-Flyer_A4.pdf')
    w.write(pdf)
    p = pymupdf.open(pdf)[0]
    assert not p.get_fonts()
    p.get_pixmap(dpi=150, clip=p.trimbox).save(os.path.join(OUT, 'Vorschau_Herbst-Flyer_A4.png'))
    import cv2
    pix = p.get_pixmap(dpi=200, clip=p.trimbox)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)[..., :3]
    val, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print('QR ->', repr(val))
    assert val == 'https://www.gts-boeblingen.de'
    cm = p.get_pixmap(dpi=100, colorspace=pymupdf.csCMYK)
    a = np.frombuffer(cm.samples, np.uint8).reshape(cm.h, cm.w, cm.n)[..., :4].astype(float) / 2.55
    print('Trim mm', round(p.trimbox.width / MM, 1), round(p.trimbox.height / MM, 1), '| max ink %.0f%%' % a.sum(2).max())
