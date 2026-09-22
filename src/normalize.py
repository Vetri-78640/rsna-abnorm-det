"""Intensity normalisation and image-based quality control for knee MRI.

MRI voxel values are in arbitrary units -- a mix of tissue properties and
hardware settings, with no physical meaning and no comparability across
scanners. How you standardise them therefore matters, and the public notebook
gets it wrong in one place.

PER-SLICE WINDOWING IS THE BUG. Cell 21 sets `INTENSITY = 'slice'` and stretches
each slice independently to its own 1st-99th percentile. Four of the twelve
targets -- Effusion, Synovitis, Contusion, Fracture -- are AMPLITUDE findings.
A per-slice stretch maps the brightest fluid on every slice to 1.0, so a trace
effusion and a tense 80 mL effusion become indistinguishable except by area. It
also injects slice-to-slice flicker, since consecutive slices get different
transfer functions purely from their content.

The file already contains an untaken `INTENSITY == 'series'` branch, so flipping
that one constant is a free experiment. Families A and the raptor arm already
normalise per series.

A second problem is subtler: the 99th percentile is set by different TISSUE in
different sequences -- fluid on a fat-suppressed series, marrow fat on a
non-suppressed one, and unsuppressed subcutaneous fat when fat saturation has
failed. Anchoring on a percentile is therefore the opposite of standardising.
`muscle_reference` is the knee analogue of WhiteStripe: skeletal muscle is large,
contiguous, rarely pathological, and already the accepted reference tissue for
signal-intensity ratios in musculoskeletal work.
"""

from __future__ import annotations

import numpy as np


def per_series_window(vol, lo_pct=1.0, hi_pct=99.0, eps=1e-6):
    """Percentile window computed once over the WHOLE series.

    Preserves relative brightness between slices, which is what effusion volume
    and marrow-oedema extent depend on.
    """
    vol = np.asarray(vol, dtype=np.float32)
    if vol.size == 0:
        return vol
    lo, hi = np.percentile(vol, [lo_pct, hi_pct])
    return np.clip((vol - lo) / max(float(hi - lo), eps), 0.0, 1.0)


def per_slice_window(vol, lo_pct=1.0, hi_pct=99.0, eps=1e-6):
    """The notebook's behaviour, kept only for A/B comparison. Do not ship."""
    vol = np.asarray(vol, dtype=np.float32)
    out = np.empty_like(vol)
    for i in range(vol.shape[0]):
        lo, hi = np.percentile(vol[i], [lo_pct, hi_pct])
        out[i] = np.clip((vol[i] - lo) / max(float(hi - lo), eps), 0.0, 1.0)
    return out


def foreground_mask(vol, pct=25.0):
    """Crude body mask: everything above a low percentile of the volume."""
    vol = np.asarray(vol, dtype=np.float32)
    if vol.size == 0:
        return np.zeros_like(vol, dtype=bool)
    return vol > np.percentile(vol, pct)


def muscle_mode(vol, lo_q=0.20, hi_q=0.65, bins=128):
    """Robust estimate of the skeletal-muscle intensity mode.

    Muscle occupies the mid-intensity band of a knee MRI on essentially every
    sequence, so the dominant histogram mode between the 20th and 65th
    percentiles of foreground voxels is a stable, tissue-anchored reference.
    Returns None when the volume is degenerate.
    """
    vol = np.asarray(vol, dtype=np.float32)
    fg = vol[foreground_mask(vol)]
    if fg.size < 64:
        return None
    lo, hi = np.quantile(fg, [lo_q, hi_q])
    if not np.isfinite([lo, hi]).all() or hi <= lo:
        return None
    band = fg[(fg >= lo) & (fg <= hi)]
    if band.size < 32:
        return None
    counts, edges = np.histogram(band, bins=bins)
    i = int(np.argmax(counts))
    return float((edges[i] + edges[i + 1]) / 2.0)


def muscle_reference(vol, target=0.35, clip=(0.0, 4.0)):
    """Scale so muscle sits at a fixed value. Knee analogue of WhiteStripe.

    Unlike a percentile stretch this is anchored to a TISSUE, so the same
    physical brightness maps to the same number across scanners and sequences,
    and absolute fluid brightness is preserved.
    """
    vol = np.asarray(vol, dtype=np.float32)
    m = muscle_mode(vol)
    if not m or m <= 0:
        return per_series_window(vol)
    return np.clip(vol / m * target, *clip)


