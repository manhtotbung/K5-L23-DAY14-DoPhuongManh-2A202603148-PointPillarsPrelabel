"""Nuclio serverless handler wrapping vf_pp PointPillars for CVAT 3D cuboid auto-annotation."""
from __future__ import annotations

import base64
import json
import math
import struct
import warnings

import numpy as np

warnings.filterwarnings("ignore", message="torch.meshgrid")

from vf_pp.core import VF_NAMES, Config, Detector  # noqa: E402


def _invert_intensity_gray(gray: np.ndarray) -> np.ndarray:
    """Invert scripts/vf_common.py:intensity_gray (log-compressed 40..255 -> 0..50)."""
    g = gray.astype(np.float32)
    t = np.clip((g - 40.0) / 215.0, 0.0, 1.0)
    inten = np.where(g <= 40.0, 0.0, np.expm1(t * math.log1p(50.0)))
    return inten.astype(np.float32)


def parse_pcd(raw: bytes) -> np.ndarray:
    """Parse binary or ASCII PCD sent by CVAT into float32 (N, 4) [x, y, z, intensity]."""
    marker_bin = b"\nDATA binary\n"
    marker_asc = b"\nDATA ascii\n"
    idx_bin = raw.find(marker_bin)
    idx_asc = raw.find(marker_asc)

    if idx_bin != -1:
        header_text = raw[:idx_bin].decode("ascii", errors="ignore")
        payload = raw[idx_bin + len(marker_bin):]
        mode = "binary"
    elif idx_asc != -1:
        header_text = raw[:idx_asc].decode("ascii", errors="ignore")
        payload = raw[idx_asc + len(marker_asc):]
        mode = "ascii"
    else:
        raise ValueError("Unsupported PCD format (missing DATA binary/ascii header)")

    fields, sizes, types = [], [], []
    n_points = 0
    for line in header_text.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        key = parts[0].upper()
        if key == "FIELDS":
            fields = [p.lower() for p in parts[1:]]
        elif key == "SIZE":
            sizes = [int(p) for p in parts[1:]]
        elif key == "TYPE":
            types = [p.upper() for p in parts[1:]]
        elif key == "POINTS":
            n_points = int(parts[1])

    if mode == "binary":
        if not sizes:
            sizes = [4] * len(fields)
        if not types:
            types = ["F"] * len(fields)
        dtype_map = {("F", 4): "<f4", ("F", 8): "<f8", ("U", 4): "<u4", ("I", 4): "<i4", ("U", 1): "u1"}
        dt = np.dtype([(f, dtype_map.get((t, s), "<f4")) for f, t, s in zip(fields, types, sizes)])
        count = min(n_points, len(payload) // dt.itemsize) if n_points else (len(payload) // dt.itemsize)
        arr = np.frombuffer(payload[:count * dt.itemsize], dtype=dt)
        x = arr["x"].astype(np.float32)
        y = arr["y"].astype(np.float32)
        z = arr["z"].astype(np.float32)
        if "intensity" in fields:
            inten = arr["intensity"].astype(np.float32)
        elif "rgb" in fields:
            rgb_u32 = arr["rgb"].view(np.uint32) if arr["rgb"].dtype == np.float32 else arr["rgb"].astype(np.uint32)
            inten = _invert_intensity_gray(rgb_u32 & np.uint32(0xFF))
        else:
            inten = np.zeros_like(x)
        return np.stack([x, y, z, inten], axis=1)

    # ASCII fallback
    rows = []
    ix, iy, iz = fields.index("x"), fields.index("y"), fields.index("z")
    ii = fields.index("intensity") if "intensity" in fields else None
    irgb = fields.index("rgb") if "rgb" in fields else None
    for line in payload.decode("ascii", errors="ignore").splitlines():
        parts = line.split()
        if len(parts) < len(fields):
            continue
        xv, yv, zv = float(parts[ix]), float(parts[iy]), float(parts[iz])
        if ii is not None:
            iv = float(parts[ii])
        elif irgb is not None:
            g = int(float(parts[irgb])) & 0xFF
            iv = 0.0 if g <= 40 else math.expm1(min(1.0, (g - 40.0) / 215.0) * math.log1p(50.0))
        else:
            iv = 0.0
        rows.append((xv, yv, zv, iv))
    return np.asarray(rows, dtype=np.float32).reshape(-1, 4)


def init_context(context):
    context.logger.info("Loading PointPillars model (vf_pp)...")
    context.user_data.detector = Detector(Config(score_thr=0.1))
    context.logger.info("PointPillars model ready.")


def handler(context, event):
    body = event.body
    if isinstance(body, (bytes, bytearray)):
        body = json.loads(body.decode("utf-8"))
    elif isinstance(body, str):
        body = json.loads(body)

    threshold = body.get("threshold")
    score_thr = float(threshold) if threshold is not None else 0.1
    det: Detector = context.user_data.detector
    if abs(det.cfg.score_thr - score_thr) > 1e-9:
        det.set_config(Config(score_thr=score_thr))

    raw_pcd = base64.b64decode(body["image"])
    points = parse_pcd(raw_pcd)
    boxes = det.detect(points)

    results = []
    for b in boxes:
        label = VF_NAMES.get(b["label"], str(b["label"]))
        pts16 = [
            round(float(b["x"]), 4),
            round(float(b["y"]), 4),
            round(float(b["z"]), 4),
            0.0,
            0.0,
            round(float(b["yaw"]), 4),
            round(float(b["length"]), 4),
            round(float(b["width"]), 4),
            round(float(b["height"]), 4),
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        ]
        results.append({
            "type": "cuboid",
            "label": label,
            "confidence": f"{float(b['score']):.4f}",
            "points": pts16,
        })

    return context.Response(
        body=json.dumps(results),
        headers={},
        content_type="application/json",
        status_code=200,
    )
