
import streamlit as st
from stl_backend import (
    load_stl_bytes, clone_mesh, apply_transform,
    mesh_bounds_text, render_snapshot, mesh_to_stl_bytes,
)

st.set_page_config(page_title="STL Viewer & Transformer", layout="wide")
st.title("STL Viewer & Transformer (Streamlit Edition)")
st.caption("Made by Dong-A Robotics R&D Center")

up = st.file_uploader("Upload STL file", type=["stl"])

if 'orig_mesh' not in st.session_state:
    st.session_state.orig_mesh = None
if 'mesh' not in st.session_state:
    st.session_state.mesh = None

if up is not None and st.session_state.orig_mesh is None:
    st.session_state.orig_mesh = load_stl_bytes(up.read(), up.name)
    st.session_state.mesh = st.session_state.orig_mesh.clone()

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    axis = st.selectbox("Rotation Axis", ["X","Y","Z"], index=0)
with col2:
    angle_deg = st.number_input("Rotation Angle (deg)", value=0.0)
with col3:
    dx = st.number_input("Shift X (mm)", value=0.0)
with col4:
    dy = st.number_input("Shift Y (mm)", value=0.0)
with col5:
    dz = st.number_input("Shift Z (mm)", value=0.0)

if st.button("Preview Transform") and st.session_state.orig_mesh is not None:
    st.session_state.mesh = apply_transform(
        st.session_state.orig_mesh,
        axis, angle_deg, dx, dy, dz,
    )

if st.session_state.mesh is not None:
    snap = render_snapshot(st.session_state.mesh)
    st.image(snap, caption="Preview")
    st.text(mesh_bounds_text(st.session_state.mesh))

    data = mesh_to_stl_bytes(st.session_state.mesh)
    st.download_button(
        label="Download Transformed STL",
        data=data,
        file_name="transformed.stl",
        mime="application/sla",
    )
