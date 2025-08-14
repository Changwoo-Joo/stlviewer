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


# ---------- Rotation ----------
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
    ax_deg: float,
    ay_deg: float,
    az_deg: float,
    dx: float,
    dy: float,
    dz: float,
    pivot: str = "origin",   # "origin" | "centroid"
) -> mesh.Mesh:
    """X→Y→Z 순서 회전 후 평행이동. pivot 기준 회전."""
    V = stl_mesh.vectors.reshape(-1, 3)

    p = np.zeros(3, dtype=float) if pivot == "origin" else get_centroid(stl_mesh)

    V -= p
    if ax_deg:
        V[:] = V @ _rot_matrix("X", ax_deg).T
    if ay_deg:
        V[:] = V @ _rot_matrix("Y", ay_deg).T
    if az_deg:
        V[:] = V @ _rot_matrix("Z", az_deg).T
    V += p
    V += np.array([dx, dy, dz], dtype=float)

    stl_mesh.vectors[:] = V.reshape(-1, 3, 3)
    return stl_mesh


def apply_scale_axis_uniform(stl_mesh: mesh.Mesh, axis: str, target_length: float) -> mesh.Mesh:
    """선택 축 길이를 target_length로 맞추는 균등 스케일(XYZ 동일배율, 원점 기준)."""
    idx = "XYZ".index(axis.upper())
    mins, maxs = get_bbox(stl_mesh)
    cur_len = float(maxs[idx] - mins[idx])
    if cur_len == 0:
        return stl_mesh
    s = float(target_length) / cur_len
    stl_mesh.vectors *= s
    return stl_mesh


# ---------- Rendering (Solid) ----------
def render_mesh(stl_mesh: mesh.Mesh, max_tris: int | None = None, show_edges: bool = False, height: int = 880):
    """
    고속 + 매끈한 면 렌더:
    - opacity=1.0, flatshading=False → 면이 꽉 찬 실체처럼
    - show_edges=False 기본 (윤곽선 비활성화)
    """
    V = stl_mesh.vectors  # (n, 3, 3)
    n_tri = V.shape[0]

    # 다운샘플링(프리뷰 전용)
    if (max_tris is not None) and (n_tri > max_tris) and (max_tris > 0):
        stride = int(np.ceil(n_tri / max_tris))
        V = V[::stride]
        n_tri = V.shape[0]

    flat = V.reshape(-1, 3)
    x, y, z = flat[:, 0], flat[:, 1], flat[:, 2]

    base = np.arange(0, n_tri * 3, 3, dtype=np.int32)
    I, J, K = base, base + 1, base + 2

    mins, maxs = flat.min(axis=0), flat.max(axis=0)
    title_text = (
        f"X: {mins[0]:.2f} ~ {maxs[0]:.2f} ({maxs[0]-mins[0]:.2f}mm), "
        f"Y: {mins[1]:.2f} ~ {maxs[1]:.2f} ({maxs[1]-mins[1]:.2f}mm), "
        f"Z: {mins[2]:.2f} ~ {maxs[2]:.2f} ({maxs[2]-mins[2]:.2f}mm)"
    )

    mesh3d = go.Mesh3d(
        x=x, y=y, z=z, i=I, j=J, k=K,
        opacity=1.0,                # 실체감
        color="lightblue",
        flatshading=False,          # 매끈한 면
        lighting=dict(ambient=0.8, diffuse=0.9, specular=0.2, roughness=0.8),
        lightposition=dict(x=0.5, y=0.5, z=1.5),
        name="STL",
        showscale=False,
    )

    data = [mesh3d]

    # 기본값은 False: 라인 오버레이 비활성화(점박이 현상 방지)
    if show_edges:
        e = V.reshape(-1, 3, 3)
        edges = np.concatenate([
            e[:, [0, 1], :], np.full((e.shape[0], 1, 3), np.nan),
            e[:, [1, 2], :], np.full((e.shape[0], 1, 3), np.nan),
            e[:, [2, 0], :], np.full((e.shape[0], 1, 3), np.nan),
        ], axis=1).reshape(-1, 3)
        edge_trace = go.Scatter3d(
            x=edges[:, 0], y=edges[:, 1], z=edges[:, 2],
            mode="lines",
            line=dict(width=1),
            opacity=0.8,
            hoverinfo="skip",
            showlegend=False,
            name="Edges",
        )
        data.append(edge_trace)

    fig = go.Figure(data=data)
    fig.update_layout(
        title=dict(text=title_text, x=0.5, xanchor="center"),
        scene=dict(aspectmode="data"),
        margin=dict(l=0, r=0, t=36, b=0),
        showlegend=False,
        height=height,
    )
    return fig
