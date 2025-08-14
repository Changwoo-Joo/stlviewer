# streamlit_viewer_app.py
import uuid
import streamlit as st
from stl_backend import (
    load_stl, save_stl_bytes, render_mesh,  # render_mesh는 필요없지만 import 유지 가능
    get_axis_length, get_axis_lengths,
    apply_transform_xyz, apply_scale_axis_uniform, apply_scale_axis_absolute,
    put_preview_bytes, get_preview_store,
)

st.set_page_config(page_title="STL Viewer & Transformer", layout="wide")
st.title("STL Viewer & Transformer (Streamlit Cloud Ver.)")

# ---- 스타일(타이틀 잘림 방지, 본문 최대폭 넓게) ----
st.markdown("""
<style>
h1, header h1 { white-space: normal !important; font-size: 1.9rem !important; line-height: 1.25 !important; }
.block-container { padding-top: 0.6rem; max-width: 1200px; }
</style>
""", unsafe_allow_html=True)

# ---- 세션 상태 ----
if "mesh" not in st.session_state: st.session_state.mesh = None
if "angles" not in st.session_state: st.session_state.angles = {"X": 0.0, "Y": 0.0, "Z": 0.0}
if "shift" not in st.session_state: st.session_state.shift = [0.0, 0.0, 0.0]
if "abs_len_x" not in st.session_state: st.session_state.abs_len_x = None
if "abs_len_y" not in st.session_state: st.session_state.abs_len_y = None
if "abs_len_z" not in st.session_state: st.session_state.abs_len_z = None
if "preview_token" not in st.session_state: st.session_state.preview_token = str(uuid.uuid4())

# ---- 프리뷰 스토어 준비(서버 공유 dict) ----
_ = get_preview_store()  # 초기화

# ---- 프리뷰 새 탭 링크 빌더 ----
def preview_link():
    # 멀티페이지 경로: pages/Preview.py → "?page=Preview"
    return f"?page=Preview&token={st.session_state.preview_token}"

def update_preview_store():
    if st.session_state.mesh is not None:
        put_preview_bytes(st.session_state.preview_token, st.session_state.mesh)

# ---- 업로드 ----
uploaded = st.file_uploader("Upload STL file", type=["stl"])
if uploaded is not None:
    data = uploaded.getvalue()
    if data:
        st.session_state.mesh = load_stl(data)
        st.session_state.angles = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        st.session_state.shift = [0.0, 0.0, 0.0]
        lx, ly, lz = get_axis_lengths(st.session_state.mesh)
        st.session_state.abs_len_x, st.session_state.abs_len_y, st.session_state.abs_len_z = lx, ly, lz
        update_preview_store()
        st.success("STL 로드 완료. 상단 버튼으로 프리뷰를 새 탭에서 열 수 있어요.")
    else:
        st.error("업로드된 파일을 읽지 못했습니다. 파일을 다시 선택해주세요.")

# ---- 프리뷰 새 탭 버튼 ----
st.markdown(
    f'<a href="{preview_link()}" target="_blank" style="display:inline-block;padding:8px 14px;background:#4f46e5;color:white;border-radius:8px;text-decoration:none;">🔎 Open Preview in New Tab</a>',
    unsafe_allow_html=True,
)

# ================= Controls (페이지 전체 폭 사용) =================
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
        if st.button("Apply Transform (Rotation only)"):
            dax = float(ax) - st.session_state.angles["X"]
            day = float(ay) - st.session_state.angles["Y"]
            daz = float(az) - st.session_state.angles["Z"]
            if any(abs(v) > 0 for v in [dax, day, daz]):
                st.session_state.mesh = apply_transform_xyz(
                    st.session_state.mesh,
                    ax_deg=dax, ay_deg=day, az_deg=daz,
                    dx=0.0, dy=0.0, dz=0.0,
                    pivot=("origin" if pivot == "Origin" else "centroid"),
                )
                st.session_state.angles = {"X": float(ax), "Y": float(ay), "Z": float(az)}
                update_preview_store()
                st.toast("Rotation applied. Preview tab: refresh(F5) to see changes.", icon="✅")

    with st.expander("Shift (mm)", expanded=True):
        dx = st.number_input("Shift X", value=float(st.session_state.shift[0]), format="%.6f", key="sh_x")
        dy = st.number_input("Shift Y", value=float(st.session_state.shift[1]), format="%.6f", key="sh_y")
        dz = st.number_input("Shift Z", value=float(st.session_state.shift[2]), format="%.6f", key="sh_z")

    if st.button("Apply Transform (Rotation + Shift)"):
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
            update_preview_store()
            st.toast("Transform applied. Preview tab: refresh(F5) to see changes.", icon="✅")

    st.subheader("📏 Axis-Based Scale (Uniform)")
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
        lx, ly, lz = get_axis_lengths(st.session_state.mesh)
        st.session_state.abs_len_x, st.session_state.abs_len_y, st.session_state.abs_len_z = lx, ly, lz
        update_preview_store()
        st.toast("Uniform scale applied.", icon="✅")

    st.subheader("📐 Per-Axis Absolute Size (Non-uniform)")
    if st.session_state.abs_len_x is None or st.session_state.abs_len_y is None or st.session_state.abs_len_z is None:
        lx, ly, lz = get_axis_lengths(st.session_state.mesh)
        st.session_state.abs_len_x, st.session_state.abs_len_y, st.session_state.abs_len_z = lx, ly, lz

    colx, coly, colz = st.columns(3)
    with colx:
        abs_x = st.number_input("X 길이 (mm)", value=float(st.session_state.abs_len_x), key="abs_x", format="%.6f")
    with coly:
        abs_y = st.number_input("Y 길이 (mm)", value=float(st.session_state.abs_len_y), key="abs_y", format="%.6f")
    with colz:
        abs_z = st.number_input("Z 길이 (mm)", value=float(st.session_state.abs_len_z), key="abs_z", format="%.6f")

    if st.button("Apply Per-Axis Absolute Scaling"):
        changed = False
        cur_x, cur_y, cur_z = get_axis_lengths(st.session_state.mesh)
        if abs(abs_x - cur_x) > 1e-9:
            st.session_state.mesh = apply_scale_axis_absolute(st.session_state.mesh, "X", float(abs_x))
            changed = True
        if abs(abs_y - cur_y) > 1e-9:
            st.session_state.mesh = apply_scale_axis_absolute(st.session_state.mesh, "Y", float(abs_y))
            changed = True
        if abs(abs_z - cur_z) > 1e-9:
            st.session_state.mesh = apply_scale_axis_absolute(st.session_state.mesh, "Z", float(abs_z))
            changed = True

        if changed:
            st.session_state.abs_len_x, st.session_state.abs_len_y, st.session_state.abs_len_z = get_axis_lengths(st.session_state.mesh)
            update_preview_store()
            st.toast("Per-axis scale applied.", icon="✅")

    st.download_button(
        "📥 Download Transformed STL",
        data=save_stl_bytes(st.session_state.mesh),
        file_name="transformed.stl",
        mime="application/sla",
    )
