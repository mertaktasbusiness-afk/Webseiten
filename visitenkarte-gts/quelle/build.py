"""Compose front and back of the GTS business card as SVG (all text as outlines),
render print PDFs (85 x 55 mm + 3 mm bleed) and previews."""
import base64, io, json, math
import numpy as np, cv2, qrcode, cairosvg
from PIL import Image
from gts import *

S = 20                                   # raster px/mm
BLEED = 3.0
W, H = 85.0, 55.0
URL = 'https://www.gts-boeblingen.de'

F = load_fonts()
geom = json.load(open('front_geom.json'))


def data_uri(img, fmt='PNG', **kw):
    b = io.BytesIO()
    img.save(b, fmt, **kw)
    return f'data:image/{fmt.lower()};base64,' + base64.b64encode(b.getvalue()).decode()


def svg_doc(body, defs=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W + 2 * BLEED}mm" height="{H + 2 * BLEED}mm" '
            f'viewBox="{-BLEED} {-BLEED} {W + 2 * BLEED} {H + 2 * BLEED}">'
            f'<defs>{defs}</defs>{body}</svg>')


def circle(cx, cy, r, **attrs):
    a = ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" {a}/>'


GOLD_STOPS_CREAM = [(0, '#B8935C'), (0.45, '#8C6A3B'), (0.75, '#B99661'), (1, '#9B7845')]
GOLD_STOPS_DARK = [(0, '#D8BC8A'), (0.45, '#A9844E'), (0.75, '#CDAE78'), (1, '#B08D58')]

# =====================================================================================
# FRONT
# =====================================================================================
BX, BY = geom['badge']
BR = 9.5
LK = geom['line_src'][0]
LINE_BOT = geom['line_bottom_x']                       # x where the gold line meets y = 55


def line_x(y):
    return LINE_BOT + LK * (y - H)


def front_background():
    bg = np.array(Image.open('front_bg.png').convert('RGB')).astype(np.float32)
    ch, cw = bg.shape[:2]
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    X, Y = (xx + 0.5) / S - BLEED, (yy + 0.5) / S - BLEED
    # soft drop shadow under the badge
    d = np.sqrt((X - BX - 0.25) ** 2 + (Y - BY - 0.45) ** 2)
    sh = np.clip(1 - (d - BR + 0.6) / 1.4, 0, 1) ** 2 * 0.45
    bg = bg * (1 - sh[..., None])
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))


def badge_svg():
    sans = F['sans_medium']
    out = []
    out.append(circle(BX, BY, BR, fill='url(#badgeFill)'))
    out.append(circle(BX, BY, BR - 0.2, fill='none', stroke='#D9C7A0', stroke_width='0.26'))
    cap = 1.22
    size = sans.size_for_cap(cap)
    r_base = 7.35
    # top text: 'QUALITÄT · ZUVERLÄSSIGKEIT' across ~198 degrees
    top = 'QUALITÄT · ZUVERLÄSSIGKEIT'
    span = math.radians(198) * r_base
    w0 = sum(g[1] for g in sans.shape(top)) * size / sans.upm
    tr = (span - w0) / (len(sans.shape(top)) - 1)
    if tr < 0.04:
        size *= (span - 0.04 * (len(top) - 1)) / w0
        tr = 0.04
    d, _ = arc_text(sans, top, size, BX, BY, r_base, -90, tracking=tr)
    out.append(f'<path d="{d}" fill="{WHITE}"/>')
    bottom = 'NACHHALTIGKEIT'
    span_b = math.radians(104) * (r_base + cap)
    wb = sum(g[1] for g in sans.shape(bottom)) * size / sans.upm
    trb = (span_b - wb) / (len(bottom) - 1)
    d, _ = arc_text(sans, bottom, size, BX, BY, r_base + cap, 90, tracking=trb, bottom=True)
    out.append(f'<path d="{d}" fill="{WHITE}"/>')
    rm = r_base + cap / 2
    for a in (180 - 23.5, 23.5):
        out.append(circle(BX + rm * math.cos(math.radians(a)), BY + rm * math.sin(math.radians(a)), 0.24,
                          fill=GOLD_LT))
    # shield
    sx, sy = BX, BY + 0.05
    w2, top_c, top_s, bot = 4.15, -4.95, -3.85, 5.05

    def shield(scale, oy=0.0):
        p = lambda x, y: f'{sx + x * scale:.4f},{sy + oy + y * scale:.4f}'
        return (f'M{p(0, top_c)} C{p(1.4, top_c + 0.95)} {p(2.9, top_s - 0.05)} {p(w2, top_s)} '
                f'L{p(w2, -0.2)} C{p(w2, 2.6)} {p(2.3, 4.0)} {p(0, bot)} '
                f'C{p(-2.3, 4.0)} {p(-w2, 2.6)} {p(-w2, -0.2)} L{p(-w2, top_s)} '
                f'C{p(-2.9, top_s - 0.05)} {p(-1.4, top_c + 0.95)} {p(0, top_c)} Z')
    out.append(f'<path d="{shield(1)}" fill="url(#shieldGold)"/>')
    out.append(f'<path d="{shield(0.70, 0.15)}" fill="none" stroke="{WHITE}" stroke-width="0.40" '
               f'stroke-linejoin="round"/>')
    out.append(f'<path d="M{sx - 1.55:.3f},{sy + 0.30:.3f} L{sx - 0.35:.3f},{sy + 1.50:.3f} '
               f'L{sx + 1.75:.3f},{sy - 0.95:.3f}" fill="none" stroke="{WHITE}" stroke-width="0.62" '
               f'stroke-linecap="round" stroke-linejoin="round"/>')
    return '\n'.join(out)


