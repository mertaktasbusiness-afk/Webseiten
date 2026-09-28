"""GTS Flyer A4 (210 x 297 mm + 3 mm Beschnitt) nach dem Mockup flyer_mockup.jpg.
Alle Texte/Icons als Vektorpfade, Fotos aus dem Mockup; Ausgabe als CMYK-PDF."""
import base64, io, math, os, subprocess, sys
import numpy as np, cv2, cairosvg, pymupdf
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
from gts import *

OUT = sys.argv[1] if len(sys.argv) > 1 else 'flyer_out'
os.makedirs(OUT, exist_ok=True)
W, H, B = 210.0, 297.0, 3.0
F = load_fonts()
F['sans_semi'] = Font('montserrat-latin-600-normal.ttf')
F['serif_med'] = Font('cormorant-garamond-latin-500-normal.ttf')

C_CREAM, C_DARK, C_GOLD, C_GOLD_LT = '#F1ECE3', '#0F2A1E', '#A07C48', '#C8A874'
C_BAND, C_PANEL, C_FOOT, C_TEXT = '#183A2B', '#0F2A1E', '#10291D', '#34403A'
PX = 210 / 1073                                   # mm pro Mockup-Pixel

mock = cv2.cvtColor(cv2.imread('flyer_mockup.jpg'), cv2.COLOR_BGR2RGB).astype(np.float32)


def uri(img):
    b = io.BytesIO()
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(b, 'JPEG', quality=95)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()


def upscale(img, f):
    big = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_LANCZOS4)
    bl = cv2.GaussianBlur(big, (0, 0), 1.8)
    return np.clip(big + 0.6 * (big - bl), 0, 255)


# ------------------------------------------------------------------ Texte
def t(text, cap, x, y, color, font='sans', anchor='start', tr=0.0, skew=0.0):
    f = F[font]
    d, bb, _ = text_run(f, text, f.size_for_cap(cap), x, y, tr, anchor=anchor)
    tf = f' transform="translate({x},{y}) skewX({skew}) translate({-x},{-y})"' if skew else ''
    return f'<path d="{d}" fill="{color}"{tf}/>'


# ------------------------------------------------------------------ Icons (24er Raster, Kontur)
IC = {
    'gebaeude': ['M3 21h14', 'M5 21V5h9v16', 'M8 8h1M11 8h1M8 11h1M11 11h1M8 14h1M11 14h1', 'M14 11h4v10h-1',
                 'M19 3l.6 1.4L21 5l-1.4.6L19 7l-.6-1.4L17 5l1.4-.6z', 'M21 9l.4.9.9.4-.9.4-.4.9-.4-.9-.9-.4.9-.4z'],
    'haus': ['M3 11 L12 3.5 L21 11', 'M5.5 9.2 V20.5 H18.5 V9.2', 'M10 20.5 V14.5 H14 V20.5'],
    'schild': ['M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z', 'M8.8 12.2l2.2 2.2 4.2-4.4'],
    'schluessel': ['M11.5 13.5a4.5 4.5 0 1 1-6.36 6.36 4.5 4.5 0 0 1 6.36-6.36z', 'M11.5 13.5L21 4',
                   'M17.5 7.5l2.5 2.5', 'M15 10l2 2'],
    'sterne': ['M10 4l1.6 4.4L16 10l-4.4 1.6L10 16l-1.6-4.4L4 10l4.4-1.6z',
               'M18 13l.9 2.1 2.1.9-2.1.9-.9 2.1-.9-2.1-2.1-.9 2.1-.9z', 'M18 2.5l.7 1.6 1.6.7-1.6.7-.7 1.6-.7-1.6-1.6-.7 1.6-.7z'],
    'dampf': ['M7 3c-2 2.5 2 4.5 0 7s2 4.5 0 7 2 3.5 0 4', 'M12 3c-2 2.5 2 4.5 0 7s2 4.5 0 7 2 3.5 0 4',
              'M17 3c-2 2.5 2 4.5 0 7s2 4.5 0 7 2 3.5 0 4'],
    'diamant': ['M6 3h12l4 6-10 12L2 9z', 'M2 9h20', 'M9 3l-1 6 4 12 4-12-1-6'],
    'thermometer': ['M13 14.76V4.5a2.5 2.5 0 0 0-5 0v10.26a4.5 4.5 0 1 0 5 0z', 'M10.5 17.5V9',
                    'M16 5h3M16 8h2M16 11h3'],
    'blatt': ['M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z',
              'M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12'],
    'tablet': ['M7 2h10a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z', 'M11 18.5h2'],
    'chip': ['M7 6h10a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1z', 'M9.5 9.5h5v5h-5z',
             'M9 2v4M12 2v4M15 2v4M9 18v4M12 18v4M15 18v4M2 9h4M2 12h4M2 15h4M18 9h4M18 12h4M18 15h4'],
    'chart': ['M3 21h18', 'M6 21v-4M10 21v-7M14 21v-5M18 21v-9', 'M4 13l5-5 4 3 7-7', 'M16 4h4v4'],
    'hand': ['m11 17 2 2a1 1 0 1 0 3-3',
             'm14 14 2.5 2.5a1 1 0 1 0 3-3l-3.88-3.88a3 3 0 0 0-4.24 0l-.88.88a1 1 0 1 1-3-3l2.81-2.81'
             'a5.79 5.79 0 0 1 7.06-.87l.47.28a2 2 0 0 0 1.42.25L21 4', 'm21 3 1 11h-2',
             'M3 3 2 14l6.5 6.5a1 1 0 1 0 3-3', 'M3 4h8'],
    'personen': ['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2', 'M9 3a4 4 0 1 1 0 8 4 4 0 0 1 0-8z',
                 'M22 21v-2a4 4 0 0 0-3-3.87', 'M16 3.13a4 4 0 0 1 0 7.75'],
    'haken': ['M4 12.5l5 5L20 6.5'],
}


