from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import cv2
import numpy as np
from scipy.optimize import minimize


ProgressCallback = Callable[[str, int, int], None]


@dataclass
class OptimizationResult:
    dx: int
    dy: int
    scale_x: float
    scale_y: float
    angle: float
    score: float
    success: bool
    message: str
    iterations: int
    evaluations: int


def _prepare_feature_image(image: np.ndarray) -> np.ndarray:
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    gray = gray.astype(np.float32) / 255.0
    gray = cv2.normalize(gray, None, 0.0, 1.0, cv2.NORM_MINMAX)

    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(grad_x, grad_y)
    magnitude = cv2.normalize(magnitude, None, 0.0, 1.0, cv2.NORM_MINMAX)

    feature = 0.55 * gray + 0.45 * magnitude
    feature = cv2.normalize(feature, None, 0.0, 1.0, cv2.NORM_MINMAX)
    return feature.astype(np.float32)


def _prepare_ecc_image(image: np.ndarray) -> np.ndarray:
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    return gray.astype(np.float32) / 255.0


def _resize_pair(
    ir_img: np.ndarray,
    vis_img: np.ndarray,
    max_side: int = 512,
) -> tuple[np.ndarray, np.ndarray, float]:
    height, width = ir_img.shape[:2]
    scale = min(1.0, max_side / float(max(height, width)))

    if scale == 1.0:
        return ir_img, vis_img, 1.0

    new_size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    resized_ir = cv2.resize(ir_img, new_size, interpolation=cv2.INTER_AREA)
    resized_vis = cv2.resize(vis_img, new_size, interpolation=cv2.INTER_AREA)
    return resized_ir, resized_vis, scale


def _build_transform(
    shape: tuple[int, int],
    dx: float,
    dy: float,
    scale_x: float,
    scale_y: float,
    angle: float,
) -> np.ndarray:
    height, width = shape[:2]
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    matrix[0, 0] *= scale_x
    matrix[1, 1] *= scale_y
    matrix[0, 2] += dx
    matrix[1, 2] += dy
    return matrix