def front_svg(bg_uri):
    defs = [gold_gradient('goldCream', 7, 8, 16, 18, GOLD_STOPS_CREAM),
            gold_gradient('shieldGold', BX - 4, BY - 5, BX + 4, BY + 5,
                          [(0, '#CDAA6E'), (0.5, '#A8844D'), (1, '#86653A')]),
            f'<radialGradient id="badgeFill" gradientUnits="userSpaceOnUse" cx="{BX - 2}" cy="{BY - 3}" '
            f'r="{BR * 1.35}"><stop offset="0" stop-color="#1A3D2D"/><stop offset="1" stop-color="#0C2218"/>'
            f'</radialGradient>']
    body = [f'<image x="{-BLEED}" y="{-BLEED}" width="{W + 2 * BLEED}" height="{H + 2 * BLEED}" '
            f'preserveAspectRatio="none" xlink:href="{bg_uri}"/>']
    # gold diagonal (continues into the bleed on both ends)
    body.append(f'<path d="M{line_x(H + 3.5):.4f},{H + 3.5} L{line_x(-3.5):.4f},-3.5" stroke="#BF9E68" '
                f'stroke-width="0.42" fill="none"/>')
    body.append(badge_svg())
    # logo (mockup coordinates shifted down by 3 mm)
    body.append(logo_svg(F, 'translate(0,3.0)', DKGREEN, DKGREEN, DKGREEN, 'goldCream'))
    # name
    name = F['serif_name']
    size = name.size_for_cap(4.2)
    w, _ = ink_width(name, 'Tuncay Eroglu', size)
    size *= (45.4 - 7.5) / w
    d, bb = text_ink(name, 'Tuncay Eroglu', size, 7.5, 30.2)
    body.append(f'<path d="{d}" fill="{DKGREEN}"/>')
    print('name cap height %.2f mm, ink %.2f..%.2f' % (size * name.cap / name.upm, bb[0], bb[2]))
    # INHABER
    sans = F['sans_medium']
    s2 = sans.size_for_cap(1.45)
    tr = fit_tracking(sans, 'INHABER', s2, 21.2 - 7.8)
    d, _ = text_ink(sans, 'INHABER', s2, 7.8, 34.3, tr)
    body.append(f'<path d="{d}" fill="{GOLD}"/>')
    body.append(f'<path d="M7.7,37.9 L17.7,37.9" stroke="{GOLD}" stroke-width="0.2"/>')
    # script lines
    sc = F['script']
    ssize = sc.size_for_cap(2.35)
    w2, _ = ink_width(sc, 'für Sauberkeit. Technik. Zuverlässigkeit.', ssize, 0.05)
    ssize *= 36.0 / w2
    for txt, y in (('GTS – Ihr Partner', 42.7), ('für Sauberkeit. Technik. Zuverlässigkeit.', 46.45)):
        d, bb = text_ink(sc, txt, ssize, 7.55, y, 0.05)
        body.append(f'<path d="{d}" fill="{GOLD}" stroke="{GOLD}" stroke-width="0.13" stroke-linejoin="round"/>')
        print('script line ends at %.2f (gold line at %.2f)' % (bb[2], line_x(y)))
    return svg_doc('\n'.join(body), ''.join(defs))


