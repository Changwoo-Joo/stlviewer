# streamlit_viewer_app.py
import streamlit as st
from stl_backend import (
    load_stl,
    apply_transform,
    apply_scale,
    render_mesh,
    save_stl_bytes,
    get_axis_length,
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

# 누적 표시용(각 축 회전각 / 이동값)
if "display_angles" not in st.session_state:
    st.session_state.display_angles = {"X": 0.0, "Y": 0.0, "Z": 0.0}
if "display_shift" not in st.session_state:
    st.session_state.display_shift = [0.0, 0.0, 0.0]  # dx, dy, dz

# 업로드 처리
if uploaded is not None:
    st.session_state.mesh = load_stl(uploaded.read())
    st.session_state.updated = True
    # 누적 표시값 초기화
    st.session_state.display_angles = {"X": 0.0, "Y": 0.0, "Z": 0.0}
    st.session_state.display_shift = [0.0, 0.0, 0.0]

# ---- 변환 메뉴 ----
if st.session_state.mesh is not None:
    st.subheader("🌀 Transform (Rotation & Translation)")
    rot_col1, rot_col2 = st.columns([1, 3])

    with rot_col1:
        axis = st.selectbox("Rotation Axis", ["X", "Y", "Z"], key="rot_axis")
        # 표시값(현재 축의 누적 회전각)
        current_display_angle = st.session_state.display_angles.get(axis, 0.0)

        # 표시용 입력: 목표 절대값을 입력받고, 기존 표시값과의 차이만큼만 실제 적용
        angle = st.number_input(
            "Rotation Angle (degrees)",
            value=float(current_display_angle),
            format="%.6f",
            key=f"angle_input_{axis}",
        )

        dx = st.number_input(
            "Shift X",
            value=float(st.session_state.display_shift[0]),
            format="%.6f",
            key="shift_x_input",
        )
        dy = st.number_input(
            "Shift Y",
            value=float(st.session_state.display_shift[1]),
            format="%.6f",
            key="shift_y_input",
        )
        dz = st.number_input(
            "Shift Z",
            value=float(st.session_state.display_shift[2]),
            format="%.6f",
            key="shift_z_input",
        )

        if st.button("Apply Transform"):
            # 이전 표시값과의 차이를 적용(절대 목표 → 델타로 변환)
            delta_angle = float(angle) - st.session_state.display_angles[axis]
            delta_dx = float(dx) - st.session_state.display_shift[0]
            delta_dy = float(dy) - st.session_state.display_shift[1]
            delta_dz = float(dz) - st.session_state.display_shift[2]

            if any(abs(v) > 0 for v in [delta_angle, delta_dx, delta_dy, delta_dz]):
                st.session_state.mesh = apply_transform(
                    st.session_state.mesh, axis, delta_angle, delta_dx, delta_dy, delta_dz
                )
                # 표시값 갱신
                st.session_state.display_angles[axis] = float(angle)
                st.session_state.display_shift = [float(dx), float(dy), float(dz)]
                st.session_state.updated = True

    with rot_col2:
        st.markdown("### 🖱️ Quick Controls (Drag-like)")
        snap_mode = st.checkbox(
            "Shift-like Snap (회전 90°, 이동 Large step)", value=False
        )

        # 스냅 off: 작은 스텝 / on: 큰 스텝
        rot_small, rot_large = 10.0, 90.0
        move_small, move_large = 5.0, 50.0
        rot_step = rot_large if snap_mode else rot_small
        move_step = move_large if snap_mode else move_small

        qc1, qc2, qc3 = st.columns(3)

        # ---- Rotate Controls ----
        with qc1:
            st.write("↻ Rotate")
            c = st.columns(2)
            if c[0].button(f"−{int(rot_step)}°"):
                st.session_state.mesh = apply_transform(
                    st.session_state.mesh, axis, -rot_step, 0.0, 0.0, 0.0
                )
                st.session_state.display_angles[axis] -= rot_step
                st.session_state.updated = True
            if c[1].button(f"+{int(rot_step)}°"):
                st.session_state.mesh = apply_transform(
                    st.session_state.mesh, axis, rot_step, 0.0, 0.0, 0.0
                )
                st.session_state.display_angles[axis] += rot_step
                st.session_state.updated = True

        # ---- Move X/Y Controls ----
        with qc2:
            st.write("⇄ Move X / Y")
            r1 = st.columns(2)
            if r1[0].button(f"X −{int(move_step)}"):
                st.session_state.mesh = apply_transform(
                    st.session_state.mesh, "Z", 0.0, -move_step, 0.0, 0.0
                )
                st.session_state.display_shift[0] -= move_step
                st.session_state.updated = True
            if r1[1].button(f"X +{int(move_step)}"):
                st.session_state.mesh = apply_transform(
                    st.session_state.mesh, "Z", 0.0, +move_step, 0.0, 0.0
                )
                st.session_state.display_shift[0] += move_step
                st.session_state.updated = True

            r2 = st.columns(2)
            if r2[0].button(f"Y −{int(move_step)}"):
                st.session_state.mesh = apply_transform(
                    st.session_state.mesh, "Z", 0.0, 0.0, -move_step, 0.0
                )
                st.session_state.display_shift[1] -= move_step
                st.session_state.updated = True
            if r2[1].button(f"Y +{int(move_step)}"):
                st.session_state.mesh = apply_transform(
                    st.session_state.mesh, "Z", 0.0, 0.0, +move_step, 0.0
                )
                st.session_state.display_shift[1] += move_step
                st.session_state.updated = True

        # ---- Move Z Controls ----
        with qc3:
            st.write("⇅ Move Z")
            r3 = st.columns(2)
            if r3[0].button(f"Z −{int(move_step)}"):
                st.session_state.mesh = apply_transform(
                    st.session_state.mesh, "Z", 0.0, 0.0, 0.0, -move_step
                )
                st.session_state.display_shift[2] -= move_step
                st.session_state.updated = True
            if r3[1].button(f"Z +{int(move_step)}"):
                st.session_state.mesh = apply_transform(
                    st.session_state.mesh, "Z", 0.0, 0.0, 0.0, +move_step
                )
                st.session_state.display_shift[2] += move_step
                st.session_state.updated = True

    # ---- Axis-Based Scale ----
    st.subheader("📏 Axis-Based Scale")
    scale_axis = st.selectbox("Scale 기준 축", ["X", "Y", "Z"], key="scale_axis")

    # 선택된 축의 현재 길이를 기본값으로 자동 기입
    if st.session_state.mesh is not None:
        curr_len = get_axis_length(st.session_state.mesh, st.session_state.scale_axis)
    else:
        curr_len = 100.0  # fallback

    target_length = st.number_input(
        "해당 축의 최종 길이 (mm)",
        value=float(curr_len),
        key=f"target_length_{st.session_state.scale_axis}",
        format="%.6f",
        step=1.0,
    )

    if st.button("Apply Axis-Based Scaling"):
        st.session_state.mesh = apply_scale(
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
