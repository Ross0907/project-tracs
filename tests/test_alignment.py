import numpy as np
from image_processing import _compute_rigid_transform, _compute_similarity_transform, icp_rigid, ransac_global_fit


def make_ellipse(n=200, noise=0.0):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    a, b = 100.0, 40.0
    x = a * np.cos(t)
    y = b * np.sin(t)
    pts = np.vstack([x, y]).T
    pts += np.random.normal(scale=noise, size=pts.shape)
    return pts


def apply_sim_transform(pts, angle_deg=10.0, scale=1.05, tx=5.0, ty=-8.0):
    theta = np.deg2rad(angle_deg)
    c, s = np.cos(theta), np.sin(theta)
    R = np.array([[c, -s], [s, c]])
    transformed = scale * (R @ pts.T).T + np.array([tx, ty])
    return transformed


def test_similarity_estimation():
    pts = make_ellipse(300, noise=0.5)
    dst = apply_sim_transform(pts, angle_deg=12.3, scale=1.12, tx=7.2, ty=-3.7)
    T, err = _compute_similarity_transform(pts, dst)
    # Transform pts
    R = T[0:2, 0:2]
    t = T[0:2, 2]
    pts_t = (R @ pts.T).T + t
    mean_err = np.mean(np.linalg.norm(pts_t - dst, axis=1))
    assert mean_err < 1.5


def test_ransac_and_icp():
    pts = make_ellipse(500, noise=0.8)
    dst = apply_sim_transform(pts, angle_deg=5.0, scale=1.03, tx=10.0, ty=-6.0)
    # add outliers to dst
    idx = np.random.choice(dst.shape[0], size=50, replace=False)
    dst[idx] += np.random.normal(scale=50.0, size=(50, 2))

    # Create initial correspondences by simple nearest (simulate matching)
    T_r, err_r, inliers = ransac_global_fit(pts, dst, n_iter=300, inlier_threshold=8.0, allow_scale=True, min_inliers=40)
    assert inliers.sum() >= 200 or err_r < 5.0

    # ICP refinement
    transformed, T_icp = icp_rigid(pts, dst, max_iter=80, outlier_threshold=12.0, use_kdtree=True, allow_scale=True)
    # After ICP, transformed should be close to dst for many points
    # Build nearest neighbors to estimate error
    from scipy.spatial import cKDTree
    tree = cKDTree(dst)
    dists, _ = tree.query(transformed, k=1)
    assert np.median(dists) < 6.0
