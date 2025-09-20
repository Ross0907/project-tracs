import cv2
import numpy as np
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize
import time

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


def analyze_dent(perfect_image_path, dented_image_path, show_plot=True, output_path="profile_comparison.jpg"):
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
        # Get top and bottom anchor segments for alignment
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
                
            print(f"Top anchor translation: ({dx_top:.2f}, {dy_top:.2f})")
            print(f"Bottom anchor translation: ({dx_bottom:.2f}, {dy_bottom:.2f})")

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
            print("Applied piecewise warp to the dented profile.")
        else:
             print("Warning: Could not create anchor segments for piecewise alignment.")

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

