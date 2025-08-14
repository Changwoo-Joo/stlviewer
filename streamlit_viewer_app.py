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

uploaded = st.file_uploader("Upload STL file", type=["stl"])

# ---- 세션 상태 초기화 ----
if "mesh" not in st.session_state:
    st.session_state.mesh = None
if "updated" not in st.session_state:
    st.session_state.updated = False
if "last_fig" not in st.session_state:
    st.session_state.last_fig = None

# 회전/이동 표시 상태(절대값 UI)
if "angles" not in st.session_state:
    st.session_state.angles = {"X": 0.0, "Y": 0.0, "Z": 0.0}
if "shift" not in st.session_state:
    st.session_state.shift = [0.0, 0.0, 0.0]  # dx, dy, dz

# 업로드 처리
if uploaded is not None:
    st.session_state.mesh = load_stl(uploaded.read())
    st.session_state.updated = True
    st.session_state.angles = {"X": 0.0, "Y": 0.0, "Z": 0.0}
    st.session_state.shift = [0.0, 0.0, 0.0]

# ---- 변환 메뉴 ----
if st.session_state.mesh is not None:
    st.subheader("🌀 Transform (Rotation & Translation)")

    colL, colR = st.columns(2)
    with colL:
        st.markdown("**Rotation (degrees)** — 디자인 툴처럼 X/Y/Z에 각도 직접 입력")
        ax = st.number_input("X", value=float(st.session_state.angles["X"]), format="%.6f", key="ang_x")
        ay = st.number_input("Y", value=float(st.session_state.angles["Y"]), format="%.6f", key="ang_y")
        az = st.number_input("Z", value=float(st.session_state.angles["Z"]), format="%.6f", key="ang_z")
        pivot = st.radio("Pivot(회전 기준점)", ["Model centroid", "Origin"], horizontal=True)

    with colR:
        st.markdown("**Shift (mm)**")
        dx = st.number_input("Shift X", value=float(st.session_state.shift[0]), format="%.6f", key="sh_x")
        dy = st.number_input("Shift Y", value=float(st.session_state.shift[1]), format="%.6f", key="sh_y")
        dz = st.number_input("Shift Z", value=float(st.session_state.shift[2]), format="%.6f", key="sh_z")

    if st.button("Apply Transform"):
        # 이전 표시값과의 차이(델타)만 실제 메시에 적용 → 누적 회전/이동을 절대값처럼 다룸
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
                pivot=("centroid" if pivot == "Model centroid" else "origin"),
            )
            # 표시 상태 갱신
            st.session_state.angles = {"X": float(ax), "Y": float(ay), "Z": float(az)}
            st.session_state.shift = [float(dx), float(dy), float(dz)]
            st.session_state.updated = True

    # ---- Axis-Based Scale ----
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

    # ---- Preview ----
    st.subheader("📊 Preview")
    if st.session_state.updated:
        fig = render_mesh(st.session_state.mesh)
        st.session_state.last_fig = fig
        st.session_state.updated = False
    else:
        fig = st.session_state.last_fig

    if fig:
        st.plotly_chart(fig, use_container_width=True)

    # ---- Download ----
    st.download_button(
        "📥 Download Transformed STL",
        data=save_stl_bytes(st.session_state.mesh),
        file_name="transformed.stl",
        mime="application/sla",
    )
