import cv2
import numpy as np
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize
import time
from typing import Tuple
from pathlib import Path

# Try to import KD-tree for faster nearest-neighbor. If unavailable, we'll fall back
# to the brute-force approach already present in icp_rigid.
try:
    from scipy.spatial import cKDTree as KDTree
except Exception:
    KDTree = None

def adjust_exposure_gamma(image, gamma=0.5, gain=1.0):
    """
    Adjusts the exposure and gamma of an image to isolate bright regions.
    A lower gamma value darkens the image, making bright areas like lasers pop.
    
    Args:
        image (numpy.ndarray): The input image.
        gamma (float): Gamma correction value. < 1 darkens, > 1 lightens.
        gain (float): A multiplier for brightness (not used in this version).
            
    Returns:
        numpy.ndarray: The adjusted image.
    """
    # Build a lookup table mapping the pixel values [0, 255] to
    # their adjusted gamma values.
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255
                      for i in np.arange(0, 256)]).astype("uint8")

    # Apply the gamma correction using the lookup table
    return cv2.LUT(image, table)

def align_images(im1, im2):
    """
    Aligns im2 to im1 using ORB feature matching.
    This corrects for small shifts or rotations between the two images.
    
    Args:
        im1 (numpy.ndarray): The reference image.
        im2 (numpy.ndarray): The image to be aligned.
            
    Returns:
        tuple: A tuple containing the aligned image and the homography matrix.
    """
    # Convert images to grayscale for feature detection
    im1_gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
    im2_gray = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)

    # --- 1. Detect ORB features and compute descriptors ---
    MAX_FEATURES = 5000
    GOOD_MATCH_PERCENT = 0.15
    orb = cv2.ORB_create(MAX_FEATURES)
    keypoints1, descriptors1 = orb.detectAndCompute(im1_gray, None)
    keypoints2, descriptors2 = orb.detectAndCompute(im2_gray, None)

    if descriptors1 is None or descriptors2 is None:
        print("Warning: Could not find features in one or both images for alignment.")
        # Return original image if features can't be found
        return im2, np.identity(3) 

    # --- 2. Match features ---
    matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
    matches = matcher.match(descriptors2, descriptors1, None)

    # Sort matches by score
    matches = sorted(matches, key=lambda x: x.distance, reverse=False)

    # Keep only the best matches
    num_good_matches = int(len(matches) * GOOD_MATCH_PERCENT)
    matches = matches[:num_good_matches]

    # --- 3. Find Homography ---
    points1 = np.zeros((len(matches), 2), dtype=np.float32)
    points2 = np.zeros((len(matches), 2), dtype=np.float32)

    for i, match in enumerate(matches):
        points1[i, :] = keypoints1[match.trainIdx].pt
        points2[i, :] = keypoints2[match.queryIdx].pt

    # Find the perspective transformation matrix
    try:
        h, mask = cv2.findHomography(points2, points1, cv2.RANSAC)
    except cv2.error as e:
        print(f"Warning: Homography calculation failed: {e}. Returning original image.")
        return im2, np.identity(3) 

    if h is None:
        print("Warning: Homography could not be computed. Using original image.")
        return im2, np.identity(3)

    # --- 4. Warp image ---
    height, width, channels = im1.shape
    im2_aligned = cv2.warpPerspective(im2, h, (width, height))

    return im2_aligned, h

def get_laser_mask(image):
    """
    Isolates the red laser line using advanced filtering and thresholding.
    """
    # --- 1. Programmatically adjust exposure and gamma ---
    adjusted_image = adjust_exposure_gamma(image, gamma=0.5)

    # --- 2. Isolate Red Channel and Threshold ---
    red_channel = adjusted_image[:, :, 2]
    _, thresholded = cv2.threshold(red_channel, 200, 255, cv2.THRESH_BINARY)
    
    # --- 3. Morphological Cleaning ---
    # First, use OPEN to remove small noise specks from the background
    open_kernel = np.ones((3, 3), np.uint8)
    opened_mask = cv2.morphologyEx(thresholded, cv2.MORPH_OPEN, open_kernel, iterations=2)
    
    # Then, use CLOSE with a larger kernel to fill gaps in the main laser line
    close_kernel = np.ones((11, 11), np.uint8)
    final_mask = cv2.morphologyEx(opened_mask, cv2.MORPH_CLOSE, close_kernel, iterations=2)
    
    return final_mask, adjusted_image

