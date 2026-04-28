from pathlib import Path
import os
import shutil
import subprocess


def detect_audiveris() -> str:
    env_value = os.getenv("AUDIVERIS_BIN", "").strip()
    if env_value:
        return env_value

    candidates = [
        "/Applications/Audiveris.app/Contents/MacOS/Audiveris",
        "/opt/audiveris/bin/Audiveris",
        "/usr/local/bin/Audiveris",
        "/usr/bin/Audiveris",
        "Audiveris",
        "audiveris",
    ]
    for candidate in candidates:
        if Path(candidate).exists() or shutil.which(candidate):
            return candidate

    return candidates[0]


AUDIVERIS = detect_audiveris()

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
