from importlib.resources import files

import cv2
import numpy as np

_ASSETS_DIR = files("hermex") / "assets"

_alpha_map_small = None
_alpha_map_large = None


def gemini_remove_watermark(input_path: str, output_path: str):
    def calc_alpha(img, size):
        if img.shape[:2] != size:
            img = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
        return np.max(img, axis=2).astype(np.float32) / 255.0

    def load_assets():
        global _alpha_map_small, _alpha_map_large
        if _alpha_map_small is not None:
            return

        bg_small = cv2.imread(str(_ASSETS_DIR / "bg_48.png"))
        bg_large = cv2.imread(str(_ASSETS_DIR / "bg_96.png"))
        if bg_small is None or bg_large is None:
            raise ValueError(
                f"Could not load watermark reference assets from {_ASSETS_DIR}."
            )
        _alpha_map_small = calc_alpha(bg_small, (48, 48))
        _alpha_map_large = calc_alpha(bg_large, (96, 96))

    def get_config(width, height):
        if width > 1024 and height > 1024:
            return {"margin": 64, "size": 96, "map": _alpha_map_large}
        else:
            return {"margin": 32, "size": 48, "map": _alpha_map_small}

    load_assets()

    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Could not read input image: {input_path}")

    h, w = img.shape[:2]
    config = get_config(w, h)
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
    cv2.imwrite(output_path, img)
