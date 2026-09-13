"""Synthesise dispensing patterns so the pipeline is demoable before real
factory images exist. Each sample encodes one known defect, which doubles as
the test oracle for the measurement code.
"""

import cv2
import numpy as np

RNG = np.random.default_rng(7)
W, H, ROWS, COLS, PITCH, MARGIN, R = 720, 460, 3, 5, 130, 110, 26


def _canvas() -> np.ndarray:
    base = np.full((H, W, 3), 232, np.uint8)
    return cv2.add(base, RNG.normal(0, 3, (H, W, 3)).astype(np.int16).clip(-12, 12).astype(np.uint8))


def _dot(img, cx, cy, r, squash=1.0, colour=(70, 70, 75)):
    cv2.ellipse(img, (int(cx), int(cy)), (int(r * squash), int(r / squash)), 0, 0, 360, colour, -1)
    cv2.GaussianBlur(img, (3, 3), 0, dst=img)


def build(kind: str) -> np.ndarray:
    img = _canvas()
    for row in range(ROWS):
        for col in range(COLS):
            cx, cy = MARGIN + col * PITCH, MARGIN + row * PITCH
            r, squash = R, 1.0

            if kind == "good":
                r = R + RNG.normal(0, 0.6)
            elif kind == "inconsistent":
                r = R * RNG.choice([0.62, 0.8, 1.0, 1.18, 1.32])
            elif kind == "missing":
                r = R + RNG.normal(0, 0.6)
                if (row, col) in {(0, 2), (1, 4), (2, 1)}:
                    continue
            elif kind == "spreading":
                r = R + RNG.normal(0, 0.6)
                if col >= 3:
                    r, squash = R * 1.45, 1.5
            elif kind == "misaligned":
                r = R + RNG.normal(0, 0.6)
                # Progressive drift plus jitter: a real axis or fixture error.
                cx += col * 5.5 + RNG.normal(0, 4)
                cy += RNG.normal(0, 4)
            elif kind == "undersized":
                r = R * (0.55 if col % 2 == 0 else 0.98)

            _dot(img, cx, cy, r, squash)
    return img


if __name__ == "__main__":
    import pathlib

    out = pathlib.Path(__file__).parent / "samples"
    out.mkdir(exist_ok=True)
    for kind in ("good", "inconsistent", "missing", "spreading", "undersized", "misaligned"):
        path = out / f"{kind}.png"
        cv2.imwrite(str(path), build(kind))
        print(f"wrote {path}")