def icon(name, cx, cy, size, color, sw=1.3):
    k = size / 24
    p = ''.join(f'<path d="{d}"/>' for d in IC[name])
    return (f'<g transform="translate({cx - 12 * k:.3f},{cy - 12 * k:.3f}) scale({k:.5f})" fill="none" '
            f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{p}</g>')


def filled_icon(kind, cx, cy, s, color):
    k = s / 24
    d = {'phone': 'M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 '
                  '3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 '
                  '1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z',
         'pin': 'M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12'
                '-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z',
         'mail': 'M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4-8 5-8-5V6l8 5 8-5v2z'}[kind]
    return (f'<path transform="translate({cx - 12 * k:.3f},{cy - 12 * k:.3f}) scale({k:.5f})" fill="{color}" '
            f'fill-rule="evenodd" d="{d}"/>')


def globe(cx, cy, r, color):
    sw = r * 0.16
    return (f'<g fill="none" stroke="{color}" stroke-width="{sw:.3f}"><circle cx="{cx}" cy="{cy}" r="{r}"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{r * 0.45:.3f}" ry="{r}"/>'
            f'<path d="M{cx - r},{cy} H{cx + r} M{cx - r * .85:.3f},{cy - r * .5:.3f} H{cx + r * .85:.3f} '
            f'M{cx - r * .85:.3f},{cy + r * .5:.3f} H{cx + r * .85:.3f}"/></g>')


# ------------------------------------------------------------------ Siegel (wie Visitenkarte)
def badge(cx, cy, R):
    s = R / 9.5
    sans = F['sans_medium']
    o = [f'<g transform="translate({cx},{cy}) scale({s:.5f})">',
         f'<circle r="9.5" fill="{C_PANEL}"/>',
         f'<circle r="9.3" fill="none" stroke="#D9C7A0" stroke-width="0.26"/>']
    cap, rb = 1.22, 7.35
    size = sans.size_for_cap(cap)
    top = 'QUALITÄT · ZUVERLÄSSIGKEIT'
    gl = sans.shape(top)
    w0 = sum(g[1] for g in gl) * size / sans.upm
    tr = (math.radians(198) * rb - w0) / (len(gl) - 1)
    d, _ = arc_text(sans, top, size, 0, 0, rb, -90, tracking=tr)
    o.append(f'<path d="{d}" fill="#F5F2EB"/>')
    bt = 'NACHHALTIGKEIT'
    wb = sum(g[1] for g in sans.shape(bt)) * size / sans.upm
    d, _ = arc_text(sans, bt, size, 0, 0, rb + cap, 90, tracking=(math.radians(104) * (rb + cap) - wb) / (len(bt) - 1),
                    bottom=True)
    o.append(f'<path d="{d}" fill="#F5F2EB"/>')
    rm = rb + cap / 2
    for a in (156.5, 23.5):
        o.append(f'<circle cx="{rm * math.cos(math.radians(a)):.3f}" cy="{rm * math.sin(math.radians(a)):.3f}" '
                 f'r="0.24" fill="{C_GOLD_LT}"/>')
    p = lambda x, y, sc=1, oy=0: f'{x * sc:.3f},{oy + y * sc:.3f}'

    def shield(sc, oy=0.0):
        return (f'M{p(0, -4.95, sc, oy)} C{p(1.4, -4.0, sc, oy)} {p(2.9, -3.9, sc, oy)} {p(4.15, -3.85, sc, oy)} '
                f'L{p(4.15, -0.2, sc, oy)} C{p(4.15, 2.6, sc, oy)} {p(2.3, 4.0, sc, oy)} {p(0, 5.05, sc, oy)} '
                f'C{p(-2.3, 4.0, sc, oy)} {p(-4.15, 2.6, sc, oy)} {p(-4.15, -0.2, sc, oy)} L{p(-4.15, -3.85, sc, oy)} '
                f'C{p(-2.9, -3.9, sc, oy)} {p(-1.4, -4.0, sc, oy)} {p(0, -4.95, sc, oy)} Z')
    o.append(f'<path d="{shield(1)}" fill="url(#shieldGold)"/>')
    o.append(f'<path d="{shield(0.7, 0.15)}" fill="none" stroke="#F5F2EB" stroke-width="0.4" stroke-linejoin="round"/>')
    o.append('<path d="M-1.55,0.35 L-0.35,1.55 L1.75,-0.9" fill="none" stroke="#F5F2EB" stroke-width="0.62" '
             'stroke-linecap="round" stroke-linejoin="round"/></g>')
    return ''.join(o)


# ------------------------------------------------------------------ Fotos
def hero_image():
    """Mockup-Foto rechts oben, links weich in Creme überblendet; deckt x 83..213, y -3..125 ab."""
    x0p, x1p, y1p = 440, 1073, 655
    src = mock[0:y1p, x0p:x1p]
    f = 12 * PX                                  # -> 12 px/mm
    big = upscale(src, f)
    # 3 mm Beschnitt oben/rechts spiegeln
    pad = int(round(3 * 12))
    big = cv2.copyMakeBorder(big, pad, 0, 0, pad, cv2.BORDER_REFLECT)
    h, w = big.shape[:2]
    X = np.arange(w) / 12 + x0p * PX              # mm
    a = np.clip((X - 86) / 26, 0, 1)
    a = (a * a * (3 - 2 * a))[None, :, None]
    cream = np.array([0xF1, 0xEC, 0xE3], np.float32)
    img = big * a + cream * (1 - a)
    return img, x0p * PX, -3.0, w / 12, h / 12


def lounge_image():
    """Foto Lounge links unten: Zielbereich x -3..62.6, y 230..268."""
    tw, th = 65.6, 38.0
    src = mock[1250:1452, 0:320]
    f = 12 * PX
    big = upscale(src, f)
    h, w = big.shape[:2]
    need_w = int(round(tw * 12)); need_h = int(round(th * 12))
    # links 3 mm Beschnitt spiegeln, dann auf Zielgröße zuschneiden
    big = cv2.copyMakeBorder(big, 0, 0, int(3 * 12), 0, cv2.BORDER_REFLECT)
    sc = max(need_w / big.shape[1], need_h / big.shape[0])
    big = cv2.resize(big, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC)
    oy = (big.shape[0] - need_h) // 2
    return big[oy:oy + need_h, :need_w], -3.0, 230.0, tw, th


# ------------------------------------------------------------------ Layout
def flyer_svg():
    o = []
    o.append(f'<rect x="-3" y="-3" width="{W + 6}" height="{H + 6}" fill="{C_CREAM}"/>')
    img, x, y, w, h = hero_image()
    o.append(f'<image x="{x:.3f}" y="{y}" width="{w:.3f}" height="{h:.3f}" preserveAspectRatio="none" '
             f'xlink:href="{uri(img)}"/>')

    # --- Kopf links
    s = 67.5 / (44.95 - 7.2)
    o.append(logo_svg(F, f'translate({9.8 - 7.2 * s:.3f},{8.0 - 3.25 * s:.3f}) scale({s:.4f})',
                      C_DARK, C_DARK, C_DARK, 'goldCream'))
    o.append(t('Ihr Partner für', 4.6, 10.2, 49.5, C_DARK, 'serif_med'))
    for txt, yy, col in (('Sauberkeit.', 60.5, C_DARK), ('Technik.', 71.2, C_GOLD), ('Zuverlässigkeit.', 81.9, C_DARK)):
        o.append(t(txt, 7.6, 10.0, yy, col, 'serif_logo'))
    o.append(f'<path d="M10.2,89.3 H30.3" stroke="{C_GOLD}" stroke-width="0.45"/>')
    para = ['Wir stehen für Qualität, Zuverlässigkeit,', 'Nachhaltigkeit und kontinuierliche Innovation.',
            'Mit Meisterbrief und langjähriger Erfahrung', 'übernehmen wir Reinigungs-, Hausmeister-',
            'und Sicherheitsleistungen für Privat- und', 'Geschäftskunden.']
    for i, ln in enumerate(para):
        o.append(t(ln, 2.05, 10.2, 96.8 + i * 4.35, C_TEXT))

    o.append(badge(183.6, 23.9, 16.4))

    # --- Band + Checkliste
    o.append(f'<rect x="-3" y="124" width="{W + 6}" height="19" fill="{C_BAND}"/>')
    o.append(f'<path d="M120.5,106.5 H{W + 3} V143 H104.3 Z" fill="{C_PANEL}"/>')
    items = ['Meisterbetrieb mit Erfahrung', 'Zuverlässige & geschulte Teams', 'Moderne Technik & nachhaltige Produkte',
             'Flexibel, diskret & termintreu', 'Für Privat- & Geschäftskunden']
    for i, it in enumerate(items):
        yy = 113.6 + i * 5.55
        o.append(icon('haken', 124.0, yy - 1.05, 3.4, C_GOLD_LT, sw=2.0))
        o.append(t(it, 2.05, 128.6, yy, '#F5F2EB'))
    o.append(f'<circle cx="23.1" cy="133.5" r="6.2" fill="none" stroke="{C_GOLD_LT}" stroke-width="0.35"/>')
    o.append(icon('hand', 23.1, 133.5, 7.4, C_GOLD_LT, sw=1.5))
    o.append(t('MEHR ALS EIN DIENSTLEISTER.', 2.75, 34.8, 132.1, C_GOLD_LT, 'serif_logo', tr=0.12))
    o.append(t('EIN VERLÄSSLICHER PARTNER.', 2.75, 34.8, 137.6, '#F5F2EB', 'serif_logo', tr=0.12))
    o.append(f'<path d="M110.6,127.5 V139.5" stroke="{C_GOLD_LT}" stroke-width="0.25"/>')

    # --- Leistungen
    o.append(t('UNSERE LEISTUNGEN', 3.4, 105, 150.0, C_DARK, 'serif_logo', anchor='middle', tr=0.55))
    o.append(f'<path d="M50,148.3 H68 M142,148.3 H160" stroke="{C_GOLD}" stroke-width="0.3"/>')
    rows = [
        [('gebaeude', ['GEBÄUDEREINIGUNG'], ['Unterhalts-, Grund-, Glas-', 'und Fassadenreinigung']),
         ('haus', ['HAUSMEISTERSERVICE'], ['Objektbetreuung und', 'Instandhaltung']),
         ('schild', ['SICHERHEIT'], ['Objektsicherung und', 'Betreuung von Ortschaften']),
         ('schluessel', ['SCHLIESSTECHNIK'], ['Zylinderwechsel und', 'Schließanlagen'])],
        [('sterne', ['SPEZIALREINIGUNG'], ['Praxen, Kirchen, Studios', 'und Baustellen']),
         ('dampf', ['UNTERHALTSREINIGUNG'], ['Regelmäßige Reinigung für', 'ein gepflegtes Umfeld']),
         ('diamant', ['SONDER- & INTENSIVREINIGUNG'], ['Oberflächenveredelung', 'und Intensivpflege']),
         ('thermometer', ['TROCKENDAMPFTECHNOLOGIE'], ['Hygienisch. Chemiefrei.', 'Tiefenwirksam.'])],
        [('blatt', ['NACHHALTIGE', 'REINIGUNGSSYSTEME'], ['Umweltschonend & effektiv']),
         ('tablet', ['DIGITALE', 'QUALITÄTSKONTROLLE'], ['Transparenz & Kontrolle', 'in Echtzeit']),
         ('chip', ['KI-GESTÜTZTE', 'VERWALTUNGSPROZESSE'], ['Effizient. Organisiert.', 'Zukunftsorientiert.']),
         ('chart', ['WIRTSCHAFTLICH', 'SINNVOLL'], ['Effiziente Lösungen für', 'nachhaltigen Werterhalt'])],
    ]
    cols = [31.5, 80.5, 129.5, 178.5]
    for r, row in enumerate(rows):
        iy = 156.6 + r * 24.8
        for c, (ic, title, desc) in enumerate(row):
            cx = cols[c]
            o.append(icon(ic, cx, iy, 9.0, C_GOLD, sw=1.15))
            ty = iy + 9.4
            for j, tl in enumerate(title):
                o.append(t(tl, 1.62, cx, ty + j * 3.3, C_DARK, 'sans_semi', anchor='middle', tr=0.1))
            dy = ty + (len(title) - 1) * 3.3 + 4.0
            for j, dl in enumerate(desc):
                o.append(t(dl, 1.55, cx, dy + j * 3.45, C_TEXT, anchor='middle'))

    # --- Kunden & Partner
    o.append(f'<path d="M-3,230 H{W + 3}" stroke="#D8CDB9" stroke-width="0.3"/>')
    img, x, y, w, h = lounge_image()
    o.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="none" xlink:href="{uri(img)}"/>')
    o.append(t('UNSERE KUNDEN & PARTNER', 2.85, 67.0, 237.3, C_DARK, 'serif_logo', tr=0.25))
    kund = ['Wir betreuen unter anderem Unternehmen aus der Automobilbranche wie',
            'McLaren und Porsche, Baugesellschaften, Praxen, Kirchen, Studios,',
            'Gemeinschaftspraxen, Ärztehäuser, Medizinische Versorgungszentren,',
            'Co-Working-Büros, Business-Center, hochwertige Büromobilien,',
            'Kanzleien, Ingenieur- und Architekturbüros, IT-Unternehmen und', 'weitere gewerbliche Kunden.']
    for i, ln in enumerate(kund):
        o.append(t(ln, 1.55, 67.0, 241.9 + i * 3.25, C_TEXT))
    o.append(f'<circle cx="189.5" cy="248.0" r="11.5" fill="none" stroke="{C_GOLD}" stroke-width="0.35"/>')
    o.append(icon('personen', 189.5, 248.4, 13.5, C_GOLD, sw=1.1))
    o.append(f'<rect x="67" y="260.6" width="137" height="5.2" rx="2.6" fill="{C_DARK}"/>')
    o.append(t('QUALITÄT  ·  VERTRAUEN  ·  ZUVERLÄSSIGKEIT  ·  NACHHALTIGKEIT  ·  INNOVATION  ·  PARTNERSCHAFT',
               1.3, 135.5, 263.85, '#F5F2EB', 'sans_semi', anchor='middle', tr=0.12))

    # --- Fußbereich
    o.append(f'<rect x="-3" y="268" width="{W + 6}" height="{H - 268 + 3}" fill="{C_FOOT}"/>')
    o.append(f'<path d="M151.5,268 H{W + 3} V{H + 3} H147.5 Z" fill="{C_CREAM}"/>')
    o.append(t('KONTAKT', 2.5, 10.2, 274.6, '#F5F2EB', 'serif_logo', tr=0.3))
    rowsK = [('pin', 'Böblingen und Umgebung'), ('phone', '0170 1601830'),
             ('mail', 'info@gts-boeblingen.de'), ('globe', 'www.gts-boeblingen.de')]
    for i, (k, txt) in enumerate(rowsK):
        yy = 279.6 + i * 3.9
        o.append(globe(12.2, yy - 0.85, 1.2, C_GOLD_LT) if k == 'globe' else filled_icon(k, 12.2, yy - 0.85, 2.9, C_GOLD_LT))
        o.append(t(txt, 1.75, 16.6, yy, '#F5F2EB'))
    o.append(f'<path d="M68.5,271.5 V292.5" stroke="{C_GOLD_LT}" stroke-width="0.25"/>')
    o.append(t('“', 16.0, 75.5, 286.0, C_GOLD_LT, 'serif_logo'))
    q = [('Vertrauen ist der Anfang', '#F5F2EB'), ('jeder erfolgreichen', '#F5F2EB'), ('Zusammenarbeit.', '#F5F2EB'),
         ('Lassen Sie uns gemeinsam', C_GOLD_LT), ('Maßstäbe setzen.', C_GOLD_LT)]
    for i, (ln, col) in enumerate(q):
        o.append(t(ln, 1.95, 90.0, 275.8 + i * 3.85, col, skew=-11))
    o.append(t('LASSEN SIE UNS INS', 2.45, 156.0, 275.0, C_DARK, 'serif_logo', tr=0.2))
    o.append(t('GESPRÄCH KOMMEN.', 2.45, 156.0, 279.1, C_DARK, 'serif_logo', tr=0.2))
    o.append(t('Wir beraten Sie persönlich und finden', 1.4, 156.0, 283.2, C_TEXT))
    o.append(t('die passende Lösung für Ihre Anforderungen.', 1.4, 156.0, 285.9, C_TEXT))
    o.append(f'<rect x="156" y="288.2" width="47" height="4.6" rx="2.3" fill="{C_GOLD}"/>')
    o.append(t('JETZT TERMIN VEREINBAREN', 1.35, 179.5, 291.18, '#FFFFFF', 'sans_semi', anchor='middle', tr=0.2))

    defs = (gold_gradient('goldCream', 7, 8, 16, 18, [(0, '#B8935C'), (0.45, '#8C6A3B'), (0.75, '#B99661'), (1, '#9B7845')])
            + gold_gradient('shieldGold', -4, -5, 4, 5, [(0, '#CDAA6E'), (0.5, '#A8844D'), (1, '#86653A')]))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W + 2 * B}mm" height="{H + 2 * B}mm" viewBox="-3 -3 {W + 2 * B} {H + 2 * B}">'
            f'<defs>{defs}</defs>{"".join(o)}</svg>')


