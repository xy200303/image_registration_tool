from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def read_image(path: str | Path, flags: int = cv2.IMREAD_COLOR):
    image_path = Path(path)

    try:
        data = np.fromfile(image_path, dtype=np.uint8)
    except OSError:
        return None

    if data.size == 0:
        return None

    return cv2.imdecode(data, flags)


def write_image(path: str | Path, image, params: list[int] | None = None) -> bool:
    image_path = Path(path)
    image_path.parent.mkdir(parents=True, exist_ok=True)

    suffix = image_path.suffix.lower() or ".png"
    success, encoded = cv2.imencode(suffix, image, params or [])
    if not success:
        return False

    try:
        encoded.tofile(image_path)
    except OSError:
        return False

    return True
