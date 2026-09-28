#!/usr/bin/env bash
# Erzeugt die Druckdaten der GTS-Visitenkarte neu.
# Voraussetzungen: Python 3.10+, Ghostscript (gs), curl.
set -euo pipefail
cd "$(dirname "$0")"

pip install -q pillow numpy opencv-python-headless qrcode fonttools brotli uharfbuzz cairosvg pypdf pymupdf

# Schriften (SIL Open Font License) aus den @fontsource-Paketen der npm-Registry
if [ ! -d fonts ]; then
  mkdir -p fonts .npm
  for p in cormorant-garamond playfair-display montserrat oooh-baby; do
    url=$(curl -sS "https://registry.npmjs.org/@fontsource/$p/latest" | python3 -c "import json,sys; print(json.load(sys.stdin)['dist']['tarball'])")
    mkdir -p ".npm/$p" && curl -sSfL "$url" | tar -xz -C ".npm/$p"
  done
  python3 - <<'EOF'
import glob, os
from fontTools.ttLib import TTFont
for f in glob.glob('.npm/*/package/files/*-latin-*-normal.woff2'):
    if 'latin-ext' in f:
        continue
    t = TTFont(f); t.flavor = None
    t.save(os.path.join('fonts', os.path.basename(f).replace('.woff2', '.ttf')))
EOF
  rm -rf .npm
fi

python3 photo.py              # Foto-Hintergrund der Vorderseite (aus dem Mockup)
python3 build.py              # Layout beider Seiten als SVG/PDF (RGB, Texte in Kurven)
python3 finalize.py ../druckdaten ../vorschau   # CMYK, Beschnitt-Boxen, Vorschau, QR-Test
