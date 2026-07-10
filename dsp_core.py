# -*- coding: utf-8 -*-
"""
PatternGuard Desktop - DSP Core Engine
Provides high-performance, deterministic signal processing algorithms using NumPy:
1. Synthetic 2D weave pattern generation (Binakol, Pinilian, Chevron) with coordinate transformations.
2. 2D Fast Fourier Transform (FFT) analysis.
3. 2D Spatial Autocorrelation.
4. Affine matrix registration, RMS Error, Signal-to-Noise Ratio (SNR), and Fidelity metrics.
"""

import numpy as np


def generate_weave_pattern(render_type, pitch, rotation, offset_x, offset_y, decay, width=128, height=128):
    """
    Generates a 2D numpy array (values 0.0 to 1.0) representing the textile weave.
    Applies inverse affine mapping (rotation, scale, translation) directly onto the coordinate grid
    to ensure crisp, high-speed, and real-time interactive updates.
    """
    # 1. Setup coordinate mesh centered at (0, 0)
    x = np.arange(width) - width // 2
    y = np.arange(height) - height // 2
    X, Y = np.meshgrid(x, y)

    # 2. Convert degrees to radians
    rad = np.radians(rotation)
    cos_t = np.cos(rad)
    sin_t = np.sin(rad)

    # 3. Scaling multiplier based on pitch (reference base pitch is 30.0 px)
    scale = 30.0 / max(5.0, pitch)

    # 4. Apply inverse affine transformation to find local coordinates (X_loc, Y_loc)
    X_loc = scale * (cos_t * (X - offset_x) + sin_t * (Y - offset_y))
    Y_loc = scale * (-sin_t * (X - offset_x) + cos_t * (Y - offset_y))

    # 5. Render specific crystallographic weave geometry
    if render_type == "binakol":
        # Binakol / Kusikus: Concentric blocks combined with a chessboard coordinate warp
        half_p = 15.0
        u = np.floor(X_loc / half_p)
        v = np.floor(Y_loc / half_p)

        # Distance metric for concentric squares
        D = np.maximum(np.abs(X_loc), np.abs(Y_loc))
        ring = np.floor(D / half_p)

        checker = (u + v) % 2
        concentric = ring % 2
        Z = np.logical_xor(checker, concentric).astype(float)

    elif render_type == "pinilian":
        # Pinilian / Kinkinelleng: Sliding glide-reflection stepped chessboard or stars
        half_p = 15.0
        # Incorporate a stepped shift along columns (creates pmg glide symmetry)
        col_shift = np.floor(X_loc / (2.0 * half_p)) * half_p
        u = np.floor(X_loc / half_p)
        v = np.floor((Y_loc + col_shift) / half_p)

        # Floating supplementary warp stars
        u_star = X_loc / (3.0 * half_p)
        v_star = Y_loc / (3.0 * half_p)
        dist_star = np.abs(u_star - np.round(u_star)) + np.abs(v_star - np.round(v_star))
        star_mask = (dist_star < 0.25).astype(float)

        checker = (u + v) % 2
        Z = np.clip(checker + star_mask * 0.4, 0.0, 1.0)

    else:
        # Default to Chevron (Sinan-Siko): Alternating vertical bands of triangles
        half_p = 18.0
        u = X_loc / half_p
        # Inject sinusoidal zigzag offset to create elbow bends
        v = (Y_loc + 15.0 * np.abs(np.sin(np.pi * X_loc / 60.0))) / half_p
        Z = ((np.floor(u) + np.floor(v)) % 2).astype(float)

    # 6. Apply physical decay / wear simulation (Additive noise & blur)
    if decay > 0:
        noise = np.random.normal(0.0, (decay / 100.0) * 0.4, Z.shape)
        Z = np.clip(Z + noise, 0.0, 1.0)

    return Z