def clean_skeleton(skeleton):
    """
    Finds all contours in a skeleton image and returns a new image containing only
    the single longest contour, which represents the main profile line.
    """
    # Find all contours in the skeleton
    contours, _ = cv2.findContours(skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # If no contours are found, return a blank image
    if not contours:
        return np.zeros_like(skeleton), None
            
    # Find the single longest contour
    longest_contour = max(contours, key=lambda c: cv2.arcLength(c, False))
    
    # Create a blank image and draw only the longest contour on it
    cleaned_skeleton = np.zeros_like(skeleton)
    cv2.drawContours(cleaned_skeleton, [longest_contour], -1, 255, 1)
    
    return cleaned_skeleton, longest_contour


def segment_profile(contour):
    """
    Segments a profile contour into top and bottom anchor sections for alignment.
    """
    if contour is None:
        return None, None

    # Define anchors as a percentage of the contour's total length
    num_points_for_anchor = max(10, int(len(contour) * 0.25)) # Use 25% or 10 points
    
    # Ensure we don't try to take more points than exist
    if 2 * num_points_for_anchor > len(contour):
        num_points_for_anchor = len(contour) // 3

    if num_points_for_anchor == 0:
        return None, None

    # The contour points are ordered. The start and end are the two ends of the laser line.
    top_anchor = contour[:num_points_for_anchor]
    bottom_anchor = contour[-num_points_for_anchor:]

    return top_anchor, bottom_anchor


def _compute_rigid_transform(src: np.ndarray, dst: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Compute the 2D rigid transform (rotation + translation, no scale) that
    best aligns src -> dst in a least-squares sense using SVD (Umeyama-like
    but constrained to rigid: scale=1).

    Returns a 3x3 homogeneous transform matrix and the mean residual error.
    """
    if src.size == 0 or dst.size == 0:
        return np.eye(3), float('inf')

    src_mean = src.mean(axis=0)
    dst_mean = dst.mean(axis=0)
    src_centered = src - src_mean
    dst_centered = dst - dst_mean

    # Covariance
    H = src_centered.T @ dst_centered
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    # Ensure proper rotation (det=+1)
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T

    t = dst_mean - (R @ src_mean)

    T = np.eye(3)
    T[0:2, 0:2] = R
    T[0:2, 2] = t

    # compute mean residual
    src_trans = (R @ src.T).T + t
    residuals = np.linalg.norm(src_trans - dst, axis=1)
    mean_err = float(np.mean(residuals)) if residuals.size > 0 else float('inf')
    return T, mean_err


def _compute_similarity_transform(src: np.ndarray, dst: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Compute similarity transform (rotation + uniform scale + translation)
    mapping src -> dst using a closed-form solution (Umeyama, but allowing only
    uniform scale). Returns 3x3 homogeneous transform and mean residual error.
    """
    if src.size == 0 or dst.size == 0:
        return np.eye(3), float('inf')

    src_mean = src.mean(axis=0)
    dst_mean = dst.mean(axis=0)
    src_centered = src - src_mean
    dst_centered = dst - dst_mean

    # Compute variance for scale estimator
    var_src = (src_centered ** 2).sum() / src_centered.shape[0]
    # Covariance
    H = src_centered.T @ dst_centered / src_centered.shape[0]
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T

    # uniform scale
    scale = np.trace(np.diag(S)) / var_src if var_src > 0 else 1.0

    t = dst_mean - scale * (R @ src_mean)

    T = np.eye(3)
    T[0:2, 0:2] = scale * R
    T[0:2, 2] = t

    src_trans = (scale * (R @ src.T)).T + t
    residuals = np.linalg.norm(src_trans - dst, axis=1)
    mean_err = float(np.mean(residuals)) if residuals.size > 0 else float('inf')
    return T, mean_err


def icp_rigid(src_pts: np.ndarray, dst_pts: np.ndarray, max_iter: int = 50, tol: float = 1e-4,
              outlier_threshold: float = 25.0, use_kdtree: bool = True,
              allow_scale: bool = False) -> Tuple[np.ndarray, np.ndarray]:
    """
    A simple ICP-like rigid alignment: iteratively find nearest neighbours from
    src -> dst, reject outliers, compute best rigid transform and apply.

    Returns transformed_src (Nx2) and 3x3 transform matrix that maps original src -> transformed_src.
    """
    if src_pts is None or dst_pts is None:
        return src_pts, np.eye(3)
    src = np.asarray(src_pts, dtype=float).reshape(-1, 2)
    dst = np.asarray(dst_pts, dtype=float).reshape(-1, 2)
    if src.shape[0] < 2 or dst.shape[0] < 2:
        return src, np.eye(3)

    prev_error = float('inf')
    current_src = src.copy()
    total_T = np.eye(3)

    for i in range(max_iter):
        # Nearest neighbour: prefer KDTree if available and requested
        if use_kdtree and KDTree is not None:
            tree = KDTree(dst)
            nn_dists, nn_idx = tree.query(current_src, k=1)
        else:
            dists = np.sqrt(((current_src[:, None, :] - dst[None, :, :]) ** 2).sum(axis=2))
            nn_idx = dists.argmin(axis=1)
            nn_dists = dists[np.arange(dists.shape[0]), nn_idx]

        # Reject outliers based on threshold (robustness)
        inlier_mask = nn_dists <= outlier_threshold
        if inlier_mask.sum() < 2:
            break

        src_in = current_src[inlier_mask]
        dst_in = dst[nn_idx[inlier_mask]]

        # Compute transform from src_in -> dst_in
        if allow_scale:
            T, mean_err = _compute_similarity_transform(src_in, dst_in)
        else:
            T, mean_err = _compute_rigid_transform(src_in, dst_in)

        # Apply transform to all src points
        R = T[0:2, 0:2]
        t = T[0:2, 2]
        current_src = (R @ current_src.T).T + t

        # Accumulate transforms: new_total = T * total_T
        total_T = T @ total_T

        if abs(prev_error - mean_err) < tol:
            break
        prev_error = mean_err

    return current_src, total_T


def ransac_global_fit(src_pts: np.ndarray, dst_pts: np.ndarray, n_iter: int = 200,
                      inlier_threshold: float = 25.0, allow_scale: bool = False,
                      min_inliers: int = 10) -> Tuple[np.ndarray, float, np.ndarray]:
    """
    RANSAC-based global fit: randomly sample minimal correspondences (2 points)
    and compute a similarity/rigid transform, count inliers, and return the best transform.

    Returns (best_T, best_error, inlier_mask)
    """
    src = np.asarray(src_pts, dtype=float).reshape(-1, 2)
    dst = np.asarray(dst_pts, dtype=float).reshape(-1, 2)
    if src.shape[0] < 2 or dst.shape[0] < 2:
        return np.eye(3), float('inf'), np.zeros(src.shape[0], dtype=bool)

    best_T = np.eye(3)
    best_err = float('inf')
    best_inliers = np.zeros(src.shape[0], dtype=bool)

    # For matching we assume order is unknown; we'll use nearest neighbors from src->dst
    # Build KD-tree for dst if available
    if KDTree is not None:
        tree = KDTree(dst)
        dists0, nn0 = tree.query(src, k=1)
    else:
        dists_full = np.sqrt(((src[:, None, :] - dst[None, :, :]) ** 2).sum(axis=2))
        nn0 = dists_full.argmin(axis=1)

    # Corresponding points (initial) - these are candidate pairs
    corr_dst = dst[nn0]

    rng = np.random.default_rng()
    n_src = src.shape[0]

    for _ in range(n_iter):
        # sample two source indices
        i1, i2 = rng.choice(n_src, size=2, replace=False)
        s_sample = np.vstack([src[i1], src[i2]])
        d_sample = np.vstack([corr_dst[i1], corr_dst[i2]])

        # compute transform
        try:
            if allow_scale:
                T, _ = _compute_similarity_transform(s_sample, d_sample)
            else:
                T, _ = _compute_rigid_transform(s_sample, d_sample)
        except Exception:
            continue

        R = T[0:2, 0:2]
        t = T[0:2, 2]
        src_trans = (R @ src.T).T + t
        dists = np.linalg.norm(src_trans - corr_dst, axis=1)
        inliers = dists <= inlier_threshold
        n_in = int(inliers.sum())
        if n_in < min_inliers:
            continue

        mean_err = float(dists[inliers].mean()) if n_in > 0 else float('inf')
        if n_in > int(best_inliers.sum()) or (n_in == int(best_inliers.sum()) and mean_err < best_err):
            best_inliers = inliers
            best_T = T
            best_err = mean_err

    return best_T, best_err, best_inliers



def analyze_dent(perfect_image_path, dented_image_path, show_plot=True, output_path="profile_comparison.jpg",
                 align_mode: str = 'ransac', inlier_px: float = 25.0, allow_scale: bool = True,
                 debug_visual: bool = False):
    """
    Compares a dented image against a perfect reference image, focusing on a
    red laser line to detect and visualize defects.
    """
    start_time = time.time()
    try:
        img_perfect = cv2.imread(perfect_image_path)
        img_dented = cv2.imread(dented_image_path)
        if img_perfect is None or img_dented is None:
            print("Error: Could not load one or both images. Check file paths.")
            return
    except Exception as e:
        print(f"An error occurred while loading images: {e}")
        return

    print("Aligning images...")
    img_dented_aligned, _ = align_images(img_perfect, img_dented)
    print("Alignment complete.")

    mask_perfect, adjusted_perfect = get_laser_mask(img_perfect)
    mask_dented, adjusted_dented = get_laser_mask(img_dented_aligned)

    skeleton_perfect = (skeletonize(mask_perfect / 255) * 255).astype(np.uint8)
    skeleton_dented = (skeletonize(mask_dented / 255) * 255).astype(np.uint8)
    
    # Get the cleaned skeleton image AND the main contour from it
    cleaned_skeleton_perfect, contour_p = clean_skeleton(skeleton_perfect)
    cleaned_skeleton_dented, contour_d = clean_skeleton(skeleton_dented)

    final_warped_contour_d = contour_d # Initialize with original

    if contour_p is not None and contour_d is not None:
        # Try global rigid alignment using ICP on the contour point clouds.
        try:
            # Convert contours to Nx2 arrays
            pts_p = contour_p.reshape(-1, 2).astype(float)
            pts_d = contour_d.reshape(-1, 2).astype(float)

            # Resample to at most 800 points each for speed
            def _subsample(pts, max_n=800):
                n = pts.shape[0]
                if n <= max_n:
                    return pts
                idx = np.linspace(0, n - 1, max_n).astype(int)
                return pts[idx]

            pts_p_s = _subsample(pts_p, max_n=600)
            pts_d_s = _subsample(pts_d, max_n=600)

            # Decide which alignment strategy to use based on caller options
            try:
                if align_mode == 'piecewise':
                    raise RuntimeError('Forced piecewise by align_mode')

                # Try RANSAC first if requested
                if align_mode in ('ransac', 'auto'):
                    T_ransac, err_ransac, inliers = ransac_global_fit(pts_d_s, pts_p_s,
                                                                     n_iter=300, inlier_threshold=float(inlier_px),
                                                                     allow_scale=allow_scale, min_inliers=30)
                    if inliers.sum() >= 20 and err_ransac < max(20.0, float(inlier_px)):
                        R = T_ransac[0:2, 0:2]
                        t = T_ransac[0:2, 2]
                        full_d = (R @ pts_d.T).T + t
                        final_warped_contour_d = np.round(full_d).astype(np.int32).reshape(-1, 1, 2)
                        print(f"Applied RANSAC+similarity global fit (err={err_ransac:.2f}, inliers={inliers.sum()}).")
                        ransac_used = True
                    else:
                        ransac_used = False
                else:
                    ransac_used = False

                # If RANSAC didn't produce a good model, try ICP unless piecewise requested
                if not ransac_used and align_mode != 'piecewise':
                    transformed_d_s, T_icp = icp_rigid(pts_d_s, pts_p_s, max_iter=80, tol=1e-3,
                                                        outlier_threshold=max(15.0, float(inlier_px)), use_kdtree=True, allow_scale=allow_scale)
                    R = T_icp[0:2, 0:2]
                    t = T_icp[0:2, 2]
                    full_d = (R @ pts_d.T).T + t
                    final_warped_contour_d = np.round(full_d).astype(np.int32).reshape(-1, 1, 2)
                    print("Applied ICP (with optional scale) to dented profile.")
            except Exception as e:
                print(f"ICP/RANSAC alignment failed or forced piecewise ({e}), falling back to piecewise warp.")
                # Fallback to previous piecewise anchor-based warp
                top_p, bottom_p = segment_profile(contour_p)
                top_d, bottom_d = segment_profile(contour_d)

                if all(seg is not None for seg in [top_p, bottom_p, top_d, bottom_d]):
                    # Calculate translation for the top anchor
                    M_p_top = cv2.moments(top_p)
                    M_d_top = cv2.moments(top_d)
                    if M_p_top["m00"] != 0 and M_d_top["m00"] != 0:
                        cX_p_top = M_p_top["m10"] / M_p_top["m00"]
                        cY_p_top = M_p_top["m01"] / M_p_top["m00"]
                        cX_d_top = M_d_top["m10"] / M_d_top["m00"]
                        cY_d_top = M_d_top["m01"] / M_d_top["m00"]
                        dx_top = cX_p_top - cX_d_top
                        dy_top = cY_p_top - cY_d_top
                    else:
                        dx_top, dy_top = 0, 0

                    # Calculate translation for the bottom anchor
                    M_p_bottom = cv2.moments(bottom_p)
                    M_d_bottom = cv2.moments(bottom_d)
                    if M_p_bottom["m00"] != 0 and M_d_bottom["m00"] != 0:
                        cX_p_bottom = M_p_bottom["m10"] / M_p_bottom["m00"]
                        cY_p_bottom = M_p_bottom["m01"] / M_p_bottom["m00"]
                        cX_d_bottom = M_d_bottom["m10"] / M_d_bottom["m00"]
                        cY_d_bottom = M_d_bottom["m01"] / M_d_bottom["m00"]
                        dx_bottom = cX_p_bottom - cX_d_bottom
                        dy_bottom = cY_p_bottom - cY_d_bottom
                    else:
                        dx_bottom, dy_bottom = 0, 0
                    
                    # --- Apply Interpolated Warp (Rubber Sheeting) ---
                    warped_points = []
                    num_points = len(contour_d)
                    if num_points == 0: num_points = 1 # Avoid division by zero

                    for i, point in enumerate(contour_d):
                        x, y = point[0]
                        # Calculate the weight. Weight is 1 at the top, 0 at the bottom.
                        weight = (num_points - 1 - i) / (num_points - 1) if num_points > 1 else 1.0

                        # Interpolate the translation
                        dx = (weight * dx_top) + ((1 - weight) * dx_bottom)
                        dy = (weight * dy_top) + ((1 - weight) * dy_bottom)
                        
                        warped_points.append([x + dx, y + dy])
                    
                    final_warped_contour_d = np.array(warped_points, dtype=np.int32).reshape(-1, 1, 2)
                    print("Applied piecewise warp to the dented profile (fallback).")
                else:
                    print("Warning: Could not create anchor segments for piecewise alignment (fallback failed).")
        except Exception as e:
            print(f"ICP alignment failed ({e}), falling back to piecewise warp.")
            # Fallback to previous piecewise anchor-based warp
            top_p, bottom_p = segment_profile(contour_p)
            top_d, bottom_d = segment_profile(contour_d)

            if all(seg is not None for seg in [top_p, bottom_p, top_d, bottom_d]):
                # Calculate translation for the top anchor
                M_p_top = cv2.moments(top_p)
                M_d_top = cv2.moments(top_d)
                if M_p_top["m00"] != 0 and M_d_top["m00"] != 0:
                    cX_p_top = M_p_top["m10"] / M_p_top["m00"]
                    cY_p_top = M_p_top["m01"] / M_p_top["m00"]
                    cX_d_top = M_d_top["m10"] / M_d_top["m00"]
                    cY_d_top = M_d_top["m01"] / M_d_top["m00"]
                    dx_top = cX_p_top - cX_d_top
                    dy_top = cY_p_top - cY_d_top
                else:
                    dx_top, dy_top = 0, 0

                # Calculate translation for the bottom anchor
                M_p_bottom = cv2.moments(bottom_p)
                M_d_bottom = cv2.moments(bottom_d)
                if M_p_bottom["m00"] != 0 and M_d_bottom["m00"] != 0:
                    cX_p_bottom = M_p_bottom["m10"] / M_p_bottom["m00"]
                    cY_p_bottom = M_p_bottom["m01"] / M_p_bottom["m00"]
                    cX_d_bottom = M_d_bottom["m10"] / M_d_bottom["m00"]
                    cY_d_bottom = M_d_bottom["m01"] / M_d_bottom["m00"]
                    dx_bottom = cX_p_bottom - cX_d_bottom
                    dy_bottom = cY_p_bottom - cY_d_bottom
                else:
                    dx_bottom, dy_bottom = 0, 0
                
                # --- Apply Interpolated Warp (Rubber Sheeting) ---
                warped_points = []
                num_points = len(contour_d)
                if num_points == 0: num_points = 1 # Avoid division by zero

                for i, point in enumerate(contour_d):
                    x, y = point[0]
                    # Calculate the weight. Weight is 1 at the top, 0 at the bottom.
                    weight = (num_points - 1 - i) / (num_points - 1) if num_points > 1 else 1.0

                    # Interpolate the translation
                    dx = (weight * dx_top) + ((1 - weight) * dx_bottom)
                    dy = (weight * dy_top) + ((1 - weight) * dy_bottom)
                    
                    warped_points.append([x + dx, y + dy])
                
                final_warped_contour_d = np.array(warped_points, dtype=np.int32).reshape(-1, 1, 2)
                print("Applied piecewise warp to the dented profile (fallback).")
            else:
                print("Warning: Could not create anchor segments for piecewise alignment (fallback failed).")

    # --- Create Final Visualization ---
    final_aligned_skeleton_dented = np.zeros_like(cleaned_skeleton_dented)
    if final_warped_contour_d is not None:
        cv2.drawContours(final_aligned_skeleton_dented, [final_warped_contour_d], -1, 255, 1)

    dilate_kernel = np.ones((3, 3), np.uint8)
    thick_skeleton_perfect = cv2.dilate(cleaned_skeleton_perfect, dilate_kernel)
    thick_skeleton_dented = cv2.dilate(final_aligned_skeleton_dented, dilate_kernel)

    # Prepare data for clean plot (prefer contours if available)
    def _contour_xy(contour):
        if contour is None:
            return None, None
        arr = contour.reshape(-1, 2)
        return arr[:, 0], arr[:, 1]

    xp, yp = _contour_xy(contour_p)
    xd, yd = _contour_xy(final_warped_contour_d)

    # Fallback to skeleton pixel coordinates if contours unavailable
    if xp is None or yp is None:
        yy, xx = np.where(thick_skeleton_perfect > 0)
        xp, yp = xx, yy
    if xd is None or yd is None:
        yy, xx = np.where(thick_skeleton_dented > 0)
        xd, yd = xx, yy

    # Build a clean matplotlib figure similar to the expected example
    fig = plt.figure(figsize=(3.2, 5.6), dpi=150)  # Tall figure
    ax = fig.add_subplot(111)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    # Plot lines; invert y to match image coordinates (origin at top-left)
    ax.plot(xp, yp, color='blue', linewidth=1.5)
    ax.plot(xd, yd, color='red', linewidth=1.5)

    # Compute tight bounds with small margins
    all_x = np.concatenate([np.array(xp).ravel(), np.array(xd).ravel()])
    all_y = np.concatenate([np.array(yp).ravel(), np.array(yd).ravel()])
    if all_x.size > 0 and all_y.size > 0:
        min_x, max_x = float(np.min(all_x)), float(np.max(all_x))
        min_y, max_y = float(np.min(all_y)), float(np.max(all_y))
        mx = max(1.0, (max_x - min_x) * 0.05)
        my = max(1.0, (max_y - min_y) * 0.05)
        ax.set_xlim(min_x - mx, max_x + mx)
        # invert y-axis to keep visual orientation
        ax.set_ylim(max_y + my, min_y - my)

    ax.set_title('Clean Profile Comparison\n(Blue=Perfect, Red=Dented)', fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()
    # If debug visualization requested, overlay inliers/outliers on the adjusted perfect image
    if debug_visual:
        try:
            # Build matched pairs: map transformed dented points -> nearest perfect points
            pts_p_all = np.column_stack([xp, yp])
            pts_d_all = np.column_stack([xd, yd])
            if pts_p_all.size > 0 and pts_d_all.size > 0:
                if KDTree is not None:
                    tree = KDTree(pts_p_all)
                    dists, idxs = tree.query(pts_d_all, k=1)
                else:
                    dists_full = np.sqrt(((pts_d_all[:, None, :] - pts_p_all[None, :, :]) ** 2).sum(axis=2))
                    idxs = dists_full.argmin(axis=1)
                    dists = dists_full[np.arange(dists_full.shape[0]), idxs]

                inlier_mask = dists <= float(inlier_px)

                # Create a debug figure showing the original adjusted perfect image as background
                dbg_fig = plt.figure(figsize=(6, 6), dpi=150)
                dbg_ax = dbg_fig.add_subplot(111)
                dbg_ax.imshow(cv2.cvtColor(adjusted_perfect, cv2.COLOR_BGR2RGB))
                dbg_ax.set_title('Debug: matches (green=inliers, orange=outliers)')
                dbg_ax.axis('off')

                # Plot perfect & transformed dented contours
                dbg_ax.plot(pts_p_all[:, 0], pts_p_all[:, 1], color='blue', linewidth=1.2, label='perfect')
                dbg_ax.plot(pts_d_all[:, 0], pts_d_all[:, 1], color='red', linewidth=1.2, label='dented_transformed')

                # Draw lines for matched pairs (inliers green, outliers orange)
                for i, (p_idx, dist) in enumerate(zip(idxs, dists)):
                    p = pts_p_all[p_idx]
                    dpt = pts_d_all[i]
                    if inlier_mask[i]:
                        dbg_ax.plot([p[0], dpt[0]], [p[1], dpt[1]], color='lime', linewidth=0.6, alpha=0.7)
                    else:
                        dbg_ax.plot([p[0], dpt[0]], [p[1], dpt[1]], color='orange', linewidth=0.6, alpha=0.6)

                dbg_fig.tight_layout()
                dbg_out = str(Path(output_path).with_name('profile_comparison_debug.jpg'))
                dbg_fig.savefig(dbg_out, bbox_inches='tight', pad_inches=0.2)
                plt.close(dbg_fig)
                # Save debug as the main output so the server's /result returns the debug image when requested
                fig.savefig(output_path, bbox_inches='tight', pad_inches=0.4)
                print(f"Saved debug overlay '{dbg_out}' and output '{output_path}'.")
            else:
                # fallback to the standard plot if we can't compute matches
                fig.savefig(output_path, bbox_inches='tight', pad_inches=0.4)
        except Exception as e:
            print(f"Debug overlay failed: {e}. Saving standard output.")
            fig.savefig(output_path, bbox_inches='tight', pad_inches=0.4)
    else:
        fig.savefig(output_path, bbox_inches='tight', pad_inches=0.4)
    plt.close(fig)
    print(f"Saved clean plot '{output_path}'.")
    
    end_time = time.time()
    processing_time = end_time - start_time
    print(f"\nTotal processing time: {processing_time:.2f} seconds")

    # --- Deviation metrics ---
    def _resample_polyline(x, y, n=200):
        x = np.asarray(x, dtype=float).reshape(-1)
        y = np.asarray(y, dtype=float).reshape(-1)
        if x.size < 2:
            return x, y, 0.0
        ds = np.hypot(np.diff(x), np.diff(y))
        s = np.concatenate([[0.0], np.cumsum(ds)])
        total_len = float(s[-1]) if s.size > 0 else 0.0
        if total_len == 0.0:
            return x, y, 0.0
        s_new = np.linspace(0.0, total_len, n)
        xr = np.interp(s_new, s, x)
        yr = np.interp(s_new, s, y)
        return xr, yr, total_len

    metrics = None
    try:
        xr_p, yr_p, len_p = _resample_polyline(xp, yp, n=300)
        xr_d, yr_d, len_d = _resample_polyline(xd, yd, n=300)
        n = min(len(xr_p), len(xr_d))
        if n > 1:
            xr_p = xr_p[:n]; yr_p = yr_p[:n]
            xr_d = xr_d[:n]; yr_d = yr_d[:n]
            deviations = np.hypot(xr_p - xr_d, yr_p - yr_d)
            if deviations.size > 0:
                max_dev = float(np.max(deviations))
                mean_dev = float(np.mean(np.abs(deviations)))
                rms_dev = float(np.sqrt(np.mean(deviations ** 2)))
                p95_dev = float(np.percentile(deviations, 95))
                idx_max = int(np.argmax(deviations))
                metrics = {
                    'max_deviation_px': round(max_dev, 2),
                    'mean_deviation_px': round(mean_dev, 2),
                    'rms_deviation_px': round(rms_dev, 2),
                    'p95_deviation_px': round(p95_dev, 2),
                    'total_profile_length_px': round(float(max(len_p, len_d)), 2),
                    'worst_point': {
                        'perfect_xy': [round(float(xr_p[idx_max]), 1), round(float(yr_p[idx_max]), 1)],
                        'dented_xy': [round(float(xr_d[idx_max]), 1), round(float(yr_d[idx_max]), 1)],
                        'index': idx_max,
                    }
                }
    except Exception as _:
        # Leave metrics as None on failure
        metrics = None


    if show_plot:
        fig = plt.figure(figsize=(18, 6))
        fig.suptitle(f"Analysis complete in {processing_time:.2f} seconds", fontsize=16)

        plt.subplot(1, 3, 1)
        plt.imshow(cv2.cvtColor(adjusted_perfect, cv2.COLOR_BGR2RGB))
        plt.title("Perfect Image (Exposure Adjusted)")
        plt.axis('off')
        plt.subplot(1, 3, 2)
        plt.imshow(cv2.cvtColor(adjusted_dented, cv2.COLOR_BGR2RGB))
        plt.title("Dented Image (Exposure Adjusted)")
        plt.axis('off')
        plt.subplot(1, 3, 3)
        plt.plot(xp, yp, color='blue', linewidth=1.2)
        plt.plot(xd, yd, color='red', linewidth=1.2)
        plt.gca().invert_yaxis()
        plt.xticks([]); plt.yticks([])
        for spine in plt.gca().spines.values():
            spine.set_visible(False)
        plt.title("Clean Profile Comparison\n(Blue=Perfect, Red=Dented)")
        plt.axis('off')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for suptitle
        plt.show()

    return output_path, processing_time, metrics

if __name__ == '__main__':
    perfect_image_file = "Perfect_Image.jpg"
    dented_image_file = "Dented_Image.jpg"
    
    analyze_dent(perfect_image_file, dented_image_file, show_plot=True, output_path="profile_comparison.jpg")

