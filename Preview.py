# pages/Preview.py
import streamlit as st
from stl_backend import get_preview_bytes, load_stl, render_mesh

st.set_page_config(page_title="Preview", layout="wide")

st.markdown("""
<style>
h1, header h1 { white-space: normal !important; font-size: 1.7rem !important; line-height: 1.25 !important; }
.block-container { padding-top: 0.6rem; max-width: 1400px; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Preview (Full quality)")

# URL에서 token 받기
params = st.experimental_get_query_params()
token = params.get("token", [None])[0]

if not token:
    st.warning("토큰이 없습니다. 메인 페이지에서 'Open Preview in New Tab'을 클릭해 들어오세요.")
else:
    data = get_preview_bytes(token)
    if not data:
        st.info("미리보기 데이터가 아직 없습니다. 메인 페이지에서 STL을 업로드하거나 변환을 적용한 뒤 새로고침(F5) 해주세요.")
    else:
        m = load_stl(data)
        fig = render_mesh(m, height=900)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "scrollZoom": True})

        # 새로고침 유도
        st.caption("변환을 적용한 뒤에는 이 탭을 새로고침(F5)하면 최신 상태로 반영됩니다.")
