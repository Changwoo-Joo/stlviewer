# streamlit_viewer_app.py
import streamlit as st
from stl_backend import (
    load_stl, save_stl_bytes, render_mesh,
    get_axis_length, get_axis_lengths,
    apply_transform_xyz, apply_scale_axis_uniform, apply_scale_axis_absolute,
)

st.set_page_config(page_title="STL Viewer & Transformer", layout="wide")
st.title("STL Viewer & Transformer (Streamlit Cloud Ver.)")

# ---- Global CSS: 왼쪽 패널 전용 스크롤 ----
st.markdown("""
<style>
/* 왼쪽 패널: 독립 스크롤바 + 화면 높이 맞춤 */
.left-scroll {
    position: sticky;
    top: 0;
    height: calc(100vh - 60px); /* 필요 시 -값 조정 */
    overflow-y: auto;
    padding-right: 12px;
}

/* 스크롤바 스타일 */
.left-scroll::-webkit-scrollbar { width: 8px; }
.left-scroll::-webkit-scrollbar-thumb { background: #bbb; border-radius: 8px; }
.left-scroll::-webkit-scrollbar-track { background: transparent; }
.left-scroll { scrollbar-width: thin; scrollbar-color: #bbb transparent; }

/* 페이지 전체 상단 여백 줄이기 */
.block-container { padding-top: 0.4rem !important; }

/* 제목 길 때 줄바꿈 방지 & 폰트 조절 */
div.plot-container div.gtitle { white-space: nowrap !important; font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)

# ---- 세션 상태 ----
if "mesh" not in st.session_state: st.session_state.mesh = None
if "updated" not in st.session_state: st.session_state.updated = False
if "last_fig" not in st.session_state: st.session_state.last_fig = None
if "angles" not in st.session_state: st.session_state.angles = {"X": 0.0, "Y": 0.0, "Z": 0.0}
if "shift" not in st.session_state: st.session_state.shift = [0.0, 0.0, 0.0]
if "pivot_sel" not in st.session_state: st.session_state.pivot_sel = "Origin"
if "preview_height" not in st.session_state: st.session_state.preview_height = 880
for k in ["abs_len_x", "abs_len_y", "abs_len_z"]:
    if k not in st.session_state: st.session_state[k] = None

# ---- 좌/우 레이아웃 ----
left, right = st.columns([0.25, 0.75], gap="large")

with left:
    st.markdown('<div class="left-scroll">', unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload STL file", type=["stl"])
    if uploaded is not None:
        data = uploaded.getvalue()
        if data:
            st.session_state.mesh = load_stl(data)
            st.session_state.updated = True
            st.session_state.angles = {"X": 0.0, "Y": 0.0, "Z": 0.0}
            st.session_state.shift = [0.0, 0.0, 0.0]
            lx, ly, lz = get_axis_lengths(st.session_state.mesh)
            st.session_state.abs_len_x, st.session_state.abs_len_y, st.session_state.abs_len_z = lx, ly, lz
        else:
            st.error("업로드된 파일을 읽지 못했습니다.")

    if st.session_state.mesh is not None:
        st.subheader("🌀 Transform (Rotation & Translation)")
        with st.expander("Rotation (degrees)", expanded=True):
            ax = st.number_input("X", value=st.session_state.angles["X"], format="%.6f", key="ang_x")
            ay = st.number_input("Y", value=st.session_state.angles["Y"], format="%.6f", key="ang_y")
            az = st.number_input("Z", value=st.session_state.angles["Z"], format="%.6f", key="ang_z")
            pivot = st.radio("Pivot(회전 기준점)", ["Model centroid", "Origin"], horizontal=True, index=1, key="pivot_sel")
            if st.button("Apply Transform", key="apply_transform_rotation_block"):
                dax, day, daz = ax - st.session_state.angles["X"], ay - st.session_state.angles["Y"], az - st.session_state.angles["Z"]
                if any(abs(v) > 0 for v in [dax, day, daz]):
                    st.session_state.mesh = apply_transform_xyz(st.session_state.mesh, dax, day, daz, 0, 0, 0, pivot=("origin" if pivot == "Origin" else "centroid"))
                    st.session_state.angles = {"X": ax, "Y": ay, "Z": az}
                    st.session_state.updated = True

        with st.expander("Shift (mm)", expanded=True):
            dx = st.number_input("Shift X", value=st.session_state.shift[0], format="%.6f", key="sh_x")
            dy = st.number_input("Shift Y", value=st.session_state.shift[1], format="%.6f", key="sh_y")
            dz = st.number_input("Shift Z", value=st.session_state.shift[2], format="%.6f", key="sh_z")

        if st.button("Apply Transform", key="apply_transform_main"):
            dax, day, daz = ax - st.session_state.angles["X"], ay - st.session_state.angles["Y"], az - st.session_state.angles["Z"]
            ddx, ddy, ddz = dx - st.session_state.shift[0], dy - st.session_state.shift[1], dz - st.session_state.shift[2]
            if any(abs(v) > 0 for v in [dax, day, daz, ddx, ddy, ddz]):
                st.session_state.mesh = apply_transform_xyz(st.session_state.mesh, dax, day, daz, ddx, ddy, ddz, pivot=("origin" if pivot == "Origin" else "centroid"))
                st.session_state.angles, st.session_state.shift = {"X": ax, "Y": ay, "Z": az}, [dx, dy, dz]
                st.session_state.updated = True

        st.subheader("📏 Axis-Based Scale (Uniform)")
        scale_axis = st.selectbox("Scale 기준 축", ["X", "Y", "Z"], key="scale_axis")
        curr_len = get_axis_length(st.session_state.mesh, scale_axis)
        target_length = st.number_input("해당 축의 최종 길이 (mm)", value=curr_len, key=f"target_length_{scale_axis}", format="%.6f", step=1.0)
        if st.button("Apply Axis-Based Scaling"):
            st.session_state.mesh = apply_scale_axis_uniform(st.session_state.mesh, scale_axis, target_length)
            st.session_state.abs_len_x, st.session_state.abs_len_y, st.session_state.abs_len_z = get_axis_lengths(st.session_state.mesh)
            st.session_state.updated = True

        st.subheader("📐 Per-Axis Absolute Size (Non-uniform)")
        if None in (st.session_state.abs_len_x, st.session_state.abs_len_y, st.session_state.abs_len_z):
            st.session_state.abs_len_x, st.session_state.abs_len_y, st.session_state.abs_len_z = get_axis_lengths(st.session_state.mesh)
        colx, coly, colz = st.columns(3)
        abs_x = colx.number_input("X 길이 (mm)", value=st.session_state.abs_len_x, key="abs_x", format="%.6f")
        abs_y = coly.number_input("Y 길이 (mm)", value=st.session_state.abs_len_y, key="abs_y", format="%.6f")
        abs_z = colz.number_input("Z 길이 (mm)", value=st.session_state.abs_len_z, key="abs_z", format="%.6f")
        if st.button("Apply Per-Axis Absolute Scaling"):
            changed = False
            cur_x, cur_y, cur_z = get_axis_lengths(st.session_state.mesh)
            if abs(abs_x - cur_x) > 1e-9: st.session_state.mesh = apply_scale_axis_absolute(st.session_state.mesh, "X", abs_x); changed = True
            if abs(abs_y - cur_y) > 1e-9: st.session_state.mesh = apply_scale_axis_absolute(st.session_state.mesh, "Y", abs_y); changed = True
            if abs(abs_z - cur_z) > 1e-9: st.session_state.mesh = apply_scale_axis_absolute(st.session_state.mesh, "Z", abs_z); changed = True
            if changed:
                st.session_state.abs_len_x, st.session_state.abs_len_y, st.session_state.abs_len_z = get_axis_lengths(st.session_state.mesh)
                st.session_state.updated = True

        st.download_button("📥 Download Transformed STL", data=save_stl_bytes(st.session_state.mesh), file_name="transformed.stl", mime="application/sla")

    st.markdown('</div>', unsafe_allow_html=True)

with right:
    if st.session_state.mesh is not None:
        st.subheader("📊 Preview (Full quality)")
        fig = render_mesh(st.session_state.mesh, height=st.session_state.preview_height)
        st.session_state.last_fig = fig
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "scrollZoom": False})