def amplitude_features(vol):
    """Scalars that survive normalisation, capturing what a stretch deletes.

    `p99_over_muscle` is the one that matters for Effusion and Contusion: it is
    how bright the brightest fluid is relative to a stable reference tissue,
    which is exactly the quantity a per-slice window destroys.
    """
    vol = np.asarray(vol, dtype=np.float32)
    if vol.size == 0:
        return {k: 0.0 for k in
                ("p99_over_muscle", "p999_over_muscle", "bright_fraction",
                 "muscle_mode", "dynamic_range")}
    m = muscle_mode(vol) or 1.0
    p50, p99, p999 = np.percentile(vol, [50, 99, 99.9])
    return {
        "p99_over_muscle": float(p99 / m) if m > 0 else 0.0,
        "p999_over_muscle": float(p999 / m) if m > 0 else 0.0,
        "bright_fraction": float((vol > 2.0 * m).mean()) if m > 0 else 0.0,
        "muscle_mode": float(m),
        "dynamic_range": float(p99 / max(p50, 1e-6)),
    }


def fatsat_failure_ratio(slice_2d, ring_frac=0.12):
    """Detect failed or inhomogeneous fat suppression from the image itself.

    Frequency-selective fat saturation (CHESS/SPIR/SPAIR) degrades with B0
    inhomogeneity, and this is worst off-isocentre -- which is the knee's normal
    position in a large-bore magnet. On a genuinely fat-suppressed slice the
    subcutaneous fat ring should be dark, so a high subcutaneous-to-muscle ratio
    means the header's Fat_Suppression flag is lying about this series.

    Returns the ratio; values above roughly 1.2 indicate failure. STIR is immune
    because it nulls by T1 rather than frequency, so exclude IR series.
    """
    a = np.asarray(slice_2d, dtype=np.float32)
    if a.ndim != 2 or min(a.shape) < 16:
        return None
    h, w = a.shape
    # Threshold relative to the bright end rather than by a fixed percentile, so
    # the body mask survives whether the subcutaneous ring is dark (fat sat
    # working) or bright (fat sat failed) -- the latter is the case this function
    # exists to catch, and a percentile threshold masks out the core instead.
    body = a > 0.12 * float(np.percentile(a, 99))
    if body.sum() < 64:
        return None
    ys, xs = np.nonzero(body)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    ry = max(1, int((y1 - y0) * ring_frac))
    rx = max(1, int((x1 - x0) * ring_frac))

    ring = np.zeros_like(body)
    ring[y0:y0 + ry, x0:x1 + 1] = True
    ring[y1 - ry:y1 + 1, x0:x1 + 1] = True
    ring[y0:y1 + 1, x0:x0 + rx] = True
    ring[y0:y1 + 1, x1 - rx:x1 + 1] = True
    ring &= body

    core = np.zeros_like(body)
    core[y0 + 2 * ry:y1 - 2 * ry, x0 + 2 * rx:x1 - 2 * rx] = True
    core &= body

    if ring.sum() < 32 or core.sum() < 32:
        return None
    core_v = float(np.median(a[core]))
    if core_v <= 1e-6:
        return None
    return float(np.median(a[ring]) / core_v)


def bias_field_correct(vol, sigma_frac=0.25):
    """Cheap N4 stand-in: divide out a smooth low-pass estimate of the field.

    Knee coils have strong sensitivity gradients, so marrow near a coil element
    reads brighter than marrow at the centre. Proper N4 is far too slow for an
    inference kernel; a Gaussian-blur divide removes most of the low-frequency
    component at negligible cost. Falls back to identity without scipy.
    """
    vol = np.asarray(vol, dtype=np.float32)
    try:
        from scipy.ndimage import gaussian_filter
    except ImportError:
        return vol
    if vol.ndim != 3 or vol.size == 0:
        return vol
    sigma = max(1.0, sigma_frac * min(vol.shape[1], vol.shape[2]))
    field = gaussian_filter(vol, sigma=(0, sigma, sigma))
    field = np.where(field < 1e-3, 1.0, field)
    out = vol / field
    m = float(np.median(out[out > 0])) if (out > 0).any() else 1.0
    return (out / max(m, 1e-6)).astype(np.float32)
