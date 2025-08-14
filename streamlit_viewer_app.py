# streamlit_viewer_app.py
import streamlit as st
from stl_backend import (
    load_stl, save_stl_bytes, render_mesh,
    get_axis_length, apply_transform_xyz, apply_scale_axis_uniform,
)

st.set_page_config(page_title="STL Viewer & Transformer", layout="wide")
st.title("STL Viewer & Transformer (Streamlit Cloud Ver.)")

# ---- Global CSS: 왼쪽 패널 전용 스크롤 ----
st.markdown("""
<style>
.left-scroll { max-height: 88vh; overflow-y: auto; padding-right: 10px; }
.block-container { padding-top: 0.6rem; }
</style>
""", unsafe_allow_html=True)

# ---- 세션 상태 ----
if "mesh" not in st.session_state: st.session_state.mesh = None
if "updated" not in st.session_state: st.session_state.updated = False
if "last_fig" not in st.session_state: st.session_state.last_fig = None
if "angles" not in st.session_state: st.session_state.angles = {"X": 0.0, "Y": 0.0, "Z": 0.0}
if "shift" not in st.session_state: st.session_state.shift = [0.0, 0.0, 0.0]
if "pivot_sel" not in st.session_state: st.session_state.pivot_sel = "Origin"  # 기본 Origin
if "preview_height" not in st.session_state: st.session_state.preview_height = 920

# ---- 헬퍼: 입력값 델타 적용 ----
def _apply_from_inputs(ax, ay, az, dx, dy, dz, pivot_label: str):
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
            pivot=("origin" if pivot_label == "Origin" else "centroid"),
        )
        st.session_state.angles = {"X": float(ax), "Y": float(ay), "Z": float(az)}
        st.session_state.shift = [float(dx), float(dy), float(dz)]
        st.session_state.updated = True

# ---- 좌/우 레이아웃 (왼쪽 25% / 오른쪽 75%) ----
left, right = st.columns([0.25, 0.75], gap="large")

with left:
    st.markdown('<div class="left-scroll">', unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload STL file", type=["stl"])
    if uploaded is not None:
        st.session_state.mesh = load_stl(uploaded.read())
        st.session_state.updated = True
        st.session_state.angles = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        st.session_state.shift = [0.0, 0.0, 0.0]

    if st.session_state.mesh is not None:
        st.subheader("🌀 Transform (Rotation & Translation)")

        # Rotation
        with st.expander("Rotation (degrees)", expanded=True):
            ax = st.number_input("X", value=float(st.session_state.angles["X"]), format="%.6f", key="ang_x")
            ay = st.number_input("Y", value=float(st.session_state.angles["Y"]), format="%.6f", key="ang_y")
            az = st.number_input("Z", value=float(st.session_state.angles["Z"]), format="%.6f", key="ang_z")
            pivot = st.radio(
                "Pivot(회전 기준점)", ["Model centroid", "Origin"],
                horizontal=True, index=1, key="pivot_sel"
            )

            # 회전 블록 아래 Apply (회전값 + 현재 shift 값 적용)
            if st.button("Apply Transform", key="apply_transform_rotation_block"):
                _apply_from_inputs(ax, ay, az, st.session_state.shift[0], st.session_state.shift[1], st.session_state.shift[2], pivot)

        # Shift
        with st.expander("Shift (mm)", expanded=True):
            dx = st.number_input("Shift X", value=float(st.session_state.shift[0]), format="%.6f", key="sh_x")
            dy = st.number_input("Shift Y", value=float(st.session_state.shift[1]), format="
