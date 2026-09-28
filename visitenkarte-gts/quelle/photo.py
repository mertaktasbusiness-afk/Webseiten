"""Build the raster background (cream + photo panel) of the front side.

Output: front_bg.png at 20 px/mm covering 91 x 61 mm (85 x 55 mm + 3 mm bleed)
and front_geom.json with the geometry the vector layer has to match.
Coordinates in mm are trim-box coordinates (0,0 = top-left corner of the card).
"""
import json
import numpy as np, cv2
from PIL import Image

S = 20                      # px per mm
BLEED = 3.0
W_MM, H_MM = 85.0, 55.0
CW, CH = int((W_MM + 2 * BLEED) * S), int((H_MM + 2 * BLEED) * S)
CREAM = np.array([0xF1, 0xEC, 0xE3], np.float32)
u8 = lambda im: np.clip(im, 0, 255).astype(np.uint8)

# ---- source: mockup front card, rectified at true aspect (85 x 43.1 mm) ----
mock = np.array(Image.open('mockup.webp').convert('RGB'))
SRC_H = 43.1
sw, sh = int(85 * S), int(round(SRC_H * S))
M = cv2.getPerspectiveTransform(np.float32([(58, 183), (935, 15), (1051, 426), (136, 611)]),
                                np.float32([[0, 0], [sw, 0], [sw, sh], [0, sh]]))
src = cv2.warpPerspective(mock, M, (sw, sh), flags=cv2.INTER_LANCZOS4,
                          borderMode=cv2.BORDER_REPLICATE).astype(np.float32)

BX, BY, BR = 74.62, 15.68, 9.15          # badge circle in source (mm)
LK, LB = -0.7154, 86.119                 # gold line in source: x = LK*y + LB


def band_edges(y):
    """Crisp old gold line (~0.5 mm). The soft light ribbon next to it near the top is kept."""
    return 0.45 + 0 * y, 0.45 + 0 * y                     # left, right half widths


def in_hole(x, y):
    lx = LK * y + LB
    l, r = band_edges(y)
    band = (x > lx - l) & (x < lx + r)
    badge = (x - BX) ** 2 + (y - BY) ** 2 < (BR + 0.35) ** 2
    return band | badge


yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
xm, ym = (xx + 0.5) / S, (yy + 0.5) / S
line_x = LK * ym + LB
green_side = xm > line_x
hole = in_hole(xm, ym)

# tint model photo -> green overlay (per channel linear, matched statistics)
sel_p = (~green_side) & (xm > line_x - 3.5) & (xm < line_x - 0.8) & (ym > 27) & (ym < 42.5)
sel_g = green_side & (xm < line_x + 3.5) & (xm > line_x + 0.8) & (ym > 27) & (ym < 42.5)
a = src[sel_g].std(0) / src[sel_p].std(0)
b = src[sel_g].mean(0) - a * src[sel_p].mean(0)
tint = lambda im: np.clip(im * a + b, 0, 255)

photo = cv2.inpaint(u8(src), hole.astype(np.uint8) * 255, 7, cv2.INPAINT_TELEA).astype(np.float32)
green = np.where(green_side[..., None], src, tint(photo))
green = cv2.inpaint(u8(green), hole.astype(np.uint8) * 255, 7, cv2.INPAINT_TELEA).astype(np.float32)

# ---- placement: badge slides along the line so that the line runs into the top-right corner ----
NBX = 72.5
OX = NBX - BX
OY = (W_MM - LB - OX) / (-LK)               # solve LK*(0-OY) + LB + OX = 85
NBY = BY + OY
print('offset', round(OX, 3), round(OY, 3), 'badge', NBX, round(NBY, 3))

DX0, DX1, DY0, DY1 = 45.0, 84.6, 0.4, 42.7  # trusted source domain (source mm)
BUILDING_X = 69.0                           # right tower starts here (source x)
PERIOD, PSHIFT = 5.5, 1.0                   # facade repeat (measured by autocorrelation, mm)

cy, cx = np.mgrid[0:CH, 0:CW].astype(np.float32)
X = (cx + 0.5) / S - BLEED
Y = (cy + 0.5) / S - BLEED
sx, sy = X - OX, Y - OY

def reflect(v, lo, hi):
    v = np.where(v < lo, 2 * lo - v, v)
    return np.where(v > hi, 2 * hi - v, v)


gx, gy = reflect(sx, DX0, DX1), reflect(sy, DY0, DY1)      # green layer: plain mirror
# right of the domain: constant shift along the line direction (keeps distance to the line)
SHIFT_R = 8.0
right = sx > DX1
sx, sy = np.where(right, sx + LK * SHIFT_R, sx), np.where(right, sy + SHIFT_R, sy)
# left of the domain (hidden under the fade anyway): reflect
sx = np.where(sx < DX0, 2 * DX0 - sx, sx)
# bottom: reflect
sy = np.where(sy > DY1, 2 * DY1 - sy, sy)
# top: continue the tower facade by its repeat, clamp the sky
above = sy < DY0
k = np.ceil((DY0 - sy) / PERIOD)
sx_t = np.where(above, sx + k * PSHIFT, sx)
sy_t = np.where(above, sy + k * PERIOD, sy)
# close to the line: shift along the line instead, so the ribbon/line side stays intact
SHIFT_T = 5.5
sx_l = np.where(above, sx + LK * SHIFT_T, sx)
sy_l = np.where(above, sy + SHIFT_T, sy)
dist = (LK * sy + LB) - sx                                   # >0 on photo side
wl = np.clip((9.5 - dist) / 3.0, 0, 1)                       # 1 near the line (tower copy drifts ~5 mm towards it)
sx_t = sx_t * (1 - wl) + sx_l * wl
sy_t = sy_t * (1 - wl) + sy_l * wl
sy_s = np.where(above, DY0, sy)
wt = np.clip((sx - (BUILDING_X - 0.6)) / 1.2, 0, 1)[..., None]


