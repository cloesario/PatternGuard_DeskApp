"FFT and NCC for wallpaper group classification"

import cv2
import numpy as np
import scipy.fft as fft

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

"ALGORITHM I: 2D Wiener-Khinchin FFT & Wallpaper Group Classification."
def run_algorithm_i_autocorrelation(I_gray):
    F = fft.fft2(I_gray)
    S = F * np.conj(F)
    R_xx = fft.ifft2(S)
    R_xx = np.abs(fft.fftshift(R_xx))
    h, w = I_gray.shape
    cy, cx = h // 2, w // 2

    R_xx_filtered = R_xx.copy()
    cv2.circle(R_xx_filtered, (cx, cy), 20, 0, -1)
    _, _, _, max_loc = cv2.minMaxLoc(R_xx_filtered)

    a2_val = float(abs(max_loc[0] - cx))
    a1_val = float(abs(max_loc[1] - cy))

    if a1_val < 15:
        a1_val = 48.0
    if a2_val < 15:
        a2_val = 48.0

    theta_dom = float(np.degrees(np.arctan2(a1_val, a2_val)))

    try:
        detected_group = classify_wallpaper_group(I_gray, a1_val, a2_val)
    except Exception as e:
        print(f"[Wallpaper Classification Warning] {e}")
        detected_group = "p1"

    return R_xx, a1_val, a2_val, theta_dom, detected_group


"ALGORITHM II: Defect Isolation Mask"

def run_algorithm_ii_defect_isolation(I_bgr, a1, a2):

    I_gray = cv2.cvtColor(I_bgr, cv2.COLOR_BGR2GRAY)

    # 1. Target pure black / artificial cuts
    _, M_dark = cv2.threshold(I_gray, 25, 255, cv2.THRESH_BINARY_INV)

    # 2. Measure local variance strictly for unnatural anomalies
    k_size = max(15, int(min(a1, a2) // 2))
    if k_size % 2 == 0:
        k_size += 1

    local_mean = cv2.boxFilter(I_gray, -1, (k_size, k_size))
    diff_map = cv2.absdiff(I_gray, local_mean)

    # High threshold (120) prevents woven patterns from triggering false positives
    _, structural_anomalies = cv2.threshold(diff_map, 120, 255, cv2.THRESH_BINARY)

    # Combine dark cuts and severe structural anomalies
    M_mask = cv2.bitwise_or(M_dark, structural_anomalies)

    # Morphological opening removes isolated single-pixel weave false positives
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    M_mask = cv2.morphologyEx(M_mask, cv2.MORPH_OPEN, kernel_open)

    # Slight dilation to cover edges
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    M_mask = cv2.dilate(M_mask, kernel_dilate, iterations=1)

    return M_mask, diff_map.astype(np.float32)

"ALGORITHM III: Exemplar Inpainting"
def run_algorithm_iii_template_alignment(I_color, M_mask, a1, a2, patch_size=32, stride=8, symmetry_group="p1"):

    h, w, c = I_color.shape
    I_out = I_color.copy()

    # Ensure 2D mask
    if M_mask.ndim == 3:
        M_mask = M_mask[:, :, 0]

    y_indices, x_indices = np.where(M_mask == 255)
    if len(y_indices) == 0:
        return I_color

    half_p = patch_size // 2
    shift_x = int(a2) if a2 >= 12 else 48
    shift_y = int(a1) if a1 >= 12 else 48

    # Lattice candidate displacement vectors
    candidate_offsets = [
        (0, shift_x), (0, -shift_x),
        (shift_y, 0), (-shift_y, 0),
        (0, 2 * shift_x), (0, -2 * shift_x),
        (2 * shift_y, 0), (-2 * shift_y, 0),
        (shift_y, shift_x), (-shift_y, -shift_x),
        (shift_y, -shift_x), (-shift_y, shift_x)
    ]

    working_mask = M_mask.copy()
    for y, x in zip(y_indices[::stride], x_indices[::stride]):
        y1, y2 = max(0, y - half_p), min(h, y + half_p)
        x1, x2 = max(0, x - half_p), min(w, x + half_p)
        p_h, p_w = y2 - y1, x2 - x1

        target_defect = working_mask[y1:y2, x1:x2]
        if np.sum(target_defect) == 0:
            continue

        best_donor = None
        min_ssd = float("inf")
        target_patch = I_out[y1:y2, x1:x2]
        valid_pixel_mask = (target_defect == 0)

        for dy, dx in candidate_offsets:
            cy1, cy2 = y1 + dy, y2 + dy
            cx1, cx2 = x1 + dx, x2 + dx
            if 0 <= cy1 and cy2 <= h and 0 <= cx1 and cx2 <= w:
                candidate_donor = I_out[cy1:cy2, cx1:cx2]
                candidate_mask = M_mask[cy1:cy2, cx1:cx2]

                # Donor patch must be clean
                if np.sum(candidate_mask) == 0:
                    if np.any(valid_pixel_mask):
                        diff = (target_patch[valid_pixel_mask].astype(np.float32) -
                                candidate_donor[valid_pixel_mask].astype(np.float32))
                        ssd = np.sum(diff ** 2)
                    else:
                        ssd = 0.0

                    if ssd < min_ssd:
                        min_ssd = ssd
                        best_donor = candidate_donor

        if best_donor is not None and best_donor.shape == target_patch.shape:
            blend_mask = np.zeros((p_h, p_w), dtype=np.float32)
            blend_mask[target_defect == 255] = 1.0
            blend_mask = cv2.GaussianBlur(blend_mask, (3, 3), 0)
            blend_mask = np.expand_dims(blend_mask, axis=-1)

            inpainted = (1.0 - blend_mask) * target_patch + blend_mask * best_donor
            I_out[y1:y2, x1:x2] = np.clip(inpainted, 0, 255).astype(np.uint8)
            working_mask[y1:y2, x1:x2] = 0

    # Clean fallback restricted strictly to remaining un-reconstructed defect pixels
    unrepaired_mask = cv2.bitwise_and(M_mask, working_mask)
    if np.sum(unrepaired_mask) > 0:
        I_out = cv2.inpaint(I_out, unrepaired_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    return I_out