# =====================================================================================
# BACK
# =====================================================================================
WM_S, WM_C = 2.6, (70.1, 27.5)                          # watermark scale / arc centre


def wm_transform():
    return (f'translate({WM_C[0] - ARC_C[0] * WM_S:.4f},{WM_C[1] - ARC_C[1] * WM_S:.4f}) '
            f'scale({WM_S})')


def back_background():
    ch, cw = int((H + 2 * BLEED) * S), int((W + 2 * BLEED) * S)
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    X, Y = (xx + 0.5) / S - BLEED, (yy + 0.5) / S - BLEED
    c0 = np.array([0x19, 0x3B, 0x2B], np.float32)
    c1 = np.array([0x0C, 0x21, 0x17], np.float32)
    r = np.clip(np.sqrt(((X - 30) / 70) ** 2 + ((Y - 22) / 48) ** 2), 0, 1) ** 1.3
    bg = c0 * (1 - r[..., None]) + c1 * r[..., None]
    # watermark: big logo, filled with a faint photo texture
    wm = svg_doc(f'<g fill="#fff">' + logo_svg(F, wm_transform(), '#fff', '#fff', '#fff', 'wmW',
                                                   tagline=False) + '</g>',
                 gold_gradient('wmW', 0, 0, 1, 1, [(0, '#fff'), (1, '#fff')]))
    png = cairosvg.svg2png(bytestring=wm.encode(), output_width=cw, output_height=ch)
    mask = np.array(Image.open(io.BytesIO(png)).convert('RGBA'))[..., 3].astype(np.float32) / 255
    photo = np.array(Image.open('front_bg.png').convert('L')).astype(np.float32)
    photo = cv2.resize(photo[:, 900:], (cw, ch), interpolation=cv2.INTER_LINEAR)
    tex = (photo - photo.mean()) / (photo.std() + 1e-6)
    tint = np.array([0x3C, 0x5E, 0x4A], np.float32)
    lay = tint[None, None, :] + (tex * 16)[..., None]
    a = (mask * 0.34)[..., None]
    bg = bg * (1 - a) + lay * a
    rng = np.random.default_rng(3)
    bg = bg + rng.normal(0, 1.3, (ch, cw, 1)).astype(np.float32)
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))


ICON = GOLD_LT


def icon_phone(cx, cy, s=2.75):
    k = s / 24
    return (f'<path transform="translate({cx - 12 * k:.4f},{cy - 12 * k:.4f}) scale({k:.5f})" fill="{ICON}" '
            'd="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 '
            '3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 '
            '1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/>')


def icon_mail(cx, cy):
    w, h = 3.0, 2.1
    x0, y0 = cx - w / 2, cy - h / 2
    return (f'<rect x="{x0:.4f}" y="{y0:.4f}" width="{w}" height="{h}" rx="0.22" fill="{ICON}"/>'
            f'<path d="M{x0 + 0.25:.4f},{y0 + 0.28:.4f} L{cx:.4f},{cy + 0.25:.4f} L{x0 + w - 0.25:.4f},{y0 + 0.28:.4f}" '
            f'fill="none" stroke="#10281C" stroke-width="0.2" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<path d="M{x0 + 0.25:.4f},{y0 + h - 0.25:.4f} L{cx - 0.55:.4f},{cy - 0.05:.4f} M{x0 + w - 0.25:.4f},'
            f'{y0 + h - 0.25:.4f} L{cx + 0.55:.4f},{cy - 0.05:.4f}" fill="none" stroke="#10281C" '
            f'stroke-width="0.14" stroke-linecap="round"/>')