def sample(layer, sxx, syy):
    return cv2.remap(layer, (sxx * S - 0.5).astype(np.float32), (syy * S - 0.5).astype(np.float32),
                     cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def valid_photo(sxx, syy):
    ok = (sxx >= DX0) & (sxx <= DX1 + 0.1) & (syy >= 0) & (syy <= DY1 + 0.1)
    return ok & (sxx < LK * syy + LB - band_edges(syy)[0]) & ~in_hole(sxx, syy)


P = sample(photo, sx_t, sy_t) * wt + sample(photo, sx, sy_s) * (1 - wt)
P_ok = np.where(wt[..., 0] > 0.5, valid_photo(sx_t, sy_t), valid_photo(sx, sy_s))
# sky columns above the source were clamped -> soften their vertical streaks
sky_ext = ((Y - OY < DY0) * (1 - wt[..., 0]))[..., None]
P = P * (1 - sky_ext) + cv2.GaussianBlur(P, (0, 0), sigmaX=10, sigmaY=1) * sky_ext
seam = (np.clip(1 - np.abs(sy - DY0) / 0.8, 0, 1) * (Y - OY < DY0 + 0.8))[..., None]
P = P * (1 - 0.6 * seam) + cv2.GaussianBlur(P, (0, 0), 2.0) * 0.6 * seam
G = sample(green, gx, gy)
G_ok = ~in_hole(gx, gy)

new_line_x = LK * (Y - OY) + LB + OX
gside = X > new_line_x

# fill whatever could not be sampled cleanly (only where the layer is actually used)
P_bad = (~P_ok) & (~gside) & (X > 40)
G_bad = (~G_ok) & gside
P = cv2.inpaint(u8(P), cv2.dilate(P_bad.astype(np.uint8) * 255, np.ones((3, 3), np.uint8)), 5,
                cv2.INPAINT_TELEA).astype(np.float32)
G = cv2.inpaint(u8(G), cv2.dilate(G_bad.astype(np.uint8) * 255, np.ones((3, 3), np.uint8)), 5,
                cv2.INPAINT_TELEA).astype(np.float32)
print('filled px  photo:', int(P_bad.sum()), ' green:', int(G_bad.sum()))

# green overlay: mostly flat deep green, the photo only shimmers through (as in the mockup)
GREEN_A = np.array([0x16, 0x36, 0x28], np.float32)          # near the line / top
GREEN_B = np.array([0x0D, 0x22, 0x18], np.float32)          # bottom-right corner
gdist = np.clip(((X - new_line_x) * 0.8 + (Y - 10) * 0.6) / 45.0, 0, 1)[..., None]
base = GREEN_A * (1 - gdist) + GREEN_B * gdist
Gl = cv2.GaussianBlur(G, (0, 0), 12)
G = base + 0.30 * (G - Gl) + 0.22 * (Gl - Gl.mean((0, 1)))

# synthesized strip above the source: keep only its soft tones (no structure / seams)
syn = np.clip((DY0 + 1.2 - (Y - OY)) / 1.2, 0, 1)[..., None]
P = P * (1 - syn) + cv2.GaussianBlur(P, (0, 0), 18) * syn

# light haze along the top edge (hides the synthesized strip, matches the sunny look)
HAZE = np.array([0xEE, 0xE6, 0xD9], np.float32)
hz = (np.clip((6.5 - Y) / 7.5, 0, 1) ** 1.6 * 0.90)[..., None]
P = P * (1 - hz) + HAZE * hz

panel = np.where(gside[..., None], G, P)

# clean-up: mild sharpening + grade (mockup lighting made the photo dim)
blur = cv2.GaussianBlur(panel, (0, 0), 1.6)
panel = np.clip(panel + 0.5 * (panel - blur), 0, 255)
panel = np.where(gside[..., None], panel,
                 np.clip(panel * np.array([1.06, 1.04, 1.01], np.float32), 0, 255))

# fade into cream on the left, softened towards the bottom-left
t = np.clip((X - (43.5 + 0.06 * np.clip(Y - 30, 0, None))) / 17.0, 0, 1)
alpha = t * t * (3 - 2 * t)
tb = np.clip((Y - 42.0) / 16.0, 0, 1)
alpha = alpha * (1 - 0.5 * tb * tb)
alpha = np.where(gside, 1.0, alpha)

vign = 1.0 - 0.025 * (((X - 20) / 60) ** 2 + ((Y - 27) / 40) ** 2)
bg = CREAM[None, None, :] * vign[..., None]
out = bg * (1 - alpha[..., None]) + panel * alpha[..., None]
rng = np.random.default_rng(7)
out = out + rng.normal(0, 2.0, (CH, CW, 1)).astype(np.float32) * alpha[..., None]
out = out + rng.normal(0, 0.8, (CH, CW, 1)).astype(np.float32) * (1 - alpha[..., None])  # dither cream

Image.fromarray(u8(out)).save('front_bg.png')
json.dump({'offset': [float(OX), float(OY)], 'line_src': [LK, LB],
           'badge': [NBX, float(NBY)], 'badge_src_r': BR,
           'line_bottom_x': float(LK * (H_MM - OY) + LB + OX)}, open('front_geom.json', 'w'), indent=1)
print(json.load(open('front_geom.json')))
