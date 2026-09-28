"""RGB PDFs from build.py -> print-ready CMYK PDFs with TrimBox/BleedBox, plus previews."""
import os, subprocess, sys
import numpy as np, cv2, pymupdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
PREVIEW = sys.argv[2] if len(sys.argv) > 2 else OUT
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREVIEW, exist_ok=True)
MM = 72 / 25.4
BLEED, W, H = 3.0, 85.0, 55.0
URL = 'https://www.gts-boeblingen.de'

GS = ['gs', '-q', '-dNOPAUSE', '-dBATCH', '-dSAFER', '-sDEVICE=pdfwrite']
GS_OPTS = ['-dCompatibilityLevel=1.6', '-dPDFSETTINGS=/prepress',
           '-sColorConversionStrategy=CMYK', '-sProcessColorModel=DeviceCMYK', '-dAutoRotatePages=/None',
           '-dDownsampleColorImages=true', '-dColorImageDownsampleType=/Bicubic', '-dColorImageResolution=400',
           '-dColorImageDownsampleThreshold=1.1', '-dAutoFilterColorImages=false', '-dColorImageFilter=/DCTEncode',
           '-c', '<< /ColorACSImageDict << /QFactor 0.08 /Blend 1 /HSamples [1 1 1 1] /VSamples [1 1 1 1] >> '
                 '/ColorImageDict << /QFactor 0.08 /Blend 1 /HSamples [1 1 1 1] /VSamples [1 1 1 1] >> >> '
                 'setdistillerparams', '-f']

SIDES = [('front', 'Vorderseite'), ('back', 'Rueckseite')]
media = RectangleObject([0, 0, (W + 2 * BLEED) * MM, (H + 2 * BLEED) * MM])
trim = RectangleObject([BLEED * MM, BLEED * MM, (W + BLEED) * MM, (H + BLEED) * MM])

both = PdfWriter()
for key, label in SIDES:
    raw = f'{key}_cmyk_raw.pdf'
    subprocess.run(GS + ['-o', raw] + GS_OPTS + [f'{key}_rgb.pdf'], check=True)
    r = PdfReader(raw)
    w = PdfWriter()
    for writer in (w, both):
        writer.add_page(r.pages[0])
        pg = writer.pages[-1]
        pg.mediabox = media
        pg.cropbox = media
        pg.bleedbox = media
        pg.trimbox = trim
    w.add_metadata({'/Title': f'GTS Visitenkarte – {label} (85 x 55 mm + 3 mm Beschnitt, CMYK)',
                    '/Author': 'GTS Gebäude Technik Service', '/Subject': 'Druckdaten Visitenkarte'})
    w.write(os.path.join(OUT, f'GTS_Visitenkarte_{label}.pdf'))
both.add_metadata({'/Title': 'GTS Visitenkarte – Seite 1 Vorderseite, Seite 2 Rückseite (85 x 55 mm + 3 mm Beschnitt, CMYK)',
                   '/Author': 'GTS Gebäude Technik Service', '/Subject': 'Druckdaten Visitenkarte'})
both.write(os.path.join(OUT, 'GTS_Visitenkarte_Vorder-und-Rueckseite.pdf'))

# ---- checks + previews from the final files ----
for key, label in SIDES:
    doc = pymupdf.open(os.path.join(OUT, f'GTS_Visitenkarte_{label}.pdf'))
    p = doc[0]
    assert not p.get_fonts(), 'fonts should be outlined'
    tb = p.trimbox
    print(label, 'MediaBox mm', round(p.mediabox.width / MM, 2), 'x', round(p.mediabox.height / MM, 2),
          '| TrimBox mm', round(tb.width / MM, 2), 'x', round(tb.height / MM, 2))
    cm = p.get_pixmap(dpi=300, colorspace=pymupdf.csCMYK)
    a = np.frombuffer(cm.samples, np.uint8).reshape(cm.h, cm.w, cm.n)[..., :4].astype(float) / 2.55
    print('   max total ink %.0f %%' % a.sum(2).max())
    pix = p.get_pixmap(dpi=300, clip=tb)
    pix.save(os.path.join(PREVIEW, f'Vorschau_{label}.png'))
    if key == 'back':
        img = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)[..., :3]
        val, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        print('   QR code ->', repr(val))
        assert val == URL
print('ok')
