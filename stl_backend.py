# stl_backend.py
import io
import os
import tempfile
import numpy as np
from stl import mesh
import plotly.graph_objects as go

# ---------- STL I/O ----------
def load_stl(file_bytes: bytes) -> mesh.Mesh:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tmp:
        tmp.write(file_bytes)
        tmp.flush()
        path = tmp.name
    try:
        m = mesh.Mesh.from_file(path)
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
    return m

def save_stl_bytes(stl_mesh: mesh.Mesh) -> io.BytesIO:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tmp:
        temp_path = tmp.name
    try:
        stl_mesh.save(temp_path)
        with open(temp_path, "rb") as f:
            data = f.read()
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass
    return io.BytesIO(data)

# ---------- Geometry ----------
def get_bbox(stl_mesh: mesh.Mesh):
    v = stl_mesh.vectors  # (n_tri, 3, 3)
    mins = np.min(v, axis=(0, 1))
    maxs = np.max(v, axis=(0, 1))
    return mins, maxs  # (xmin, ymin, zmin), (xmax, ymax, zmax)

def get_axis_length(stl_mesh: mesh.Mesh, axis: str) -> float:
    idx = "XYZ".index(axis.upper())
    mins, maxs = get_bbox(stl_mesh)
    return float(maxs[idx] - mins[idx])

def get_axis_lengths(stl_mesh: mesh.Mesh):
    """X/Y/Z 각 축 길이를 튜플로 반환 (lenX, lenY, lenZ)."""
    mins, maxs = get_bbox(stl_mesh)
    lengths = maxs - mins
    return float(lengths[0]), float(lengths[1]), float(lengths[2])

def get_centroid(stl_mesh: mesh.Mesh) -> np.ndarray:
    return np.mean(stl_mesh.vectors.reshape(-1, 3), axis=0)

# ---------- Transforms ----------
def _rot_matrix(axis: str, angle_deg: float) -> np.ndarray:
    a = axis.upper()
    t = np.deg2rad(angle_deg)
    c, s = np.cos(t), np.sin(t)
    if a == "X":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)
    if a == "Y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)
    if a == "Z":
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)
    return np.eye(3, dtype=float)

def apply_transform_xyz(
    stl_mesh: mesh.Mesh,
    ax_deg: float, ay_deg: float, az_deg: float,
    dx: float, dy: float, dz: float,
    pivot: str = "origin",   # "origin" | "centroid"
) -> mesh.Mesh:
    """X→Y→Z 순으로 회전 후 평행이동. pivot 기준 회전."""
    V = stl_mesh.vectors.reshape(-1, 3)
    p = np.zeros(3, dtype=float) if pivot == "origin" else get_centroid(stl_mesh)

    V -= p
    if ax_deg: V[:] = V @ _rot_matrix("X", ax_deg).T
    if ay_deg: V[:] = V @ _rot_matrix("Y", ay_deg).T
    if az_deg: V[:] = V @ _rot_matrix("Z", az_deg).T
    V += p
    V += np.array([dx, dy, dz], dtype=float)

    stl_mesh.vectors[:] = V.reshape(-1, 3, 3)
    return stl_mesh

def apply_scale_axis_uniform(stl_mesh: mesh.Mesh, axis: str, target_length: float) -> mesh.Mesh:
    """선택 축 길이를 target_length로 맞추는 균등 스케일(XYZ 동일 배율, 원점 기준)."""
    idx = "XYZ".index(axis.upper())
    mins, maxs = get_bbox(stl_mesh)
    cur_len = float(maxs[idx] - mins[idx])
    if