def icon_globe(cx, cy, r=1.32):
    sw = 0.19
    o = [circle(cx, cy, r, fill='none', stroke=ICON, stroke_width=sw)]
    o.append(f'<ellipse cx="{cx:.4f}" cy="{cy:.4f}" rx="{r * 0.45:.4f}" ry="{r:.4f}" fill="none" '
             f'stroke="{ICON}" stroke-width="{sw * 0.9}"/>')
    o.append(f'<path d="M{cx:.4f},{cy - r:.4f} L{cx:.4f},{cy + r:.4f} M{cx - r:.4f},{cy:.4f} L{cx + r:.4f},{cy:.4f}" '
             f'stroke="{ICON}" stroke-width="{sw * 0.9}"/>')
    for dy in (-0.52, 0.52):
        hw = math.sqrt(r * r - (dy * r) ** 2) * 0.97
        o.append(f'<path d="M{cx - hw:.4f},{cy + dy * r:.4f} Q{cx:.4f},{cy + dy * r * 1.12:.4f} '
                 f'{cx + hw:.4f},{cy + dy * r:.4f}" fill="none" stroke="{ICON}" stroke-width="{sw * 0.9}"/>')
    return ''.join(o)


def icon_pin(cx, cy, s=3.0):
    k = s / 22
    return (f'<path transform="translate({cx - 12 * k:.4f},{cy - 12.3 * k:.4f}) scale({k:.5f})" fill="{ICON}" '
            'fill-rule="evenodd" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 '
            '9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>')


QR_BOX = (61.0, 17.3, 15.6)                             # x, y, size (mm)


def qr_svg():
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, border=0, box_size=1)
    q.add_data(URL)
    q.make(fit=True)
    m = np.array(q.get_matrix(), bool)
    n = m.shape[0]
    bx, by, bs = QR_BOX
    size = 13.3
    mod = size / n
    x0, y0 = bx + (bs - size) / 2, by + (bs - size) / 2
    d = []
    for r in range(n):
        c = 0
        while c < n:
            if m[r, c]:
                c2 = c
                while c2 < n and m[r, c2]:
                    c2 += 1
                d.append(f'M{x0 + c * mod:.4f},{y0 + r * mod:.4f}h{(c2 - c) * mod:.4f}v{mod:.4f}h{-(c2 - c) * mod:.4f}z')
                c = c2
            else:
                c += 1
    print(f'QR version {q.version}, {n} modules, module {mod:.3f} mm, quiet zone {(bs - size) / 2 / mod:.1f} modules')
    return (f'<rect x="{bx}" y="{by}" width="{bs}" height="{bs}" rx="0.75" fill="#FBFAF6" '
            f'stroke="#BD9A63" stroke-width="0.32"/>'
            f'<path d="{"".join(d)}" fill="#000000"/>')


