#!/bin/bash
set -e
VER=${1:-v1.5}
rm -rf dist && mkdir -p dist/pacman
cp pac-man.py config.json CONTROLS.txt dist/pacman/
cp -r pacman assets vendor dist/pacman/
find dist/pacman -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
grep -E "pygame-ce|mazegenerator" requirements.txt > dist/pacman/requirements.txt
printf '#!/bin/bash\ncd "$(dirname "$0")"\npython3 --version\npython3 pac-man.py config.json\n' > dist/pacman/run.sh
chmod +x dist/pacman/run.sh
cd dist && zip -qr pacman-$VER.zip pacman && cd ..
echo "OK: dist/pacman-$VER.zip"