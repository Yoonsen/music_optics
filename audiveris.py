from pathlib import Path
import subprocess

AUDIVERIS = "/Applications/Audiveris.app/Contents/MacOS/Audiveris"

IN_DIR = Path("pages")
OUT_DIR = Path("scores")
OUT_DIR.mkdir(exist_ok=True)

for img in sorted(IN_DIR.glob("*.png")):
    print(f"Processing {img.name}...")
    cmd = [
        AUDIVERIS,
        "-batch",
        "-export",
        "-output", str(OUT_DIR),
        str(img),
    ]
    subprocess.run(cmd, check=True)

print("Done.")