def back_svg(bg_uri):
    defs = [gold_gradient('goldDark', 6, 5, 20, 20, GOLD_STOPS_DARK)]
    body = [f'<image x="{-BLEED}" y="{-BLEED}" width="{W + 2 * BLEED}" height="{H + 2 * BLEED}" '
            f'preserveAspectRatio="none" xlink:href="{bg_uri}"/>']
    # logo: 0.8 x, arc starts at x = 7.0, ring top at y = 4.8
    sc = 0.8
    tx, ty = 7.0 - 7.25 * sc, 4.8 - 3.28 * sc
    body.append(logo_svg(F, f'translate({tx:.4f},{ty:.4f}) scale({sc})', WHITE, WHITE, WHITE, 'goldDark'))
    body.append(f'<path d="M7.6,20.4 L18.6,20.4" stroke="{GOLD_LT}" stroke-width="0.17"/>')
    # contact rows
    sans = F['sans']
    cap = 1.68
    size = sans.size_for_cap(cap)
    rows = [('0170 1601830', icon_phone), ('info@gts-boeblingen.de', icon_mail),
            ('www.gts-boeblingen.de', icon_globe), ('Böblingen und Umgebung', icon_pin)]
    for i, (txt, ic) in enumerate(rows):
        y = 26.4 + i * 4.65
        d, bb = text_ink(sans, txt, size, 14.2, y, 0.02)
        body.append(f'<path d="{d}" fill="{WHITE}"/>')
        body.append(ic(9.45, y - cap / 2))
    # QR code + call to action
    body.append(qr_svg())
    bx, by, bs = QR_BOX
    scr = F['script']
    ssize = scr.size_for_cap(2.45)
    cx = bx + bs / 2
    d1, bb1, _ = text_run(scr, 'Jetzt Kontakt', ssize, cx, by + bs + 4.6, 0.05, anchor='middle')
    d2, bb2, _ = text_run(scr, 'aufnehmen', ssize, cx + 0.4, by + bs + 8.3, 0.05, anchor='middle')
    for d in (d1, d2):
        body.append(f'<path d="{d}" fill="{GOLD_LT}" stroke="{GOLD_LT}" stroke-width="0.13" stroke-linejoin="round"/>')
    # curved arrow from the text up towards the QR code
    ax0, ay0 = bb1[2] + 0.9, bb1[1] + 0.3
    ax1, ay1 = bx + bs + 1.9, by + bs * 0.62
    c1 = (ax0 + 1.9, ay0 - 1.6)
    c2 = (ax1 + 1.9, ay1 + 1.7)
    body.append(f'<path d="M{ax0:.3f},{ay0:.3f} C{c1[0]:.3f},{c1[1]:.3f} {c2[0]:.3f},{c2[1]:.3f} {ax1:.3f},{ay1:.3f}" '
                f'fill="none" stroke="{GOLD_LT}" stroke-width="0.2" stroke-linecap="round"/>')
    tx_, ty_ = ax1 - c2[0], ay1 - c2[1]
    ln = math.hypot(tx_, ty_)
    tx_, ty_ = tx_ / ln, ty_ / ln
    hl = 1.0
    for sgn in (1, -1):
        a = math.radians(32) * sgn
        hx = -(tx_ * math.cos(a) - ty_ * math.sin(a)) * hl
        hy = -(tx_ * math.sin(a) + ty_ * math.cos(a)) * hl
        body.append(f'<path d="M{ax1:.3f},{ay1:.3f} l{hx:.3f},{hy:.3f}" stroke="{GOLD_LT}" stroke-width="0.2" '
                    f'stroke-linecap="round"/>')
    print('arrow right edge %.2f' % max(ax0, c1[0], c2[0], ax1))
    # bottom claim with rules
    sm = F['sans_medium']
    ts = sm.size_for_cap(1.1)
    claim = 'SAUBERKEIT · TECHNIK · ZUVERLÄSSIGKEIT'
    left, right = 7.6, bx + bs
    tw = 43.0
    tr = fit_tracking(sm, claim, ts, tw)
    xs = (left + right) / 2 - tw / 2
    yb = 49.3
    d, bb = text_ink(sm, claim, ts, xs, yb, tr)
    body.append(f'<path d="{d}" fill="{GOLD_LT}"/>')
    ym = yb - 1.1 / 2
    body.append(f'<path d="M{left},{ym:.3f} L{bb[0] - 2.4:.3f},{ym:.3f} M{bb[2] + 2.4:.3f},{ym:.3f} L{right},{ym:.3f}" '
                f'stroke="{GOLD_LT}" stroke-width="0.17"/>')
    return svg_doc('\n'.join(body), ''.join(defs))


if __name__ == '__main__':
    fbg = front_background()
    fbg.save('front_bg_final.png')
    bbg = back_background()
    bbg.save('back_bg_final.png')
    front = front_svg(data_uri(fbg))
    back = back_svg(data_uri(bbg))
    open('front.svg', 'w').write(front)
    open('back.svg', 'w').write(back)
    for name, svg in (('front', front), ('back', back)):
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=f'{name}_rgb.pdf')
        cairosvg.svg2png(bytestring=svg.encode(), write_to=f'{name}_preview.png',
                         output_width=int((W + 2 * BLEED) * 14), output_height=int((H + 2 * BLEED) * 14))
    print('done')
