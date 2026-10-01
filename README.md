Download & install instructions

1. Download the .zip for Linux and unpack it.
2. You need Python 3.10+ installed (check: `python3 --version`).
3. Open a terminal in the unpacked `pacman/` folder:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

4. Launch:

```bash
./run.sh
```

(or: `.venv/bin/python pac-man.py config.json`)

5. No internet needed after install — the maze-generator wheel
   is bundled inside `vendor/`.
