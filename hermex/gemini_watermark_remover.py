from importlib.resources import files
from pathlib import Path

import cv2
import numpy as np

_ASSETS_DIR = files("hermex") / "assets"

# The bg_48/bg_96 assets encode the watermark alpha map directly (opacity
# included). To re-derive after a watermark change, recover alpha from a
# flat-color sample via (obs - bg)/(255 - bg) using the local background.

_alpha_map_small: np.ndarray | None = None
_alpha_map_large: np.ndarray | None = None


def _calc_alpha(img: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    if img.shape[:2] != size:
        img = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
    return np.max(img, axis=2).astype(np.float32) / 255.0


def _load_assets() -> None:
    global _alpha_map_small, _alpha_map_large
    if _alpha_map_small is not None:
        return

    bg_small = cv2.imread(str(_ASSETS_DIR / "bg_48.png"))
    bg_large = cv2.imread(str(_ASSETS_DIR / "bg_96.png"))
    if bg_small is None or bg_large is None:
        raise ValueError(
            f"Could not load watermark reference assets from {_ASSETS_DIR}."
        )
    _alpha_map_small = _calc_alpha(bg_small, (48, 48))
    _alpha_map_large = _calc_alpha(bg_large, (96, 96))


def _get_config(width: int, height: int) -> dict:
    # `margin` is the gap in pixels between the watermark box and the
    # bottom-right corner.
    if width > 1024 and height > 1024:
        return {"margin": 192, "size": 96, "map": _alpha_map_large}
    else:
        return {"margin": 96, "size": 48, "map": _alpha_map_small}


def remove_gemini_watermark(input_path: str | Path, output_path: str | Path) -> None:
    """
    Remove the Gemini watermark from an image file.

    :param input_path: Path to the image to process.
    :param output_path: Path to write the result to. Pass the same value as
        ``input_path`` to overwrite the file in place.
    """
    _load_assets()

    img = cv2.imread(str(input_path))
    if img is None:
        raise ValueError(f"Could not read input image: {input_path}")

    h, w = img.shape[:2]
    config = _get_config(w, h)
    alpha_map = config["map"]
    size = config["size"]
    margin = config["margin"]

    x = w - margin - size
    y = h - margin - size

    if x < 0 or y < 0:
        raise ValueError(f"Image too small to process: {input_path}")

    roi = img[y : y + size, x : x + size].astype(np.float32)

    alpha = alpha_map[:, :, np.newaxis]
    alpha_clamped = np.minimum(alpha, 0.99)
    restored_roi = (roi - (alpha * 255.0)) / (1.0 - alpha_clamped)
    restored_roi = np.clip(restored_roi, 0, 255)

    mask_3ch = np.repeat(alpha > 0.002, 3, axis=2)
    final_roi = np.where(mask_3ch, restored_roi, roi)

    img[y : y + size, x : x + size] = final_roi.astype(np.uint8)
    cv2.imwrite(str(output_path), img)
