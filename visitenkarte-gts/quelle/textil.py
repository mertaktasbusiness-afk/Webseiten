"""Druckdaten für die GTS-Arbeitskleidung (T-Shirt): Brust, Rücken, Ärmel + Positionierungsplan.
Vektoren in Originalgröße (mm), transparenter Hintergrund, Volltonfarben (kein Verlauf)."""
import os, sys
import cairosvg
from gts import *

OUT = sys.argv[1] if len(sys.argv) > 1 else 'textil_out'
os.makedirs(OUT, exist_ok=True)
F = load_fonts()

TX_WHITE = '#FFFFFF'
TX_GOLD = '#C9A66B'
SHIRT = '#12291E'
GOLD_DEF = gold_gradient('gSolid', 0, 0, 1, 1, [(0, TX_GOLD), (1, TX_GOLD)])

# Logo-Ausdehnung in Logo-Koordinaten (mm im Mockup): Bogen links .. Slogan rechts, Ring oben .. Bogen unten
LX0, LX1, LY0, LY1 = 7.2, 44.95, 3.25, 18.1


def doc(w, h, body, defs=GOLD_DEF, bg=None):
    rect = f'<rect x="0" y="0" width="{w}" height="{h}" fill="{bg}"/>' if bg else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">'
            f'<defs>{defs}</defs>{rect}{body}</svg>')


def logo(x, y, width):
    s = width / (LX1 - LX0)
    return logo_svg(F, f'translate({x - LX0 * s:.4f},{y - LY0 * s:.4f}) scale({s:.5f})',
                    TX_WHITE, TX_WHITE, TX_WHITE, 'gSolid'), (LY1 - LY0) * s


# ---- Icons (24er Raster, Konturstil) ----
ICONS = {
    'haus': ['M3 11 L12 3.5 L21 11', 'M5.5 9.2 V20.5 H18.5 V9.2', 'M10 20.5 V14.5 H14 V20.5'],
    'werkzeug': ['M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94'
                 'l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z'],
    'schild': ['M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z', 'M8.8 12.2l2.2 2.2 4.2-4.4'],
    'blatt': ['M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z',
              'M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12'],
}


def icon(name, cx, cy, size, sw=1.5, color=TX_GOLD):
    k = size / 24
    paths = ''.join(f'<path d="{d}"/>' for d in ICONS[name])
    return (f'<g transform="translate({cx - 12 * k:.4f},{cy - 12 * k:.4f}) scale({k:.5f})" fill="none" '
            f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{paths}</g>')


def script_line(text, cx, y, ink_w):
    sc = F['script']
    size = sc.size_for_cap(10)
    w, _ = ink_width(sc, text, size, 0.05)
    size *= ink_w / w
    d, bb, _ = text_run(sc, text, size, cx, y, 0.05 * size / 4, anchor='middle')
    sw = size * 0.012
    return f'<path d="{d}" fill="{TX_GOLD}" stroke="{TX_GOLD}" stroke-width="{sw:.3f}" stroke-linejoin="round"/>', size


# ---- 1) Brust links: 100 mm breit ----
def brust():
    w = 100.0
    g, h = logo(0, 0, w)
    return doc(w, round(h + 0.5, 1), g), w, h


# ---- 2) Rücken: 280 mm breit ----
def ruecken():
    W = 280.0
    g, h = logo(15, 0, 250)
    parts = [g]
    l1, size = script_line('Sauberkeit. Technik.', W / 2, h + 38, 165)
    l2, _ = script_line('Zuverlässigkeit.', W / 2 + 4, h + 38 + size * 0.95, 125)
    parts += [l1, l2]
    iy = h + 38 + size * 0.95 + 42
    for i, n in enumerate(['haus', 'werkzeug', 'schild', 'blatt']):
        parts.append(icon(n, W / 2 + (i - 1.5) * 46, iy, 28))
    H = iy + 15
    return doc(W, round(H, 1), ''.join(parts)), W, H


# ---- 3) Ärmel rechts: Schild 60 mm hoch ----
def aermel():
    Hh = 60.0
    k = Hh / 21.0                                  # Schild im 24er Raster: y 1.5..22.5
    ww = 17.6 * k
    body = (f'<g transform="translate({-3.2 * k:.3f},{-1.5 * k:.3f}) scale({k:.4f})" fill="none" stroke="{TX_GOLD}" '
            f'stroke-linecap="round" stroke-linejoin="round">'
            f'<path stroke-width="1.15" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
            f'<path stroke-width="0.8" d="M12 19.2s5.6-2.9 5.6-7.4V6.6L12 4.5 6.4 6.6v5.2c0 4.5 5.6 7.4 5.6 7.4z"/>'
            f'<path stroke-width="1.15" d="M9.2 11.8l2 2 3.8-4"/></g>')
    return doc(round(ww, 1), Hh, body), ww, Hh


def export(name, svg, w_mm):
    open(os.path.join(OUT, name + '.svg'), 'w').write(svg)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=os.path.join(OUT, name + '.pdf'))
    cairosvg.svg2png(bytestring=svg.encode(), write_to=os.path.join(OUT, name + '_300dpi.png'),
                     output_width=int(round(w_mm / 25.4 * 300)))


