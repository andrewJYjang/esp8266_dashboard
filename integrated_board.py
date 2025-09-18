# 통합 센서 모니터링 + 커뮤니티 대시보드 (상하 분할)
import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from supabase import create_client, Client
import time

# =============================================================================
# Supabase 설정 및 클라이언트들
# =============================================================================

# Simple REST API 클라이언트 (app.py 방식)
class SimpleSupabaseClient:
    def __init__(self, url, key):
        self.url = url.rstrip('/')
        self.key = key
        self.headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
    
    def select(self, table, columns="*", filters=None, order=None, limit=None):
        endpoint = f"{self.url}/rest/v1/{table}"
        params = {'select': columns}
        
        if filters:
            for key, value in filters.items():
                params[key] = value
        
        if order:
            params['order'] = order
            
        if limit:
            params['limit'] = limit
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"데이터 조회 실패: {response.status_code}")
            return []
    
    def insert(self, table, data):
        endpoint = f"{self.url}/rest/v1/{table}"
        response = requests.post(endpoint, headers=self.headers, json=data)
        
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, response.text


try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
except Exception:
    st.sidebar.error("Supabase 설정이 필요합니다!")
    supabase_url = st.sidebar.text_input("Supabase URL")
    supabase_key = st.sidebar.text_input("Supabase Anon Key", type="password")
    if not supabase_url or not supabase_key:
        st.stop()

@st.cache_resource
def init_supabase(url, key):
    simple_client = SimpleSupabaseClient(url, key)
    auth_client = create_client(url, key)
    return simple_client, auth_client

simple_supabase, auth_supabase = init_supabase(supabase_url, supabase_key)

# =============================================================================
# 센서 데이터 관련 함수들 (app.py 기반)
# =============================================================================

