# stl_backend.py
import io
import os
import tempfile
import numpy as np

# numpy-stl
from stl import mesh
# 렌더용
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


# ---------- Geometry Utils ----------
def get_bbox(stl_mesh: mesh.Mesh):
    v = stl_mesh.vectors  # (n_tri, 3, 3)
    mins = np.min(v, axis=(0, 1))
    maxs = np.max(v, axis=(0, 1))
    return mins, maxs  # (xmin, ymin, zmin), (xmax, ymax, zmax)


def get_axis_length(stl_mesh: mesh.Mesh, axis: str) -> float:
    idx = "XYZ".index(axis.upper())
    mins, maxs = get_bbox(stl_mesh)
    return float(maxs[idx] - mins[idx])


def get_centroid(stl_mesh: mesh.Mesh) -> np.ndarray:
    return np.mean(stl_mesh.vectors.reshape(-1, 3), axis=0)


# ---------- Rotation Matrices ----------
def rot_matrix(axis: str, angle_deg: float) -> np.ndarray:
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


# ---------- Transforms ----------
def apply_transform_xyz(
    stl_mesh: mesh.Mesh,
    ax_deg: float,
    ay_deg: float,
    az_deg: float,
    dx: float,
    dy: float,
    dz: float,
    pivot: str = "centroid",   # "centroid" | "origin"
) -> mesh.Mesh:
    """X→Y→Z 순서로 회전 후 평행이동. pivot 기준 회전."""
    V = stl_mesh.vectors.reshape(-1, 3)

    if pivot == "centroid":
        p = get_centroid(stl_mesh)
    else:
        p = np.zeros(3, dtype=float)

    # pivot 이동 → 회전들 → 복귀
    V -= p
    if ax_deg != 0:
        V[:] = V @ rot_matrix("X", ax_deg).T
    if ay_deg != 0:
        V[:] = V @ rot_matrix("Y", ay_deg).T
    if az_deg != 0:
        V[:] = V @ rot_matrix("Z", az_deg).T
    V += p

    # 평행이동
    V += np.array([dx, dy, dz], dtype=float)

    stl_mesh.vectors[:] = V.reshape(-1, 3, 3)
    return stl_mesh


def apply_scale_axis_uniform(stl_mesh: mesh.Mesh, axis: str, target_length: float) -> mesh.Mesh:
    """
    선택 축의 길이를 target_length로 맞추는 '균등 스케일'(XYZ 모두 동일비율).
    pivot은 모델 원점(데이터 그대로) 기준.
    """
    idx = "XYZ".index(axis.upper())
    mins, maxs = get_bbox(stl_mesh)
    cur_len = float(maxs[idx] - mins[idx])
    if cur_len == 0:
        return stl_mesh
    s = float(target_length) / cur_len
    stl_mesh.vectors *= s
    return stl_mesh


# ---------- Rendering ----------
def render_mesh(stl_mesh: mesh.Mesh):
    x, y, z = [], [], []
    I, J, K = [], [], []
    idx = 0
    for tri in stl_mesh.vectors:
        for vtx in tri:
            x.append(vtx[0]); y.append(vtx[1]); z.append(vtx[2])
        I.append(idx); J.append(idx + 1); K.append(idx + 2)
        idx += 3

    xmin, xmax = np.min(x), np.max(x)
    ymin, ymax = np.min(y), np.max(y)
    zmin, zmax = np.min(z), np.max(z)

    title_text = (
        f"X: {xmin:.2f} ~ {xmax:.2f} ({xmax-xmin:.2f}mm), "
        f"Y: {ymin:.2f} ~ {ymax:.2f} ({ymax-ymin:.2f}mm), "
        f"Z: {zmin:.2f} ~ {zmax:.2f} ({zmax-zmin:.2f}mm)"
    )

    mesh3d = go.Mesh3d(
        x=x, y=y, z=z, i=I, j=J, k=K,
        color="lightblue", opacity=0.5, name="STL Model"
    )
    fig = go.Figure(data=[mesh3d])
    fig.update_layout(
        title=dict(text=title_text, x=0.5, xanchor="center"),
        scene=dict(aspectmode="data"),
        margin=dict(l=0, r=0, t=60, b=0),
    )
    return fig