motifs = {}
for key, fn, label in (('brust', brust, 'GTS_Shirt_Brust-links_100mm'),
                       ('ruecken', ruecken, 'GTS_Shirt_Ruecken_280mm'),
                       ('aermel', aermel, 'GTS_Shirt_Aermel-rechts_60mm')):
    svg, w, h = fn()
    export(label, svg, w)
    motifs[key] = (svg, w, h)
    print(f'{label}: {w:.0f} x {h:.0f} mm')


# ---- Positionierungsplan (A4 quer) ----
def txt(t, x, y, cap, color, font='sans', anchor='start', tr=0.0):
    f = F[font]
    d, _, _ = text_run(f, t, f.size_for_cap(cap), x, y, tr, anchor=anchor)
    return f'<path d="{d}" fill="{color}"/>'


def embed(svg, x, y, scale):
    inner = svg.split('</defs>', 1)[1].rsplit('</svg>', 1)[0]
    return f'<g transform="translate({x},{y}) scale({scale})">{inner}</g>'


PW, PH = 297, 210
b = [f'<rect width="{PW}" height="{PH}" fill="#0E2419"/>']
b.append(txt('GTS ARBEITSKLEIDUNG – DRUCKDATEN & POSITIONEN', 18, 22, 4.2, TX_WHITE, 'sans_medium', tr=0.6))
b.append(f'<path d="M18,28 L80,28" stroke="{TX_GOLD}" stroke-width="0.5"/>')
cols = [('brust', 'BRUST LINKS', ['Breite: 10 cm', 'Links auf der Brust (vom Träger aus)', 'ca. 8 cm unter der Schulternaht', 'ca. 10 cm neben der Mitte']),
        ('ruecken', 'RÜCKEN', ['Breite: 28 cm', 'Mittig auf dem Rücken', 'Oberkante ca. 8 cm unter', 'der Kragennaht']),
        ('aermel', 'ÄRMEL RECHTS', ['Höhe: 6 cm', 'Rechter Ärmel, außen mittig', 'ca. 4 cm über dem Ärmelsaum', ''])]
for i, (key, title, lines) in enumerate(cols):
    x0 = 18 + i * 91
    b.append(f'<rect x="{x0}" y="38" width="83" height="100" rx="3" fill="{SHIRT}" stroke="#2C4A3A" stroke-width="0.4"/>')
    svg, w, h = motifs[key]
    sc = min(70 / w, 80 / h)
    b.append(embed(svg, x0 + 41.5 - w * sc / 2, 88 - h * sc / 2, sc))
    b.append(txt(title, x0, 150, 3.0, TX_GOLD, 'sans_medium', tr=0.4))
    for j, ln in enumerate(lines):
        if ln:
            b.append(txt(ln, x0, 158 + j * 6.2, 2.3, '#E8E3D8'))
b.append(txt('Farben: Weiß #FFFFFF  ·  Gold #C9A66B (z. B. Pantone 7503 C oder Gold-Metallic)  ·  Textil: dunkelgrün', 18, 192, 2.2, '#BFC9C2'))
b.append(txt('Alle Motive liegen in Originalgröße als PDF/SVG (Vektor) und als PNG 300 dpi mit transparentem Hintergrund bei.', 18, 199, 2.2, '#BFC9C2'))
plan = doc(PW, PH, ''.join(b))
cairosvg.svg2pdf(bytestring=plan.encode(), write_to=os.path.join(OUT, 'GTS_Arbeitskleidung_Positionierungsplan.pdf'))
cairosvg.svg2png(bytestring=plan.encode(), write_to=os.path.join(OUT, 'GTS_Arbeitskleidung_Positionierungsplan.png'),
                 output_width=2400)
print('ok')
