import numpy as np
from image_processing import _compute_similarity_transform, icp_rigid, ransac_global_fit


def smoke():
    # Synthetic test: create a profile and apply sim transform + outliers
    t = np.linspace(0, 2*np.pi, 400, endpoint=False)
    pts = np.vstack([100*np.cos(t), 40*np.sin(t)]).T
    dst = _apply = (lambda p: p)(pts)
    dst = (1.02 * np.array([[np.cos(np.deg2rad(4)), -np.sin(np.deg2rad(4))],[np.sin(np.deg2rad(4)), np.cos(np.deg2rad(4))]] ) @ pts.T).T + np.array([6.0, -3.0])
    # add noise and outliers
    dst += np.random.normal(scale=0.6, size=dst.shape)
    dst[np.random.choice(dst.shape[0], 30, replace=False)] += np.random.normal(scale=40.0, size=(30,2))

    T_ransac, err_ransac, inliers = ransac_global_fit(pts, dst, n_iter=200, inlier_threshold=12.0, allow_scale=True, min_inliers=50)
    print('RANSAC err, inliers:', err_ransac, inliers.sum())
    transformed, T_icp = icp_rigid(pts, dst, max_iter=80, outlier_threshold=15.0, use_kdtree=True, allow_scale=True)
    print('ICP median dist:', np.median(np.linalg.norm(transformed - dst, axis=1)))

if __name__ == '__main__':
    smoke()
