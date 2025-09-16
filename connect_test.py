import streamlit as st
from supabase import create_client

# secrets.toml에서 값 가져오기
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase(url, key):
    return create_client(url, key)

supabase = init_supabase(url, key)

# 테스트용 출력 (나중에 지워도 됨)
st.write("Supabase 클라이언트 연결 완료 ✅")
