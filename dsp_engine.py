# -*- coding: utf-8 -*-
"""
PatternGuard Computer Vision & Signal Processing Engine
(Balanced High-Precision Defect Masking & Lattice Exemplar Inpainting)
"""
# dsp_engine.py
import cv2
import numpy as np
import scipy.fft as fft


# ==============================================================================
# ALGORITHM I: MACRO-LATTICE EXTRACTION & WALLPAPER GROUP CLASSIFICATION
# ==============================================================================

def _find_axis_peak(profile, center_idx, min_offset=15, fallback=48.0):
    """Find the strongest peak in a 1D autocorrelation profile (excluding a
    window around the trivial zero-offset center peak), with parabolic
    sub-pixel refinement.
    """
    work = profile.copy()
    lo = max(0, center_idx - min_offset)
    hi = min(len(work), center_idx + min_offset + 1)
    work[lo:hi] = -np.inf

    idx = int(np.argmax(work))
    if not np.isfinite(work[idx]) or work[idx] <= 0:
        return fallback

    if 1 <= idx < len(profile) - 1:
        f_m1, f_0, f_p1 = profile[idx - 1], profile[idx], profile[idx + 1]
        denom = f_m1 - 2.0 * f_0 + f_p1
        d = 0.5 * (f_m1 - f_p1) / denom if abs(denom) > 1e-9 else 0.0
        d = float(np.clip(d, -0.5, 0.5))
    else:
        d = 0.0

    offset = abs((idx + d) - center_idx)
    return offset if offset >= min_offset else fallback


def run_algorithm_i_autocorrelation(I_gray, macro_tile_floor=60.0):
    """
    ALGORITHM I: MACRO-LATTICE COHERENCE EXTRACTION (2D Wiener-Khinchin FFT).
    """
    I_f = I_gray.astype(np.float64)
    h, w = I_f.shape

    window = np.outer(np.hanning(h), np.hanning(w))
    I_windowed = I_f * window

    F = fft.fft2(I_windowed)
    S = F * np.conj(F)
    R_xx = np.abs(fft.fftshift(fft.ifft2(S)))

    cy, cx = h // 2, w // 2

    vertical_profile = R_xx[:, cx]
    horizontal_profile = R_xx[cy, :]

    a1_val = _find_axis_peak(vertical_profile, cy, min_offset=15, fallback=48.0)
    a2_val = _find_axis_peak(horizontal_profile, cx, min_offset=15, fallback=48.0)

    if a1_val < macro_tile_floor:
        mult = max(1, round(macro_tile_floor / a1_val))
        a1_val *= mult
    if a2_val < macro_tile_floor:
        mult = max(1, round(macro_tile_floor / a2_val))
        a2_val *= mult

    theta_dom = float(np.degrees(np.arctan2(a1_val, a2_val)))

    try:
        detected_group = classify_wallpaper_group(I_gray, a1_val, a2_val)
    except Exception as e:
        print(f"[Wallpaper classification warning] {e}")
        detected_group = "p1"

    return R_xx, float(a1_val), float(a2_val), theta_dom, detected_group


def _ncc(a, b):
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    a = a - a.mean()
    b = b - b.mean()
    denom = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if denom < 1e-6:
        return 0.0
    return float(np.sum(a * b) / denom)


