# stl_backend.py
import io
import os
import tempfile
import numpy as np
from stl import mesh
import plotly.graph_objects as go


# ---------- STL I/O ----------
def load_stl(file_bytes: bytes) -> mesh.Mesh:
    """
    numpy-stl은 파일 경로 로드를 선호하므로 임시파일을 경유한다.
    """
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
    """
    mesh.save()는 파일경로가 필요하므로 임시파일에 저장 후 BytesIO로 반환.
    """
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
    axis_idx = "XYZ".index(axis.upper())
    mins, maxs = get_bbox(stl_mesh)
    return float(maxs[axis_idx] - mins[axis_idx])


# ---------- Transforms ----------
def apply_transform(
    stl_mesh: mesh.Mesh,
    axis: str,
    angle_deg: float,
    dx: float,
    dy: float,
    dz: float,
) -> mesh.Mesh:
    """
    원점 기준 회전 후 평행이동을 적용.
    """
    ax = axis.upper()
    angle_rad = np.deg2rad(angle_deg)

    if ax == "X":
        R = np.array(
            [
                [1, 0, 0],
                [0, np.cos(angle_rad), -np.sin(angle_rad)],
                [0, np.sin(angle_rad), np.cos(angle_rad)],
            ],
            dtype=float,
        )
    elif ax == "Y":
        R = np.array(
            [
                [np.cos(angle_rad), 0, np.sin(angle_rad)],
                [0, 1, 0],
                [-np.sin(angle_rad), 0, np.cos(angle_rad)],
            ],
            dtype=float,
        )
    elif ax == "Z":
        R = np.array(
            [
                [np.cos(angle_rad), -np.sin(angle_rad), 0],
                [np.sin(angle_rad), np.cos(angle_rad), 0],
                [0, 0, 1],
            ],
            dtype=float,
        )
    else:
        R = np.eye(3, dtype=float)

    # 회전
    stl_mesh.vectors[:] = np.einsum("...ij,jk->...ik", stl_mesh.vectors, R.T)

    # 평행이동
    stl_mesh.x += dx
    stl_mesh.y += dy
    stl_mesh.z += dz
    return stl_mesh


def apply_scale(stl_mesh: mesh.Mesh, axis: str, target_length: float) -> mesh.Mesh:
    """
    선택 축의 현재 길이를 target_length로 맞추는 '균등 스케일'(XYZ 동일 배율, 원점 기준).
    """
    axis_idx = "XYZ".index(axis.upper())
    mins, maxs = get_bbox(stl_mesh)
    cur_len = float(maxs[axis_idx] - mins[axis_idx])
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
            x.append(vtx[0])
            y.append(vtx[1])
            z.append(vtx[2])
        I.append(idx)
        J.append(idx + 1)
        K.append(idx + 2)
        idx += 3

    xmin, xmax = np.min(x), np.max(x)
    ymin, ymax = np.min(y), np.max(y)
    zmin, zmax = np.min(z), np.max(z)

    xlen = xmax - xmin
    ylen = ymax - ymin
    zlen = zmax - zmin

    title_text = (
        f"X: {xmin:.2f} ~ {xmax:.2f} ({xlen:.2f}mm), "
        f"Y: {ymin:.2f} ~ {ymax:.2f} ({ylen:.2f}mm), "
        f"Z: {zmin:.2f} ~ {zmax:.2f} ({zlen:.2f}mm)"
    )

    mesh3d = go.Mesh3d(
        x=x,
        y=y,
        z=z,
        i=I,
        j=J,
        k=K,
        color="lightblue",
        opacity=0.5,
        name="STL Model",
    )

    fig = go.Figure(data=[mesh3d])
    fig.update_layout(
        title=dict(text=title_text, x=0.5, xanchor="center"),
        scene=dict(aspectmode="data"),
        margin=dict(l=0, r=0, t=60, b=0),
    )
    return fig
