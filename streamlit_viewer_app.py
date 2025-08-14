# streamlit_viewer_app.py
import streamlit as st
from stl_backend import (
    load_stl,
    save_stl_bytes,
    render_mesh,
    get_axis_length,
    apply_transform_xyz,
    apply_scale_axis_uniform,
)

st.set_page_config(page_title="STL Viewer & Transformer", layout="wide")
st.title("STL Viewer & Transformer (Streamlit Cloud Ver.)")

# ---- 세션 상태 ----
if "mesh" not in st.session_state:
    st.session_state.mesh = None
if "updated" not in st.session_state:
    st.session_state.updated = False
if "last_fig" not in st.session_state:
    st.session_state.last_fig = None
if "angles" not in st.session_state:
    st.session_state.angles = {"X": 0.0, "Y": 0.0, "Z": 0.0}
if "shift" not in st.session_state:
    st.session_state.shift = [0.0, 0.0, 0.0]
if "pivot_sel" not in st.session_state:
    st.session_state.pivot_sel = "Origin"  # 기본 Origin
if "preview_quality" not in st.session_state:
    st.session_state.preview_quality = "Fast"  # 기본 품질 올림(형상 강조)
if "preview_height" not in st.session_state:
    st.session_state.preview_height = 880

# ---- 좌/우 레이아웃 (왼쪽 25% / 오른쪽 75%) ----
left, right = st.columns([0.25, 0.75], gap="large")

with left:
    uploaded = st.file_uploader("Upload STL file", type=["stl"])
    if uploaded is not None:
        st.session_state.mesh = load_stl(uploaded.read())
        st.session_state.updated = True
        st.session_state.angles = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        st.session_state.shift = [0.0, 0.0, 0.0]

    if st.session_state.mesh is not None:
        st.subheader("🌀 Transform (Rotation & Translation)")

        with st.expander("Rotation (degrees)", expanded=True):
            ax = st.number_input("X", value=float(st.session_state.angles["X"]), format="%.6f", key="ang_x")
            ay = st.number_input("Y", value=float(st.session_state.angles["Y"]), format="%.6f", key="ang_y")
            az = st.number_input("Z", value=float(st.session_state.angles["Z"]), format="%.6f", key="ang_z")
            pivot = st.radio(
                "Pivot(회전 기준점)", ["Model centroid", "Origin"],
                horizontal=True, index=1, key="pivot_sel"
            )

        with st.expander("Shift (mm)", expanded=True):
            dx = st.number_input("Shift X", value=float(st.session_state.shift[0]), format="%.6f", key="sh_x")
            dy = st.number_input("Shift Y", value=float(st.session_state.shift[1]), format="%.6f", key="sh_y")
            dz = st.number_input("Shift Z", value=float(st.session_state.shift[2]), format="%.6f", key="sh_z")

        if st.button("Apply Transform"):
            dax = float(ax) - st.session_state.angles["X"]
            day = float(ay) - st.session_state.angles["Y"]
            daz = float(az) - st.session_state.angles["Z"]
            ddx = float(dx) - st.session_state.shift[0]
            ddy = float(dy) - st.session_state.shift[1]
            ddz = float(dz) - st.session_state.shift[2]

            if any(abs(v) > 0 for v in [dax, day, daz, ddx, ddy, ddz]):
                st.session_state.mesh = apply_transform_xyz(
                    st.session_state.mesh,
                    ax_deg=dax, ay_deg=day, az_deg=daz,
                    dx=ddx, dy=ddy, dz=ddz,
                    pivot=("origin" if pivot == "Origin" else "centroid"),
                )
                st.session_state.angles = {"X": float(ax), "Y": float(ay), "Z": float(az)}
                st.session_state.shift = [float(dx), float(dy), float(dz)]
                st.session_state.updated = True

        st.subheader("📏 Axis-Based Scale")
        scale_axis = st.selectbox("Scale 기준 축", ["X", "Y", "Z"], key="scale_axis")
        curr_len = get_axis_length(st.session_state.mesh, st.session_state.scale_axis)
        target_length = st.number_input(
            "해당 축의 최종 길이 (mm)",
            value=float(curr_len),
            key=f"target_length_{st.session_state.scale_axis}",
            format="%.6f",
            step=1.0,
        )

        if st.button("Apply Axis-Based Scaling"):
            st.session_state.mesh = apply_scale_axis_uniform(
                st.session_state.mesh, st.session_state.scale_axis, float(target_length)
            )
            st.session_state.updated = True

        st.subheader("⚡ Preview Quality")
        st.session_state.preview_quality = st.radio(
            "미리보기 품질(속도 ↔︎ 정확도)",
            ["Ultra Fast", "Fast", "Full"],
            index=1,  # 기본 Fast
            horizontal=True,
        )

        st.download_button(
            "📥 Download Transformed STL",
            data=save_stl_bytes(st.session_state.mesh),
            file_name="transformed.stl",
            mime="application/sla",
        )

with right:
    if st.session_state.mesh is not None:
        st.subheader("📊 Preview")

        # 품질 → 최대 삼각형 수/에지 표시 맵
        quality_map = {
            "Ultra Fast": {"max_tris": 20000, "show_edges": False},
            "Fast":       {"max_tris": 60000, "show_edges": False},
            "Full":       {"max_tris": None,  "show_edges": True},  # Full에서만 윤곽선
        }
        q = quality_map[st.session_state.preview_quality]
        max_tris = q["max_tris"]
        show_edges = q["show_edges"]

        # 항상 최신 품질 반영(속도 충분)
        fig = render_mesh(
            st.session_state.mesh,
            max_tris=max_tris,
            show_edges=show_edges,
            height=st.session_state.preview_height,
        )
        st.session_state.last_fig = fig
        st.plotly_chart(fig, use_container_width=True)