def _seed_positions(h, w, L, n_seeds=6):
    cy, cx = h // 2, w // 2
    grid_offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1), (0, 0), (0, 0)]
    step_y = max(L, (h - L) // 3) if h > L else 0
    step_x = max(L, (w - L) // 3) if w > L else 0
    seeds = []
    for gy, gx in grid_offsets[:n_seeds]:
        y0 = int(np.clip(cy + gy * step_y - L // 2, 0, max(0, h - L)))
        x0 = int(np.clip(cx + gx * step_x - L // 2, 0, max(0, w - L)))
        seeds.append((y0, x0))
    return seeds


def _best_local_ncc(I_gray, y0, x0, L, transform_fn, search_radius, step, M_mask=None):
    h, w = I_gray.shape
    best = -1.0
    for dy in range(-search_radius, search_radius + 1, step):
        for dx in range(-search_radius, search_radius + 1, step):
            yy, xx = y0 + dy, x0 + dx
            if yy < 0 or xx < 0 or yy + L > h or xx + L > w:
                continue
            if M_mask is not None:
                region = M_mask[yy:yy + L, xx:xx + L]
                if region.size > 0 and np.mean(region > 0) > 0.15:
                    continue
            tile = I_gray[yy:yy + L, xx:xx + L]
            transformed = transform_fn(tile)
            if transformed.shape != tile.shape:
                continue
            score = _ncc(tile, transformed)
            if score > best:
                best = score
    return best


def classify_wallpaper_group(I_gray, a1, a2, M_mask=None, ncc_threshold=0.55, vote_fraction=0.5):
    h, w = I_gray.shape
    L = int(np.clip(round(1.5 * min(a1, a2)), 16, min(h, w) // 2))
    if L < 8:
        return "p1"

    seeds = _seed_positions(h, w, L, n_seeds=6)
    search_radius = int(max(8, min(a1, a2) / 2))
    step = max(2, search_radius // 6)

    def _vote(transform_fn):
        scores = [
            _best_local_ncc(I_gray, y0, x0, L, transform_fn, search_radius, step, M_mask)
            for (y0, x0) in seeds
        ]
        scores = [s for s in scores if s > -1.0]
        if not scores:
            return False
        passes = sum(1 for s in scores if s >= ncc_threshold)
        return (passes / len(scores)) >= vote_fraction

    ratio = a1 / a2 if a2 != 0 else 1.0
    is_square = abs(ratio - 1.0) < 0.20

    has_2fold = _vote(lambda t: np.rot90(t, 2))
    has_mirror_h = _vote(lambda t: np.fliplr(t))
    has_mirror_v = _vote(lambda t: np.flipud(t))
    has_mirror = has_mirror_h or has_mirror_v

    if is_square:
        has_4fold = _vote(lambda t: np.rot90(t, 1))
        if has_4fold and has_mirror:
            return "p4m"
        if has_4fold:
            return "p4"
        if has_2fold and has_mirror:
            return "cmm"
        if has_mirror:
            return "pm"
        if has_2fold:
            return "p2"
        return "p1"

    if has_2fold and (has_mirror_h and has_mirror_v):
        return "pmm"
    if has_2fold and has_mirror:
        return "cmm"
    if has_mirror:
        return "pm"
    if has_2fold:
        return "p2"
    return "p1"


GROUP_TO_TRANSFORMS = {
    "p1": ["identity"],
    "p2": ["identity", "rot180"],
    "pm": ["identity", "flip_lr"],
    "cmm": ["identity", "rot180", "flip_lr", "flip_ud"],
    "pmm": ["identity", "rot180", "flip_lr", "flip_ud"],
    "p4": ["identity", "rot90", "rot180", "rot270"],
    "p4m": ["identity", "rot90", "rot180", "rot270", "flip_lr", "flip_lr_rot90", "flip_lr_rot180", "flip_lr_rot270"],
    "p3m1": ["identity", "flip_lr"],
    "p6": ["identity", "rot180"],
    "p6m": ["identity", "rot180", "flip_lr", "flip_ud"],
}


def _generate_wallpaper_symmetries(patch, group="p1"):
    transforms = GROUP_TO_TRANSFORMS.get(group, ["identity"])
    target_shape = patch.shape[:2]
    variants = []

    for t in transforms:
        if t == "identity":
            var = patch.copy()
        elif t == "rot90":
            var = np.rot90(patch, 1)
        elif t == "rot180":
            var = np.rot90(patch, 2)
        elif t == "rot270":
            var = np.rot90(patch, 3)
        elif t == "flip_lr":
            var = np.fliplr(patch)
        elif t == "flip_ud":
            var = np.flipud(patch)
        elif t == "flip_lr_rot90":
            var = np.fliplr(np.rot90(patch, 1))
        elif t == "flip_lr_rot180":
            var = np.fliplr(np.rot90(patch, 2))
        elif t == "flip_lr_rot270":
            var = np.fliplr(np.rot90(patch, 3))
        else:
            var = patch.copy()

        if var.shape[:2] == target_shape:
            variants.append(var)

    return variants


# ==============================================================================
# ALGORITHM II: DEFECT ISOLATION MASK
# ==============================================================================

def _robust_low_threshold(arr, k=5.0, floor=None, ceil=None):
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med))) + 1e-6
    thresh = med - k * 1.4826 * mad
    if floor is not None:
        thresh = max(thresh, floor)
    if ceil is not None:
        thresh = min(thresh, ceil)
    return thresh


def _robust_high_threshold(arr, k=6.0, floor=None, ceil=None):
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med))) + 1e-6
    thresh = med + k * 1.4826 * mad
    if floor is not None:
        thresh = max(thresh, floor)
    if ceil is not None:
        thresh = min(thresh, ceil)
    return thresh


def run_algorithm_ii_defect_isolation(I_bgr, a1, a2, max_mask_fraction=0.12, min_defect_px=25):
    """
    ALGORITHM II: DEFECT ISOLATION MASK.
    """
    I_gray = cv2.cvtColor(I_bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
    h, w = I_gray.shape

    k_size = max(15, int(min(a1, a2) // 2))
    if k_size % 2 == 0:
        k_size += 1
    local_mean = cv2.boxFilter(I_gray.astype(np.float32), -1, (k_size, k_size))
    diff_map = np.abs(I_gray - local_mean)

    def _build_mask(k_dark, k_struct):
        dark_thresh = _robust_low_threshold(I_gray, k=k_dark, floor=15, ceil=90)
        m_dark = (I_gray < dark_thresh).astype(np.uint8) * 255

        struct_thresh = _robust_high_threshold(diff_map, k=k_struct, floor=35, ceil=120)
        m_struct = (diff_map > struct_thresh).astype(np.uint8) * 255

        return cv2.bitwise_or(m_dark, m_struct)

    k_dark, k_struct = 5.0, 6.0
    M_mask = _build_mask(k_dark, k_struct)
    total_px = h * w

    got_under_cap = False
    for _ in range(4):
        coverage = float(np.sum(M_mask > 0)) / total_px
        if coverage <= max_mask_fraction:
            got_under_cap = True
            break
        k_dark += 1.5
        k_struct += 1.5
        M_mask = _build_mask(k_dark, k_struct)
    if not got_under_cap:
        dark_thresh = _robust_low_threshold(I_gray, k=k_dark, floor=15, ceil=90)
        M_mask = (I_gray < dark_thresh).astype(np.uint8) * 255

    widen_k_dark, widen_k_struct = k_dark, k_struct
    for _ in range(6):
        if np.sum(M_mask > 0) >= min_defect_px:
            break
        widen_k_dark = max(1.5, widen_k_dark - 1.0)
        widen_k_struct = max(2.0, widen_k_struct - 1.0)
        M_mask = _build_mask(widen_k_dark, widen_k_struct)
        coverage = float(np.sum(M_mask > 0)) / total_px
        if coverage > max_mask_fraction:
            dark_thresh = _robust_low_threshold(I_gray, k=widen_k_dark, floor=15, ceil=90)
            M_mask = (I_gray < dark_thresh).astype(np.uint8) * 255

    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    M_mask = cv2.morphologyEx(M_mask, cv2.MORPH_OPEN, kernel_open)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(M_mask, connectivity=8)
    min_area = max(3, (k_size // 4) ** 2 // 4)
    cleaned = np.zeros_like(M_mask)
    for label_id in range(1, num_labels):
        if stats[label_id, cv2.CC_STAT_AREA] >= min_area:
            cleaned[labels == label_id] = 255
    M_mask = cleaned

    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    M_mask = cv2.dilate(M_mask, kernel_dilate, iterations=1)

    return M_mask, diff_map.astype(np.float32)


# ==============================================================================
# ALGORITHM III: SYMMETRY-AWARE LATTICE EXEMPLAR INPAINTING
# ==============================================================================

def run_algorithm_iii_template_alignment(
        I_color, M_mask, a1, a2, patch_size=32, stride=4, symmetry_group="p1"
):
    """
    ALGORITHM III: SYMMETRY-AWARE LATTICE EXEMPLAR INPAINTING.
    """
    if I_color.ndim != 3 or I_color.shape[2] != 3:
        raise ValueError(f"I_color must be a 3-channel BGR image, got shape {I_color.shape}")

    h, w, _ = I_color.shape
    I_out = I_color.copy()

    m = np.asarray(M_mask)
    if m.ndim == 3:
        m = m[:, :, 0]
    gt_mask = (m > 127).astype(np.uint8) * 255

    if gt_mask.shape != (h, w):
        raise ValueError(f"M_mask shape {gt_mask.shape} does not match image shape {(h, w)}")

    y_indices, x_indices = np.where(gt_mask == 255)
    if len(y_indices) == 0:
        return I_color.copy()

    half_p = patch_size // 2
    shift_x = int(round(a2)) if a2 >= 12 else 48
    shift_y = int(round(a1)) if a1 >= 12 else 48

    candidate_offsets = [
        (0, shift_x), (0, -shift_x),
        (shift_y, 0), (-shift_y, 0),
        (0, 2 * shift_x), (0, -2 * shift_x),
        (2 * shift_y, 0), (-2 * shift_y, 0),
        (shift_y, shift_x), (-shift_y, -shift_x),
        (shift_y, -shift_x), (-shift_y, shift_x),
        (0, 3 * shift_x), (0, -3 * shift_x),
        (3 * shift_y, 0), (-3 * shift_y, 0),
    ]

    CONTAMINATION_LIMIT = 0.15

    accum_value = np.zeros_like(I_color, dtype=np.float64)
    accum_weight = np.zeros((h, w), dtype=np.float64)

    for y, x in zip(y_indices[::stride], x_indices[::stride]):
        y1, y2 = max(0, y - half_p), min(h, y + half_p)
        x1, x2 = max(0, x - half_p), min(w, x + half_p)

        target_defect = gt_mask[y1:y2, x1:x2]
        if np.sum(target_defect) == 0:
            continue

        target_patch = I_color[y1:y2, x1:x2]
        target_valid = (target_defect == 0)

        best_donor = None
        best_donor_valid = None
        best_score = float("inf")

        for dy, dx in candidate_offsets:
            cy1, cy2 = y1 + dy, y2 + dy
            cx1, cx2 = x1 + dx, x2 + dx
            if not (0 <= cy1 and cy2 <= h and 0 <= cx1 and cx2 <= w):
                continue

            candidate_donor = I_color[cy1:cy2, cx1:cx2]
            candidate_mask = gt_mask[cy1:cy2, cx1:cx2]
            if candidate_donor.shape != target_patch.shape:
                continue

            contamination = float(np.mean(candidate_mask)) / 255.0
            if contamination >= CONTAMINATION_LIMIT:
                continue

            sym_donors = _generate_wallpaper_symmetries(candidate_donor, group=symmetry_group)
            sym_masks = _generate_wallpaper_symmetries(candidate_mask, group=symmetry_group)

            for sym_donor, sym_mask in zip(sym_donors, sym_masks):
                if sym_donor.shape != target_patch.shape:
                    continue
                donor_valid = (sym_mask == 0)
                combined_valid = target_valid & donor_valid

                if np.any(combined_valid):
                    diff = (target_patch[combined_valid].astype(np.float32) -
                            sym_donor[combined_valid].astype(np.float32))
                    score = float(np.mean(diff ** 2))
                else:
                    score = 1e6 + abs(dy) + abs(dx)

                if score < best_score:
                    best_score = score
                    best_donor = sym_donor
                    best_donor_valid = donor_valid

        if best_donor is not None:
            apply_mask = (target_defect == 255) & best_donor_valid
            if np.any(apply_mask):
                sub_val = accum_value[y1:y2, x1:x2]
                sub_w = accum_weight[y1:y2, x1:x2]
                sub_val[apply_mask] += best_donor[apply_mask].astype(np.float64)
                sub_w[apply_mask] += 1.0

    repaired = accum_weight > 0
    if np.any(repaired):
        blended = accum_value[repaired] / accum_weight[repaired, None]
        I_out[repaired] = np.clip(blended, 0, 255).astype(np.uint8)

    # GUARANTEE REPAIR: Hand any un-filled defect pixels to Telea fallback pass
    still_defective = cv2.bitwise_and(gt_mask, cv2.bitwise_not((repaired.astype(np.uint8) * 255)))
    if np.sum(still_defective) > 0:
        I_out = cv2.inpaint(I_out, still_defective, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

    # GUARANTEE CLEAN CANVAS: Non-defect pixels (gt_mask == 0) stay 100% untouched
    mask_bool_3d = np.repeat((gt_mask == 255)[:, :, np.newaxis], 3, axis=2)
    I_final = np.where(mask_bool_3d, I_out, I_color)

    return I_final.astype(np.uint8)