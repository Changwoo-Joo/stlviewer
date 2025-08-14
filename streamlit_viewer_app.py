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
    return mins, maxs

def get_axis_length(stl_mesh: mesh.Mesh, axis: str) -> float:
    idx = "XYZ".index(axis.upper())
    mins, maxs = get_bbox(stl_mesh)
    return float(maxs[idx] - mins[idx])

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
    idx = "XYZ".index(axis.upper())
    mins, maxs = get_bbox(stl_mesh)
    cur_len = float(maxs[idx] - mins[idx])
    if cur_len == 0:
        return stl_mesh
    s = float(target_length) / cur_len
    stl_mesh.vectors *= s
    return stl_mesh

# ---------- Rendering (Full, Orthographic fit) ----------
def render_mesh(stl_mesh: mesh.Mesh, height: int = 920):
    """
    Full 품질 + '화면 맞춤' 초기 뷰:
    - 직교(orthographic) 프로젝션으로 원근 왜곡 제거 → 찌그러짐 방지
    - 바운딩박스 기반 축 범위에 10% 패딩 → 처음부터 꽉 차게
    - 면은 거의 불투명 + 얇은 에지 오버레이로 경계 가독성 확보
    """
    V = stl_mesh.vectors  # (n, 3, 3)
    n_tri = V.shape[0]

    flat = V.reshape(-1, 3)
    x, y, z = flat[:, 0], flat[:, 1], flat[:, 2]
    base = np.arange(0, n_tri * 3, 3, dtype=np.int32)
    I, J, K = base, base + 1, base + 2

    mins, maxs = flat.min(axis=0), flat.max(axis=0)
    lengths = maxs - mins
    pads = np.maximum(lengths * 0.10, 1e-6)  # 최소 패딩
    ranges = np.stack([mins - pads, maxs + pads], axis=1)

    title_text = (
        f"X: {mins[0]:.2f} ~ {maxs[0]:.2f} ({lengths[0]:.2f}mm), "
        f"Y: {mins[1]:.2f} ~ {maxs[1]:.2f} ({lengths[1]:.2f}mm), "
        f"Z: {mins[2]:.2f} ~ {maxs[2]:.2f} ({lengths[2]:.2f}mm)"
    )

    # 본체(면)
    mesh3d = go.Mesh3d(
        x=x, y=y, z=z, i=I, j=J, k=K,
        color="lightblue",
        opacity=0.95,           # 경계 잘 보이도록 거의 불투명
        flatshading=False,
        lighting=dict(ambient=0.7, diffuse=0.85, specular=0.15, roughness=0.7),
        lightposition=dict(x=0.8, y=0.8, z=1.6),
        hoverinfo="skip",
        name="STL",
        showscale=False,
    )

    # 에지(윤곽선) — 낮은 불투명도
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
        opacity=0.18,
        hoverinfo="skip",
        showlegend=False,
        name="Edges",
    )

    fig = go.Figure(data=[mesh3d, edge_trace])

    # 직교 투영 + 축 범위 고정(패딩 포함) + 데이터 비율 유지
    fig.update_layout(
        title=dict(text=title_text, x=0.5, xanchor="center"),
        scene=dict(
            aspectmode="data",
            xaxis=dict(range=ranges[0].tolist(), zeroline=False, showspikes=False),
            yaxis=dict(range=ranges[1].tolist(), zeroline=False, showspikes=False),
            zaxis=dict(range=ranges[2].tolist(), zeroline=False, showspikes=False),
            camera=dict(
                projection=dict(type="orthographic"),
                eye=dict(x=1.8, y=1.8, z=1.4),  # 보기 편한 기본 각도
            ),
        ),
        margin=dict(l=0, r=0, t=36, b=0),
        showlegend=False,
        height=height,
    )
    return fig
