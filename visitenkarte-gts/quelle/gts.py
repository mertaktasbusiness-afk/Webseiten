"""Shared helpers: fonts -> SVG outline paths, logo, colours."""
import math
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

FONT_DIR = 'fonts/'

# ---------------------------------------------------------------- colours
DKGREEN = '#0F2A1E'      # logo / name on cream
GOLD = '#A07C48'         # gold on cream
GOLD_LT = '#C8A874'      # gold on dark green
WHITE = '#F5F2EB'        # warm white on dark green
CREAM = '#F1ECE3'


class Font:
    def __init__(self, fname):
        path = FONT_DIR + fname
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.upm = self.tt['head'].unitsPerEm
        self.cap = self.tt['OS/2'].sCapHeight
        self.order = self.tt.getGlyphOrder()
        self.hbfont = hb.Font(hb.Face(hb.Blob.from_file_path(path)))

    def size_for_cap(self, cap_mm):
        return cap_mm * self.upm / self.cap

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hbfont, buf, {'kern': True, 'liga': True})
        out = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            assert info.codepoint != 0, f'missing glyph in {text!r}'
            out.append((self.order[info.codepoint], pos.x_advance, pos.x_offset, pos.y_offset))
        return out

    def glyph_d(self, name, t):
        pen = SVGPathPen(self.gs, ntos=lambda v: ('%.4f' % v).rstrip('0').rstrip('.'))
        self.gs[name].draw(TransformPen(pen, t))
        return pen.getCommands()

    def glyph_bounds(self, name, t):
        bp = BoundsPen(self.gs)
        self.gs[name].draw(TransformPen(bp, t))
        return bp.bounds


def text_run(font, text, size, x, y, tracking=0.0, anchor='start'):
    """Return (path_d, ink_bbox, advance_width) for a single line, baseline at y (mm)."""
    k = size / font.upm
    glyphs = font.shape(text)
    adv = sum(g[1] for g in glyphs) * k + tracking * (len(glyphs) - 1)
    if anchor == 'middle':
        x -= adv / 2
    elif anchor == 'end':
        x -= adv
    d, pen_x = [], x
    bb = [1e9, 1e9, -1e9, -1e9]
    for name, xa, xo, yo in glyphs:
        t = (k, 0, 0, -k, pen_x + xo * k, y - yo * k)
        d.append(font.glyph_d(name, t))
        b = font.glyph_bounds(name, t)
        if b:
            bb = [min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3])]
        pen_x += xa * k + tracking
    return ''.join(d), bb, adv


def ink_width(font, text, size, tracking=0.0):
    _, bb, _ = text_run(font, text, size, 0, 0, tracking)
    return bb[2] - bb[0], bb[0]


def fit_tracking(font, text, size, width):
    """Tracking (mm) so that the ink width equals `width`."""
    w0, _ = ink_width(font, text, size, 0)
    n = len(font.shape(text)) - 1
    return (width - w0) / n


def text_ink(font, text, size, x0, y, tracking=0.0):
    """Place text so that its ink starts exactly at x0."""
    w, left = ink_width(font, text, size, tracking)
    d, bb, adv = text_run(font, text, size, x0 - left, y, tracking)
    return d, bb


def arc_text(font, text, size, cx, cy, r, center_deg, tracking=0.0, bottom=False):
    """Text along a circle. Angles are SVG angles (deg, clockwise, 0 = +x, -90 = top).
    Top text reads clockwise with baseline on r; bottom text reads left->right with its
    baseline on r (letters point towards the centre)."""
    k = size / font.upm
    glyphs = font.shape(text)
    widths = [g[1] * k for g in glyphs]
    total = sum(widths) + tracking * (len(glyphs) - 1)
    d, s = [], 0.0
    for (name, xa, xo, yo), w in zip(glyphs, widths):
        mid = s + w / 2
        if not bottom:
            phi = math.radians(center_deg) + (mid - total / 2) / r
            n = (math.cos(phi), math.sin(phi))          # outward = glyph up
            tv = (-math.sin(phi), math.cos(phi))       # reading direction
            up = n
        else:
            phi = math.radians(center_deg) - (mid - total / 2) / r
            n = (math.cos(phi), math.sin(phi))
            tv = (math.sin(phi), -math.cos(phi))
            up = (-n[0], -n[1])
        bx, by = cx + r * n[0], cy + r * n[1]
        # glyph units: gx along tv (centred on glyph), gy along up (svg y is down -> up vector as is)
        ox = bx - (w / 2) * tv[0]
        oy = by - (w / 2) * tv[1]
        t = (k * tv[0], k * tv[1], k * up[0], k * up[1], ox, oy)
        d.append(font.glyph_d(name, t))
        s += w + tracking
    return ''.join(d), total


