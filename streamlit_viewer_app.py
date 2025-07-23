import streamlit as st
from stl_backend import load_stl, apply_transform, render_mesh, save_stl_bytes

st.set_page_config(page_title="STL Viewer (Cloud Compatible)")
st.title("STL Viewer & Transformer (Streamlit Cloud Ver.)")

uploaded = st.file_uploader("Upload STL file", type=["stl"])

if uploaded:
    st.session_state.mesh = load_stl(uploaded.read())

    axis = st.selectbox("Rotation Axis", ["X", "Y", "Z"])
    angle = st.number_input("Rotation Angle (degrees)", value=0.0)
    dx = st.number_input("Shift X", value=0.0)
    dy = st.number_input("Shift Y", value=0.0)
    dz = st.number_input("Shift Z", value=0.0)

    if st.button("Apply Transform"):
        st.session_state.mesh = apply_transform(st.session_state.mesh, axis, angle, dx, dy, dz)

    img = render_mesh(st.session_state.mesh)
    st.image(img, caption="Preview")

    st.download_button("Download Transformed STL", data=save_stl_bytes(st.session_state.mesh),
                       file_name="transformed.stl", mime="application/sla")