def render_mesh(stl_mesh: mesh.Mesh, height: int = 880):
    """
    매끈한 기본 렌더(항상 Full 품질) + 윤곽선 오버레이:
    - Mesh3d (부드러운 셰이딩)
    - 얇은 라인으로 에지 강조
    """
    V = stl_mesh.vectors  # (n, 3, 3)
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

    # 본체(면)
    mesh3d = go.Mesh3d(
        x=x, y=y, z=z, i=I, j=J, k=K,
        color="lightblue",
        opacity=0.5,            # 매끈하게 보이도록 반투명
        flatshading=False,      # 부드러운 셰이딩
        lighting=dict(ambient=1.0, diffuse=0.0, specular=0.0),
        hoverinfo="skip",
        name="STL",
        showscale=False,
    )

    data = [mesh3d]

    # ── 윤곽선(에지) 오버레이 ─────────────────────────────────────────────
    # 각 삼각형의 (v0->v1), (v1->v2), (v2->v0) 라인을 그리되,
    # 삼각형마다 NaN으로 분절해서 하나의 trace로 묶음 (빠름)
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
        opacity=0.25,           # 너무 세지 않게 살짝만
        hoverinfo="skip",
        showlegend=False,
        name="Edges",
    )
    data.append(edge_trace)
    # ─────────────────────────────────────────────────────────────────────

    fig = go.Figure(data=data)
    fig.update_layout(
        title=dict(text=title_text, x=0.5, xanchor="center"),
        scene=dict(aspectmode="data"),
        margin=dict(l=0, r=0, t=36, b=0),
        showlegend=False,
        height=height,
    )
    return fig