if __name__ == '__main__':
    svg = flyer_svg()
    open('flyer.svg', 'w').write(svg)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to='flyer_rgb.pdf')
    raw = 'flyer_cmyk_raw.pdf'
    subprocess.run(['gs', '-q', '-dNOPAUSE', '-dBATCH', '-dSAFER', '-sDEVICE=pdfwrite', '-o', raw,
                    '-dCompatibilityLevel=1.6', '-dPDFSETTINGS=/prepress', '-sColorConversionStrategy=CMYK',
                    '-sProcessColorModel=DeviceCMYK', '-dAutoRotatePages=/None', '-dAutoFilterColorImages=false',
                    '-dColorImageFilter=/DCTEncode', '-dDownsampleColorImages=false', '-f', 'flyer_rgb.pdf'], check=True)
    MM = 72 / 25.4
    r = PdfReader(raw)
    w = PdfWriter()
    w.add_page(r.pages[0])
    pg = w.pages[0]
    media = RectangleObject([0, 0, (W + 2 * B) * MM, (H + 2 * B) * MM])
    pg.mediabox = pg.cropbox = pg.bleedbox = media
    pg.trimbox = RectangleObject([B * MM, B * MM, (W + B) * MM, (H + B) * MM])
    w.add_metadata({'/Title': 'GTS Flyer A4 (210 x 297 mm + 3 mm Beschnitt, CMYK)', '/Author': 'GTS Gebäude Technik Service'})
    pdf = os.path.join(OUT, 'GTS_Flyer_A4.pdf')
    w.write(pdf)
    p = pymupdf.open(pdf)[0]
    assert not p.get_fonts()
    p.get_pixmap(dpi=150, clip=p.trimbox).save(os.path.join(OUT, 'Vorschau_Flyer_A4.png'))
    cm = p.get_pixmap(dpi=100, colorspace=pymupdf.csCMYK)
    a = np.frombuffer(cm.samples, np.uint8).reshape(cm.h, cm.w, cm.n)[..., :4].astype(float) / 2.55
    print('Trim mm', round(p.trimbox.width / MM, 1), round(p.trimbox.height / MM, 1), '| max ink %.0f%%' % a.sum(2).max())