def _warp_feature(
    feature_image: np.ndarray,
    mask: np.ndarray,
    dx: float,
    dy: float,
    scale_x: float,
    scale_y: float,
    angle: float,
) -> tuple[np.ndarray, np.ndarray]:
    height, width = feature_image.shape[:2]
    matrix = _build_transform(feature_image.shape, dx, dy, scale_x, scale_y, angle)
    warped_feature = cv2.warpAffine(
        feature_image,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    warped_mask = cv2.warpAffine(
        mask,
        matrix,
        (width, height),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    return warped_feature, warped_mask


def _compute_similarity(
    warped_ir: np.ndarray,
    vis_feature: np.ndarray,
    overlap_mask: np.ndarray,
) -> tuple[float, float]:
    ir_values = warped_ir[overlap_mask]
    vis_values = vis_feature[overlap_mask]

    if ir_values.size < 64:
        return -1.0, 1.0

    ir_centered = ir_values - ir_values.mean()
    vis_centered = vis_values - vis_values.mean()

    denominator = np.linalg.norm(ir_centered) * np.linalg.norm(vis_centered)
    if denominator < 1e-8:
        correlation = -1.0
    else:
        correlation = float(np.dot(ir_centered, vis_centered) / denominator)

    mse = float(np.mean((ir_values - vis_values) ** 2))
    return correlation, mse


def _estimate_initial_guess_with_ecc(
    ir_image: np.ndarray,
    vis_image: np.ndarray,
) -> np.ndarray | None:
    vis_gray = _prepare_ecc_image(vis_image)
    ir_gray = _prepare_ecc_image(ir_image)
    warp = np.eye(2, 3, dtype=np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 150, 1e-5)

    try:
        cv2.findTransformECC(
            vis_gray,
            ir_gray,
            warp,
            cv2.MOTION_AFFINE,
            criteria,
            None,
            1,
        )
    except cv2.error:
        return None

    warp = cv2.invertAffineTransform(warp)
    scale_x = float(np.linalg.norm(warp[:, 0]))
    scale_y = float(np.linalg.norm(warp[:, 1]))
    dx = float(warp[0, 2])
    dy = float(warp[1, 2])
    return np.array([dx, dy, scale_x, scale_y], dtype=np.float64)


def optimize_registration(
    ir_image: np.ndarray,
    vis_image: np.ndarray,
    initial_dx: int = 0,
    initial_dy: int = 0,
    initial_scale_x: float = 1.0,
    initial_scale_y: float = 1.0,
    angle: float = 0.0,
    progress_callback: ProgressCallback | None = None,
) -> OptimizationResult:
    if ir_image is None or vis_image is None:
        raise ValueError("输入图像不能为空")

    if ir_image.shape[:2] != vis_image.shape[:2]:
        vis_image = cv2.resize(vis_image, (ir_image.shape[1], ir_image.shape[0]), interpolation=cv2.INTER_LINEAR)

    resized_ir, resized_vis, resize_scale = _resize_pair(ir_image, vis_image)
    ir_feature = _prepare_feature_image(resized_ir)
    vis_feature = _prepare_feature_image(resized_vis)
    valid_mask = np.ones(ir_feature.shape[:2], dtype=np.uint8)

    scaled_initial = np.array(
        [
            initial_dx * resize_scale,
            initial_dy * resize_scale,
            initial_scale_x,
            initial_scale_y,
        ],
        dtype=np.float64,
    )

    max_translation = 1000.0 * resize_scale
    bounds = [
        (-max_translation, max_translation),
        (-max_translation, max_translation),
        (0.5, 2.0),
        (0.5, 2.0),
    ]

    ecc_initial = _estimate_initial_guess_with_ecc(resized_ir, resized_vis)
    if ecc_initial is not None:
        ecc_initial[0] = float(np.clip(ecc_initial[0], bounds[0][0], bounds[0][1]))
        ecc_initial[1] = float(np.clip(ecc_initial[1], bounds[1][0], bounds[1][1]))
        ecc_initial[2] = float(np.clip(ecc_initial[2], bounds[2][0], bounds[2][1]))
        ecc_initial[3] = float(np.clip(ecc_initial[3], bounds[3][0], bounds[3][1]))

    eval_count = 0
    callback_count = 0

    def objective(params: np.ndarray) -> float:
        nonlocal eval_count
        eval_count += 1

        dx, dy, scale_x, scale_y = params
        warped_ir, warped_mask = _warp_feature(ir_feature, valid_mask, dx, dy, scale_x, scale_y, angle)
        overlap_mask = warped_mask > 0
        overlap_ratio = float(np.mean(overlap_mask))

        if overlap_ratio < 0.1:
            return 10.0 + (0.1 - overlap_ratio) * 100.0

        correlation, mse = _compute_similarity(warped_ir, vis_feature, overlap_mask)
        scale_penalty = 0.02 * ((scale_x - 1.0) ** 2 + (scale_y - 1.0) ** 2)
        overlap_penalty = 0.25 * (1.0 - overlap_ratio)
        mse_weight = 0.15
        return (1.0 - correlation) + mse_weight * mse + scale_penalty + overlap_penalty

    def callback(_: np.ndarray) -> None:
        nonlocal callback_count
        callback_count += 1
        if progress_callback is not None:
            progress_callback("正在自动优化参数...", callback_count, eval_count)

    if progress_callback is not None:
        progress_callback("正在初始化自动优化...", 0, 0)

    start_point = scaled_initial
    if ecc_initial is not None:
        if progress_callback is not None:
            progress_callback("已生成 ECC 初始估计，开始精修...", 0, eval_count)
        if objective(ecc_initial) < objective(scaled_initial):
            start_point = ecc_initial

    coarse_result = minimize(
        objective,
        start_point,
        method="Powell",
        bounds=bounds,
        callback=callback,
        options={"maxiter": 40, "xtol": 1e-2, "ftol": 1e-3},
    )

    refined_result = minimize(
        objective,
        coarse_result.x,
        method="L-BFGS-B",
        bounds=bounds,
        callback=callback,
        options={"maxiter": 80, "ftol": 1e-6},
    )

    best = refined_result if refined_result.fun <= coarse_result.fun else coarse_result
    best_dx = int(round(best.x[0] / max(resize_scale, 1e-8)))
    best_dy = int(round(best.x[1] / max(resize_scale, 1e-8)))
    best_scale_x = float(best.x[2])
    best_scale_y = float(best.x[3])

    best_warped, best_mask = _warp_feature(
        ir_feature,
        valid_mask,
        best.x[0],
        best.x[1],
        best_scale_x,
        best_scale_y,
        angle,
    )
    best_overlap = best_mask > 0
    final_score, _ = _compute_similarity(best_warped, vis_feature, best_overlap)
    message = best.message if isinstance(best.message, str) else str(best.message)

    if progress_callback is not None:
        progress_callback("自动优化完成", callback_count, eval_count)

    return OptimizationResult(
        dx=best_dx,
        dy=best_dy,
        scale_x=best_scale_x,
        scale_y=best_scale_y,
        angle=float(angle),
        score=final_score,
        success=bool(best.success),
        message=message,
        iterations=callback_count,
        evaluations=eval_count,
    )