def arc_length_deg(total, r):
    return math.degrees(total / r)


# ---------------------------------------------------------------- logo
# Local logo coordinates = millimetres measured on the (rectified) mockup front.
ARC_C, ARC_RO = (14.2, 11.1), 6.95
ARC_CI, ARC_RI = (14.55, 11.05), 6.25
RING_C, RING_R, RING_HOLE = (16.17, 4.53), 1.25, 0.33


def _crescent(a1, a2, notch_end=False, n=90):
    """Polygon of the logo arc between math angles a1..a2 (deg, CCW, y up)."""
    pts_o, pts_i = [], []
    for i in range(n + 1):
        a = math.radians(a1 + (a2 - a1) * i / n)
        pts_o.append((ARC_C[0] + ARC_RO * math.cos(a), ARC_C[1] - ARC_RO * math.sin(a)))
        pts_i.append((ARC_CI[0] + ARC_RI * math.cos(a), ARC_CI[1] - ARC_RI * math.sin(a)))
    pts = pts_o[:]
    if notch_end:
        a = math.radians(a2 - 3.6)
        rm = (ARC_RO + ARC_RI) / 2
        cxm = (ARC_C[0] + ARC_CI[0]) / 2
        cym = (ARC_C[1] + ARC_CI[1]) / 2
        pts.append((cxm + rm * math.cos(a), cym - rm * math.sin(a)))
    pts += pts_i[::-1]
    return 'M' + 'L'.join('%.4f,%.4f' % p for p in pts) + 'Z'


def _circle_d(cx, cy, r, ccw=False):
    s = 0 if ccw else 1
    return ('M%.4f,%.4f A%.4f,%.4f 0 1 %d %.4f,%.4f A%.4f,%.4f 0 1 %d %.4f,%.4f Z'
            % (cx - r, cy, r, r, s, cx + r, cy, r, r, s, cx - r, cy))


def ring_d():
    cx, cy = RING_C
    d = _circle_d(cx, cy, RING_R) + _circle_d(cx, cy, RING_HOLE)
    # small slit (cut) towards the upper right
    a = math.radians(38)
    ux, uy = math.cos(a), -math.sin(a)
    px, py = -uy, ux
    w = 0.065
    r0, r1 = 0.52, 1.02
    pts = [(cx + ux * r0 + px * w, cy + uy * r0 + py * w), (cx + ux * r1 + px * w, cy + uy * r1 + py * w),
           (cx + ux * r1 - px * w, cy + uy * r1 - py * w), (cx + ux * r0 - px * w, cy + uy * r0 - py * w)]
    d += 'M' + 'L'.join('%.4f,%.4f' % p for p in pts) + 'Z'
    return d


def logo_svg(fonts, transform, upper, letters, tagline_color, gold_id, tagline=True):
    """GTS logo. upper = colour of upper arc, letters = colour of 'GTS'."""
    serif, sans = fonts['serif_logo'], fonts['sans_medium']
    out = [f'<g transform="{transform}">']
    out.append(f'<path d="{_crescent(92, 183)}" fill="{upper}"/>')
    out.append(f'<path d="{_crescent(186.5, 265, notch_end=True)}" fill="url(#{gold_id})"/>')
    out.append(f'<path d="{ring_d()}" fill="url(#{gold_id})" fill-rule="evenodd"/>')
    size = serif.size_for_cap(8.5)
    tr = fit_tracking(serif, 'GTS', size, 35.2 - 12.25)
    d, _ = text_ink(serif, 'GTS', size, 12.25, 15.0, tr)
    out.append(f'<path d="{d}" fill="{letters}"/>')
    if tagline:
        tsize = sans.size_for_cap(1.02)
        ttr = fit_tracking(sans, 'GEBÄUDE · TECHNIK · SERVICE', tsize, 44.9 - 14.33)
        d, _ = text_ink(sans, 'GEBÄUDE · TECHNIK · SERVICE', tsize, 14.33, 17.83, ttr)
        out.append(f'<path d="{d}" fill="{tagline_color}"/>')
    out.append('</g>')
    return '\n'.join(out)


def gold_gradient(gid, x1, y1, x2, y2, stops):
    s = ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="{y1}" '
            f'x2="{x2}" y2="{y2}">{s}</linearGradient>')


def load_fonts():
    return {
        'serif_logo': Font('cormorant-garamond-latin-600-normal.ttf'),
        'serif_name': Font('playfair-display-latin-600-normal.ttf'),
        'sans_medium': Font('montserrat-latin-500-normal.ttf'),
        'sans': Font('montserrat-latin-400-normal.ttf'),
        'script': Font('oooh-baby-latin-400-normal.ttf'),
    }
