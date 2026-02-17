import cv2
import numpy as np
from pathlib import Path

def is_music_page(path, min_staff_lines=20):
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False

    h, w = img.shape

    # binariser og inverter (noter blir hvitt = 255)
    blur = cv2.GaussianBlur(img, (5, 5), 0)
    _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # marker horisontale streker
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (w // 5, 1))
    lines = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel, iterations=1)

    # finn “lange” horisontale komponenter
    contours, _ = cv2.findContours(lines, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    long_lines = [
        c for c in contours
        if cv2.boundingRect(c)[2] > w * 0.3   # bredde > 30% av siden
    ]

    return len(long_lines) >= min_staff_lines

# eksempel på bruk:
for img in Path("pages").glob("*.png"):
    if is_music_page(img):
        print(img, "→ ser ut som noter")
    else:
        print(img, "→ trolig ikke noter")