def get_sensor_data_simple(hours=24):
    """센서 데이터 조회 (Simple REST API)"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        data = simple_supabase.select(
            'maintable2',
            columns='id,created_at,light,temperature,humidity',
            filters={
                'created_at': f'gte.{start_time.isoformat()}',
            },
            order='created_at.desc',
            limit=1000
        )
        
        if data:
            if len(data) == 1000:
                st.warning("⚠️ 데이터가 너무 많아 1000개만 표시합니다. 더 짧은 기간을 선택해주세요.")
            df = pd.DataFrame(data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"센서 데이터 조회 오류: {e}")
        return pd.DataFrame()



def get_sensor_stats(df):
    """센서 데이터 통계 계산"""
    if df.empty:
        return None
    
    stats = {
        "온도": {
            "현재": df.iloc[0]['temperature'],
            "평균": df['temperature'].mean(),
            "최고": df['temperature'].max(),
            "최저": df['temperature'].min()
        },
        "습도": {
            "현재": df.iloc[0]['humidity'],
            "평균": df['humidity'].mean(),
            "최고": df['humidity'].max(),
            "최저": df['humidity'].min()
        },
        "조도": {
            "현재": df.iloc[0]['light'],
            "평균": df['light'].mean(),
            "최고": df['light'].max(),
            "최저": df['light'].min()
        }
    }
    return stats

# =============================================================================
# 커뮤니티 관련 함수들 (member_bbs.py 기반)
# =============================================================================

def sign_up(email, password, username):
    try:
        response = auth_supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "username": username
                }
            }
        })
        return response.user, None
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    try:
        response = auth_supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response.user, None
    except Exception as e:
        return None, str(e)

def sign_out():
    auth_supabase.auth.sign_out()

def add_comment(user_id, username, content, comment_type="comment"):
    try:
        data = {
            "user_id": user_id,
            "username": username,
            "content": content,
            "type": comment_type,
            "created_at": datetime.now().isoformat()
        }
        
        response = auth_supabase.table('user_comments').insert(data).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def get_comments():
    try:
        response = auth_supabase.table('user_comments').select("*").order(
            'created_at', desc=True
        ).limit(50).execute()
        return response.data
    except Exception as e:
        st.error(f"댓글 조회 오류: {e}")
        return []

def add_reply(comment_id, user_id, username, content):
    try:
        data = {
            "comment_id": comment_id,
            "user_id": user_id,
            "username": username,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        
        response = auth_supabase.table('comment_replies').insert(data).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def get_replies(comment_id):
    try:
        response = auth_supabase.table('comment_replies').select("*").eq(
            'comment_id', comment_id
        ).order('created_at', desc=False).execute()
        return response.data
    except Exception as e:
        return []

# =============================================================================
# 메인 앱
# =============================================================================

def main():
    st.set_page_config(
        page_title="🌱 통합 센서 모니터링 & 커뮤니티", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 세션 상태 초기화
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'username_simple' not in st.session_state:
        st.session_state.username_simple = None
    
    # =============================================================================
    # 사이드바 - 사용자 인증 및 컨트롤
    # =============================================================================
    
    with st.sidebar:
        st.title("🎛️ 대시보드 컨트롤")
        
        # 섹션 표시 컨트롤
        sensor_section = st.checkbox("📊 센서 모니터링", value=True)
        community_section = st.checkbox("💬 커뮤니티", value=True)
        
        st.divider()
        
        # 사용자 인증 (커뮤니티용)
        st.subheader("👤 사용자 인증")
        
        if st.session_state.user is None:
            # 로그인/회원가입 탭
            tab1, tab2 = st.tabs(["로그인", "회원가입"])
            
            with tab1:
                with st.form("login_form"):
                    email = st.text_input("이메일", placeholder="user@example.com")
                    password = st.text_input("비밀번호", type="password")
                    login_btn = st.form_submit_button("🚪 로그인", use_container_width=True)
                    
                    if login_btn and email and password:
                        with st.spinner("로그인 중..."):
                            user, error = sign_in(email, password)
                            if user:
                                st.session_state.user = user
                                st.rerun()
                            else:
                                st.error(f"로그인 실패: {error}")
            
            with tab2:
                with st.form("signup_form"):
                    email = st.text_input("이메일", placeholder="user@example.com")
                    password = st.text_input("비밀번호", type="password", help="6자 이상 입력")
                    username = st.text_input("사용자명", placeholder="홍길동")
                    signup_btn = st.form_submit_button("📝 회원가입", use_container_width=True)
                    
                    if signup_btn and email and password and username:
                        if len(password) < 6:
                            st.error("비밀번호는 6자 이상이어야 합니다.")
                        else:
                            with st.spinner("회원가입 중..."):
                                user, error = sign_up(email, password, username)
                                if user:
                                    st.success("🎉 회원가입 완료! 이메일을 확인해주세요.")
                                else:
                                    st.error(f"회원가입 실패: {error}")
        else:
            # 로그인된 사용자 정보
            username = st.session_state.user.user_metadata.get('username', '사용자')
            st.success(f"👋 안녕하세요, **{username}**님!")
            
            if st.button("🚪 로그아웃", use_container_width=True):
                sign_out()
                st.session_state.user = None
                st.rerun()
        
        st.divider()
        
        # 간단한 사용자명 (센서 댓글용)
        st.subheader("💭 간단 댓글 (비회원)")
        if st.session_state.username_simple is None:
            username_simple = st.text_input("닉네임", placeholder="홍길동")
            if st.button("입장하기", use_container_width=True):
                if username_simple.strip():
                    st.session_state.username_simple = username_simple.strip()
                    st.rerun()
                else:
                    st.error("닉네임을 입력해주세요.")
        else:
            st.info(f"🎭 닉네임: **{st.session_state.username_simple}**")
            if st.button("닉네임 변경", use_container_width=True):
                st.session_state.username_simple = None
                st.rerun()
        
        st.divider()
        
        # 전체 새로고침
        if st.button("🔄 전체 새로고침", use_container_width=True):
            st.rerun()
    
    # 메인 타이틀
    st.title("🌱 통합 센서 모니터링 & 커뮤니티")
    st.caption("ESP8266 센서 데이터 실시간 모니터링 + 커뮤니티 소통 플랫폼")
    st.markdown("---")
    
    # =============================================================================
    # 상단: 센서 모니터링 섹션 (app.py 기반)
    # =============================================================================
    
    if sensor_section:
        st.header("📊 실시간 센서 모니터링")
        
        # 시간 범위 선택
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            hours = st.selectbox("📅 데이터 조회 범위", 
                               options=[1, 6, 12, 24, 48, 72], 
                               index=3,
                               format_func=lambda x: f"최근 {x}시간")
        
        with col2:
            auto_refresh = st.checkbox("🔄 자동 새로고침", value=False)
        
        with col3:
            if st.button("📊 센서 데이터 새로고침"):
                st.rerun()
        
        # 센서 데이터 조회
        with st.spinner("센서 데이터를 불러오는 중..."):
            df_sensor = get_sensor_data_simple(hours)
        
        if not df_sensor.empty:
            # 현재 상태 표시
            stats = get_sensor_stats(df_sensor)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "🌡️ 현재 온도", 
                    f"{stats['온도']['현재']:.1f}°C",
                    delta=f"평균: {stats['온도']['평균']:.1f}°C"
                )
            
            with col2:
                st.metric(
                    "💧 현재 습도", 
                    f"{stats['습도']['현재']:.1f}%",
                    delta=f"평균: {stats['습도']['평균']:.1f}%"
                )
            
            with col3:
                st.metric(
                    "☀️ 현재 조도", 
                    f"{stats['조도']['현재']:.0f}",
                    delta=f"평균: {stats['조도']['평균']:.0f}"
                )
            
            with col4:
                st.metric(
                    "📊 데이터 개수", 
                    f"{len(df_sensor)}개",
                    delta=f"마지막 업데이트: {df_sensor.iloc[0]['created_at'].strftime('%H:%M:%S')}"
                )
            
            # 센서 데이터 차트
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('🌡️ 온도 (°C)', '💧 습도 (%)', '☀️ 조도'),
                vertical_spacing=0.08,
                shared_xaxes=True
            )
            
            # 온도 차트
            fig.add_trace(
                go.Scatter(
                    x=df_sensor['created_at'], 
                    y=df_sensor['temperature'],
                    name='온도',
                    line=dict(color='#ff6b6b', width=2),
                    fill='tonexty'
                ),
                row=1, col=1
            )
            
            # 습도 차트
            fig.add_trace(
                go.Scatter(
                    x=df_sensor['created_at'], 
                    y=df_sensor['humidity'],
                    name='습도',
                    line=dict(color='#4ecdc4', width=2),
                    fill='tonexty'
                ),
                row=2, col=1
            )
            
            # 조도 차트
            fig.add_trace(
                go.Scatter(
                    x=df_sensor['created_at'], 
                    y=df_sensor['light'],
                    name='조도',
                    line=dict(color='#ffe66d', width=2),
                    fill='tonexty'
                ),
                row=3, col=1
            )
            
            fig.update_layout(
                height=600,
                title_text="📈 센서 데이터 시계열 차트",
                showlegend=False
            )
            
            fig.update_xaxes(title_text="시간", row=3, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 센서 데이터에 대한 간단 댓글 시스템 (app.py 스타일)
            st.subheader("💭 센서 데이터 간단 댓글")
            
            if st.session_state.username_simple:
                # 댓글 작성
                with st.expander("✏️ 댓글 작성"):
                    content_simple = st.text_area("내용", placeholder="센서 데이터에 대한 의견을 남겨주세요!")
                    comment_type_simple = st.radio("유형", ["응원", "질문"])
                    
                    if st.button("등록"):
                        if content_simple.strip():
                            success, result = simple_supabase.insert('user_comments', {
                                "username": st.session_state.username_simple,
                                "content": content_simple,
                                "type": "comment" if comment_type_simple == "응원" else "question",
                                "created_at": datetime.now().isoformat()
                            })
                            if success:
                                st.success("댓글이 등록되었습니다!")
                                st.rerun()
                            else:
                                st.error(f"등록 실패: {result}")
                        else:
                            st.warning("내용을 입력해주세요.")
                
                # 최근 댓글들
                recent_comments = simple_supabase.select(
                    'user_comments',
                    order='created_at.desc',
                    limit=5
                )
                
                if recent_comments:
                    for comment in recent_comments:
                        icon = "💪" if comment['type'] == "comment" else "❓"
                        st.markdown(f"""
                        **{icon} {comment['username']}** - *{comment['created_at'][:16]}*
                        
                        {comment['content']}
                        
                        ---
                        """)
            else:
                st.info("댓글을 남기려면 사이드바에서 닉네임을 입력해주세요.")
        
        else:
            st.warning("🔭 센서 데이터가 없습니다. ESP8266이 정상적으로 데이터를 전송하고 있는지 확인해주세요.")
        
        st.markdown("---")

        # 자동 새로고침
        if auto_refresh:
            time.sleep(10)
            st.rerun()
    
    # =============================================================================
    # 하단: 커뮤니티 섹션 (member_bbs.py 기반)
    # =============================================================================
    
    if community_section:
        st.header("💬 커뮤니티")
        st.caption("센서 데이터에 대한 응원이나 궁금한 점을 자유롭게 나누어보세요!")
        
        # 시스템 현황 정보를 먼저 표시 (들여쓰기 수정)
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **📊 센서 모니터링 현황:**
            - ESP8266 기반 실시간 데이터 수집
            - 온도, 습도, 조도 모니터링
            - 시계열 차트로 트렌드 분석
            - 간단 댓글 시스템으로 즉석 소통
            """)
        
        with col2:
            st.info("""
            **💬 커뮤니티 현황:**  
            - 회원 기반 고급 댓글 시스템
            - 응원/질문 카테고리 분류
            - 답글 기능으로 심화 토론
            - 사용자 인증으로 신뢰성 확보
            """)
        if st.session_state.user:
            # 댓글/질문 작성
            with st.expander("✏️ 댓글 작성하기", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    content = st.text_area(
                        "내용", 
                        placeholder="예) 온도가 많이 올라갔네요! 식물이 괜찮을까요? 🌱",
                        height=100
                    )
                
                with col2:
                    comment_type = st.radio("유형", ["💪 응원", "❓ 질문"])
                    
                    if st.button("📝 등록하기", use_container_width=True):
                        if content.strip():
                            username = st.session_state.user.user_metadata.get('username', '익명')
                            success, error = add_comment(
                                st.session_state.user.id,
                                username,
                                content,
                                "comment" if comment_type == "💪 응원" else "question"
                            )
                            if success:
                                st.success("✅ 댓글이 등록되었습니다!")
                                st.rerun()
                            else:
                                st.error(f"⌫ 등록 실패: {error}")
                        else:
                            st.warning("⚠️ 내용을 입력해주세요.")

            # 댓글 목록 - 가독성 개선 버전
            comments = get_comments()

            if comments:
                st.subheader("💭 최근 댓글들")

                for comment in comments:
                    # 댓글 타입에 따른 아이콘
                    icon = "💪" if comment['type'] == "comment" else "❓"
                    type_text = "응원" if comment['type'] == "comment" else "질문"

                    with st.container():
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                            padding: 18px;
                            border-radius: 12px;
                            margin: 15px 0;
                            border-left: 5px solid {'#28a745' if comment['type'] == 'comment' else '#007bff'};
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                            border: 1px solid #e9ecef;
                        ">
                            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                <span style="
                                    font-weight: bold; 
                                    color: #212529;
                                    font-size: 16px;
                                ">
                                    {icon} {comment['username']}
                                </span>
                                <span style="
                                    background: {'#d4edda' if comment['type'] == 'comment' else '#cce7ff'};
                                    color: {'#155724' if comment['type'] == 'comment' else '#004085'};
                                    padding: 4px 12px;
                                    border-radius: 15px;
                                    font-size: 13px;
                                    font-weight: 600;
                                    margin-left: 12px;
                                    border: 1px solid {'#c3e6cb' if comment['type'] == 'comment' else '#b8daff'};
                                ">
                                    {type_text}
                                </span>
                                <span style="
                                    color: #6c757d; 
                                    font-size: 13px; 
                                    margin-left: auto;
                                    font-weight: 500;
                                ">
                                    {comment['created_at'][:16].replace('T', ' ')}
                                </span>
                            </div>
                            <div style="
                                color: #2c3e50;
                                line-height: 1.6;
                                font-size: 15px;
                                padding: 8px 0;
                                background: rgba(255,255,255,0.7);
                                padding: 12px;
                                border-radius: 8px;
                                border: 1px solid rgba(0,0,0,0.05);
                            ">
                                {comment['content']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # 답글 기능
                        with st.expander(f"💬 답글 ({len(get_replies(comment['id']))}개)", expanded=False):
                            # 기존 답글들 표시
                            replies = get_replies(comment['id'])
                            for reply in replies:
                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
                                    padding: 14px;
                                    margin: 8px 0;
                                    border-radius: 10px;
                                    border-left: 4px solid #6c757d;
                                    border: 1px solid #e9ecef;
                                    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
                                ">
                                    <div style="margin-bottom: 6px;">
                                        <strong style="color: #495057; font-size: 14px;">{reply['username']}</strong>
                                        <span style="
                                            color: #6c757d; 
                                            font-size: 12px; 
                                            margin-left: 10px;
                                            background: #f8f9fa;
                                            padding: 2px 6px;
                                            border-radius: 8px;
                                        ">
                                            {reply['created_at'][:16].replace('T', ' ')}
                                        </span>
                                    </div>
                                    <div style="
                                        margin-top: 8px;
                                        color: #2c3e50;
                                        line-height: 1.5;
                                        font-size: 14px;
                                        background: rgba(255,255,255,0.8);
                                        padding: 8px;
                                        border-radius: 6px;
                                    ">
                                        {reply['content']}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                            # 새 답글 작성
                            reply_content = st.text_input(
                                f"답글 작성",
                                key=f"reply_{comment['id']}",
                                placeholder="답글을 입력하세요...",
                                help="답글을 작성하고 Enter를 눌러주세요"
                            )

                            if st.button(f"답글 달기", key=f"reply_btn_{comment['id']}"):
                                if reply_content.strip():
                                    username = st.session_state.user.user_metadata.get('username', '익명')
                                    success, error = add_reply(
                                        comment['id'],
                                        st.session_state.user.id,
                                        username,
                                        reply_content
                                    )
                                    if success:
                                        st.success("답글이 등록되었습니다!")
                                        st.rerun()
                                    else:
                                        st.error(f"답글 등록 실패: {error}")
            else:
                st.info("💭 아직 댓글이 없습니다. 첫 번째 댓글을 남겨보세요!")

        else:
            st.info("💡 댓글을 남기려면 로그인이 필요합니다. 사이드바에서 로그인하거나 회원가입해주세요!")

            # 비로그인 사용자도 기존 댓글은 볼 수 있게
            comments = get_comments()
            if comments:
                st.subheader("💭 커뮤니티 댓글들")
                for comment in comments[:5]:  # 최근 5개만 표시
                    icon = "💪" if comment['type'] == "comment" else "❓"
                    type_text = "응원" if comment['type'] == "comment" else "질문"

                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                        padding: 15px;
                        border-radius: 10px;
                        margin: 12px 0;
                        border-left: 4px solid #dee2e6;
                        border: 1px solid #e9ecef;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
                    ">
                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                            <span style="font-weight: bold; color: #495057; font-size: 15px;">
                                {icon} {comment['username']}
                            </span>
                            <span style="
                                background: #e9ecef;
                                color: #495057;
                                padding: 3px 8px;
                                border-radius: 12px;
                                font-size: 12px;
                                font-weight: 600;
                                margin-left: 10px;
                                border: 1px solid #dee2e6;
                            ">
                                {type_text}
                            </span>
                        </div>
                        <div style="
                            color: #2c3e50;
                            line-height: 1.5;
                            font-size: 14px;
                            background: rgba(255,255,255,0.8);
                            padding: 10px;
                            border-radius: 6px;
                            border: 1px solid rgba(0,0,0,0.05);
                        ">
                            {comment['content']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # 자동 새로고침
    if sensor_section and auto_refresh:
        st.rerun()

    # 푸터
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>🌱 통합 센서 모니터링 & 커뮤니티 시스템 | 실시간 업데이트</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
