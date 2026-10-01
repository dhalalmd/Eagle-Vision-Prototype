import cv2
import numpy as np

# Default settings — exact keys and defaults from AGENTS.md section 8
DEFAULT_SETTINGS = {
    "brightness": 0,
    "contrast": 1.0,
    "saturation": 1.0,
    "zoom": 1.0,
    "rotate": 0,
    "flip_h": False,
    "flip_v": False,
    "grayscale": False,
    "invert_colors": False,
}

# Clamp ranges
_CLAMP = {
    "brightness":    (int,   -100, 100),
    "contrast":      (float, 0.5,  2.0),
    "saturation":    (float, 0.0,  2.0),
    "zoom":          (float, 1.0,  3.0),
    "rotate":        (int,   None, None),   # discrete set
    "flip_h":        (bool,  None, None),
    "flip_v":        (bool,  None, None),
    "grayscale":     (bool,  None, None),
    "invert_colors": (bool,  None, None),
}

_VALID_ROTATIONS = {0, 90, 180, 270}


def clamp_settings(raw: dict) -> dict:
    """Validate and clamp incoming partial settings to allowed ranges."""
    out = {}
    for key, val in raw.items():
        if key not in _CLAMP:
            continue
        typ, lo, hi = _CLAMP[key]
        if typ is bool:
            out[key] = bool(val)
        elif typ is int and key == "rotate":
            v = int(val)
            out[key] = v if v in _VALID_ROTATIONS else 0
        elif typ is int:
            out[key] = max(lo, min(hi, int(val)))
        elif typ is float:
            out[key] = max(lo, min(hi, float(val)))
    return out


def merge_settings(existing: dict, patch: dict) -> dict:
    """Merge clamped patch into existing settings."""
    merged = dict(DEFAULT_SETTINGS)
    merged.update(existing)
    merged.update(clamp_settings(patch))
    return merged


def apply_settings(frame: np.ndarray, settings: dict) -> np.ndarray:
    """Apply image adjustments to a BGR frame. Order: rotate → flip → zoom →
    brightness/contrast (LUT) → saturation → grayscale → invert.
    Skips steps at default values for zero cost."""
    if not settings:
        return frame

    # --- rotate ---
    rot = settings.get("rotate", 0)
    if rot == 90:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rot == 180:
        frame = cv2.rotate(frame, cv2.ROTATE_180)
    elif rot == 270:
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # --- flip ---
    fh = settings.get("flip_h", False)
    fv = settings.get("flip_v", False)
    if fh and fv:
        frame = cv2.flip(frame, -1)
    elif fh:
        frame = cv2.flip(frame, 1)
    elif fv:
        frame = cv2.flip(frame, 0)

    # --- zoom (centre crop, scaled back) ---
    zoom = settings.get("zoom", 1.0)
    if zoom > 1.0:
        h, w = frame.shape[:2]
        crop_h, crop_w = int(h / zoom), int(w / zoom)
        y1 = (h - crop_h) // 2
        x1 = (w - crop_w) // 2
        frame = cv2.resize(frame[y1:y1+crop_h, x1:x1+crop_w], (w, h),
                           interpolation=cv2.INTER_LINEAR)

    # --- brightness / contrast (LUT for speed) ---
    brightness = settings.get("brightness", 0)
    contrast = settings.get("contrast", 1.0)
    if brightness != 0 or contrast != 1.0:
        lut = np.arange(256, dtype=np.float32)
        lut = lut * contrast + brightness
        lut = np.clip(lut, 0, 255).astype(np.uint8)
        frame = cv2.LUT(frame, lut)

    # --- saturation ---
    sat = settings.get("saturation", 1.0)
    if sat != 1.0:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat, 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # --- grayscale ---
    if settings.get("grayscale", False):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    # --- invert ---
    if settings.get("invert_colors", False):
        frame = cv2.bitwise_not(frame)

    return frame