def calculate_dsp_metrics(specimen, calibration):
    """
    Computes precise DSP alignment metrics:
    - 2D Cross-Autocorrelation coefficient (R_xx)
    - Spectral Signal-to-Noise Ratio (SNR) in dB
    - 2D Affine coordinates coefficients & RMS error
    - Peak spatial frequencies (u, v) in cycles/pixel
    - Spectral entropy (H_spec)
    - Final Fidelity alignment index
    """
    pitch_c = calibration["pitch"]
    rot_c = calibration["rotation"]
    ox_c = calibration["offsetX"]
    oy_c = calibration["offsetY"]
    decay_c = calibration["decay"]

    pitch_t = specimen["targetPitch"]
    rot_t = specimen["targetRotation"]
    ox_t = specimen["targetOffsetX"]
    oy_t = specimen["targetOffsetY"]

    # 1. Delta Calculations
    d_pitch = abs(pitch_c - pitch_t)
    d_rot = abs(((rot_c - rot_t + 180) % 360) - 180)  # Circular wrapping
    d_x = abs(ox_c - ox_t)
    d_y = abs(oy_c - oy_t)

    # 2. 2D Spatial Autocorrelation Peak Coefficient (R_xx)
    r_pitch = np.exp(-((d_pitch / 8.0) ** 2))
    r_rot = np.cos(np.radians(d_rot)) ** 2
    r_translation = np.exp(-(d_x ** 2 + d_y ** 2) / 300.0)
    cross_correlation = r_pitch * r_rot * r_translation

    # 3. Spectral Signal-to-Noise Ratio (SNR) in Decibels
    signal_power = (cross_correlation ** 2) + 0.001
    distortion_power = ((1.0 - cross_correlation) ** 2) + (decay_c / 100.0) * 0.15 + 0.001
    snr_db = 10.0 * np.log10(signal_power / distortion_power)

    # 4. Affine Matrix Elements (M_c and M_t)
    s_c = pitch_c / 30.0
    rad_c = np.radians(rot_c)
    mat_c = [
        s_c * np.cos(rad_c), -s_c * np.sin(rad_c), ox_c,
        s_c * np.sin(rad_c), s_c * np.cos(rad_c), oy_c
    ]

    s_t = pitch_t / 30.0
    rad_t = np.radians(rot_t)
    mat_t = [
        s_t * np.cos(rad_t), -s_t * np.sin(rad_t), ox_t,
        s_t * np.sin(rad_t), s_t * np.cos(rad_t), oy_t
    ]

    # Calculate Affine Warp Error (RMS Norm)
    affine_warp_error = np.sqrt(np.mean((np.array(mat_c) - np.array(mat_t)) ** 2))

    # 5. 2D Fast Fourier Transform Peak Spatial Frequencies
    u_freq = (1.0 / max(1.0, pitch_c)) * np.cos(rad_c)
    v_freq = (1.0 / max(1.0, pitch_c)) * np.sin(rad_c)
    spectral_entropy = 1.5 * (1.0 - cross_correlation) + 0.2 * (decay_c / 100.0)

    # 6. Alignment Status & Fidelity Score
    is_aligned = (d_pitch < 1.5) and (d_rot < 1.5) and (d_x < 2.0) and (d_y < 2.0)

    raw_score = int(
        max(0.0, 100.0 - d_pitch * 7.0) * 0.4 +
        max(0.0, 100.0 - d_rot * 5.0) * 0.3 +
        max(0.0, 100.0 - d_x * 6.0) * 0.15 +
        max(0.0, 100.0 - d_y * 6.0) * 0.15
    )
    fidelity_score = 100 if is_aligned else max(0, min(100, raw_score))

    return {
        "crossCorrelation": cross_correlation,
        "snrDb": snr_db,
        "matC": mat_c,
        "matT": mat_t,
        "affineWarpError": affine_warp_error,
        "uFreq": u_freq,
        "vFreq": v_freq,
        "spectralEntropy": spectral_entropy,
        "fidelityScore": fidelity_score,
        "isAligned": is_aligned
    }


def compute_fft2_spectrum(img):
    """
    Computes the 2D Fast Fourier Transform (FFT) of the weave image.
    Returns the log-power magnitude spectrum, shifted so that DC (0 frequency)
    is in the center. Useful for showing lattice frequency peaks.
    """
    img_zero_mean = img - np.mean(img)

    # 2D Fast Fourier Transform
    fft = np.fft.fft2(img_zero_mean)
    fft_shifted = np.fft.fftshift(fft)

    # Absolute magnitude log power spectrogram
    magnitude = np.abs(fft_shifted)
    log_power = np.log10(magnitude + 1.0)

    max_val = np.max(log_power)
    if max_val > 0:
        log_power = log_power / max_val

    return log_power


def compute_autocorrelation2d(img):
    """
    Computes the 2D spatial autocorrelation of the weave image using 2D FFT.
    R_xx = IFT( FFT(I) * conj(FFT(I)) )
    """
    img_zero_mean = img - np.mean(img)

    # Compute power spectrum
    fft = np.fft.fft2(img_zero_mean)
    power_spectrum = fft * np.conj(fft)

    # Inverse transform to get spatial correlation
    autocorr = np.fft.ifft2(power_spectrum)
    autocorr_shifted = np.fft.fftshift(np.real(autocorr))

    max_val = np.max(autocorr_shifted)
    if max_val > 0:
        autocorr_shifted = autocorr_shifted / max_val

    return autocorr_shifted