import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import requests

# 페이지 설정
st.set_page_config(
    page_title="환경 모니터링 대시보드",
    page_icon="🌡️",
    layout="wide"
)

# Supabase 설정 (환경변수에서 가져오기)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except KeyError:
    st.error("❌ Supabase 설정이 없습니다. secrets.toml을 확인해주세요.")
    st.stop()

@st.cache_data(ttl=30)  # 30초마다 캐시 갱신
def load_data(hours=24):
    """환경 센서 데이터 로드"""
    try:
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        
        url = f"{SUPABASE_URL}/rest/v1/maintable2"
        params = {
            'created_at': f'gte.{time_threshold.isoformat()}',
            'order': 'created_at.asc'
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                df['created_at'] = pd.to_datetime(df['created_at'])
                return df
            else:
                return pd.DataFrame()
        else:
            st.error(f"API 요청 실패: {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

def main():
    # 헤더
    st.title("🌡️ 실시간 환경 모니터링 대시보드")
    st.markdown("---")
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")
        
        time_options = {
            "최근 1시간": 1,
            "최근 6시간": 6,
            "최근 12시간": 12,
            "최근 24시간": 24,
            "최근 3일": 72
        }
        selected_time = st.selectbox("데이터 범위", list(time_options.keys()), index=3)
        hours = time_options[selected_time]
        
        auto_refresh = st.checkbox("자동 새로고침", value=True)
        
        if st.button("🔄 새로고침"):
            st.cache_data.clear()
    
    # 데이터 로드
    df = load_data(hours)
    
    if df.empty:
        st.warning("📭 데이터가 없습니다. ESP8266이 작동 중인지 확인해주세요.")
        st.stop()
    
    # 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        temp = df['temperature'].iloc[-1] if not df.empty else 0
        st.metric("현재 온도", f"{temp:.1f}°C")
    
    with col2:
        humidity = df['humidity'].iloc[-1] if not df.empty else 0
        st.metric("현재 습도", f"{humidity:.1f}%")
    
    with col3:
        light = df['light'].iloc[-1] if not df.empty else 0
        st.metric("현재 조도", f"{light}%")
    
    with col4:
        data_count = len(df)
        st.metric("데이터 개수", f"{data_count}개")
    
    # 메인 차트들
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌡️ 온도 변화")
        fig_temp = px.line(df, x='created_at', y='temperature',
                          title="온도 추이",
                          labels={'created_at': '시간', 'temperature': '온도 (°C)'})
        fig_temp.update_traces(line_color='red')
        st.plotly_chart(fig_temp, use_container_width=True)
    
    with col2:
        st.subheader("💧 습도 변화")
        fig_hum = px.line(df, x='created_at', y='humidity',
                         title="습도 추이",
                         labels={'created_at': '시간', 'humidity': '습도 (%)'})
        fig_hum.update_traces(line_color='blue')
        st.plotly_chart(fig_hum, use_container_width=True)
    
    # 조도 차트
    st.subheader("💡 조도 변화")
    fig_light = px.line(df, x='created_at', y='light',
                       title="조도 추이",
                       labels={'created_at': '시간', 'light': '조도 (%)'})
    fig_light.update_traces(line_color='orange')
    st.plotly_chart(fig_light, use_container_width=True)
    
    # 복합 차트
    st.subheader("📊 종합 환경 데이터")
    fig_combined = go.Figure()
    
    fig_combined.add_trace(go.Scatter(x=df['created_at'], y=df['temperature'],
                                    mode='lines', name='온도 (°C)', line=dict(color='red')))
    fig_combined.add_trace(go.Scatter(x=df['created_at'], y=df['humidity'],
                                    mode='lines', name='습도 (%)', line=dict(color='blue')))
    fig_combined.add_trace(go.Scatter(x=df['created_at'], y=df['light'],
                                    mode='lines', name='조도 (%)', line=dict(color='orange')))
    
    fig_combined.update_layout(title="환경 데이터 종합", xaxis_title="시간", yaxis_title="값")
    st.plotly_chart(fig_combined, use_container_width=True)
    
    # 최근 데이터 테이블
    st.subheader("📋 최근 측정 데이터")
    recent_data = df.tail(10)[['created_at', 'temperature', 'humidity', 'light']].sort_values('created_at', ascending=False)
    recent_data['created_at'] = recent_data['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
    recent_data.columns = ['시간', '온도(°C)', '습도(%)', '조도(%)']
    st.dataframe(recent_data, use_container_width=True)
    
    # 자동 새로고침
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()
