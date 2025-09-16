# 센서 모니터링 + 회원제 댓글 시스템 (maintable2 기반)
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Supabase 설정
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# 1. 사용자 인증 함수들
def sign_up(email, password, username):
    try:
        response = supabase.auth.sign_up({
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
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response.user, None
    except Exception as e:
        return None, str(e)

def sign_out():
    supabase.auth.sign_out()

# 2. 센서 데이터 조회 (maintable2에서)
def get_sensor_data(hours=24):
    try:
        # 최근 N시간의 센서 데이터 조회
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        response = supabase.table('maintable2').select(
            "id, created_at, light, temperature, humidity"
        ).gte(
            'created_at', start_time.isoformat()
        ).order('created_at', desc=True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"센서 데이터 조회 오류: {e}")
        return pd.DataFrame()

# 3. 댓글/질문 관련 함수들
def add_comment(user_id, username, content, comment_type="comment"):
    try:
        data = {
            "user_id": user_id,
            "username": username,
            "content": content,
            "type": comment_type,  # "comment" 또는 "question"
            "created_at": datetime.now().isoformat()
        }
        
        response = supabase.table('user_comments').insert(data).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def get_comments():
    try:
        response = supabase.table('user_comments').select("*").order(
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
        
        response = supabase.table('comment_replies').insert(data).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def get_replies(comment_id):
    try:
        response = supabase.table('comment_replies').select("*").eq(
            'comment_id', comment_id
        ).order('created_at', desc=False).execute()
        return response.data
    except Exception as e:
        return []

# 4. 센서 데이터 통계
def get_sensor_stats(df):
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

# 5. 메인 앱
def main():
    st.set_page_config(
        page_title="🌱 센서 모니터링 & 커뮤니티", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 세션 상태 초기화
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # 사이드바 - 인증
    with st.sidebar:
        st.title("🔐 사용자 인증")
        
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
            st.caption("💡 로그인하면 댓글과 질문을 남길 수 있습니다!")
    
    # 메인 콘텐츠
    st.title("🌱 센서 모니터링 & 커뮤니티")
    st.caption("ESP8266으로 수집한 환경 데이터를 실시간으로 모니터링하고 커뮤니티와 소통하세요!")
    
    # 센서 데이터 섹션
    st.header("📊 실시간 센서 데이터")
    
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
        if st.button("🔄 데이터 새로고침"):
            st.rerun()
    
    # 센서 데이터 조회
    with st.spinner("센서 데이터를 불러오는 중..."):
        df = get_sensor_data(hours)
    
    if not df.empty:
        # 현재 상태 표시
        stats = get_sensor_stats(df)
        
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
                f"{len(df)}개",
                delta=f"마지막 업데이트: {df.iloc[0]['created_at'].strftime('%H:%M:%S')}"
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
                x=df['created_at'], 
                y=df['temperature'],
                name='온도',
                line=dict(color='#ff6b6b', width=2),
                fill='tonexty'
            ),
            row=1, col=1
        )
        
        # 습도 차트
        fig.add_trace(
            go.Scatter(
                x=df['created_at'], 
                y=df['humidity'],
                name='습도',
                line=dict(color='#4ecdc4', width=2),
                fill='tonexty'
            ),
            row=2, col=1
        )
        
        # 조도 차트
        fig.add_trace(
            go.Scatter(
                x=df['created_at'], 
                y=df['light'],
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
        
        # 데이터 테이블 (접기 가능)
        with st.expander("📋 상세 데이터 보기"):
            st.dataframe(
                df[['created_at', 'temperature', 'humidity', 'light']].rename(columns={
                    'created_at': '측정 시간',
                    'temperature': '온도(°C)',
                    'humidity': '습도(%)',
                    'light': '조도'
                }),
                use_container_width=True
            )
    
    else:
        st.warning("📭 센서 데이터가 없습니다. ESP8266이 정상적으로 데이터를 전송하고 있는지 확인해주세요.")
    
    st.divider()
    
    # 커뮤니티 섹션
    st.header("💬 커뮤니티")
    st.caption("센서 데이터에 대한 응원이나 궁금한 점을 자유롭게 나눠보세요!")
    
    if st.session_state.user:
        # 댓글/질문 작성
        with st.expander("✍️ 댓글 작성하기", expanded=False):
            col1, col2 = st.columns([3, 1])
            
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
                            st.error(f"❌ 등록 실패: {error}")
                    else:
                        st.warning("⚠️ 내용을 입력해주세요.")
        
        # 댓글 목록
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
                        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
                        padding: 15px;
                        border-radius: 10px;
                        margin: 10px 0;
                        border-left: 4px solid {'#28a745' if comment['type'] == 'comment' else '#007bff'};
                    ">
                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                            <span style="font-weight: bold; color: #495057;">
                                {icon} {comment['username']}
                            </span>
                            <span style="
                                background: {'#d4edda' if comment['type'] == 'comment' else '#cce7ff'};
                                color: {'#155724' if comment['type'] == 'comment' else '#004085'};
                                padding: 2px 8px;
                                border-radius: 12px;
                                font-size: 12px;
                                margin-left: 10px;
                            ">
                                {type_text}
                            </span>
                            <span style="color: #6c757d; font-size: 12px; margin-left: auto;">
                                {comment['created_at'][:16].replace('T', ' ')}
                            </span>
                        </div>
                        <div style="color: #212529; line-height: 1.5;">
                            {comment['content']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 답글 기능 (간단하게)
                    with st.expander(f"💬 답글 ({len(get_replies(comment['id']))}개)"):
                        # 기존 답글들 표시
                        replies = get_replies(comment['id'])
                        for reply in replies:
                            st.markdown(f"""
                            <div style="
                                background: #ffffff;
                                padding: 10px;
                                margin: 5px 0;
                                border-radius: 8px;
                                border-left: 3px solid #6c757d;
                            ">
                                <strong>{reply['username']}</strong>
                                <span style="color: #6c757d; font-size: 12px; margin-left: 10px;">
                                    {reply['created_at'][:16].replace('T', ' ')}
                                </span>
                                <div style="margin-top: 5px;">{reply['content']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # 새 답글 작성
                        reply_content = st.text_input(
                            f"답글 작성", 
                            key=f"reply_{comment['id']}",
                            placeholder="답글을 입력하세요..."
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
                    background: #f8f9fa;
                    padding: 10px;
                    border-radius: 8px;
                    margin: 8px 0;
                    border-left: 3px solid #dee2e6;
                ">
                    <div style="display: flex; align-items: center; margin-bottom: 5px;">
                        <span><strong>{icon} {comment['username']}</strong></span>
                        <span style="
                            background: #e9ecef;
                            padding: 2px 6px;
                            border-radius: 10px;
                            font-size: 11px;
                            margin-left: 8px;
                        ">{type_text}</span>
                    </div>
                    <div>{comment['content']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # 자동 새로고침
    if auto_refresh:
        st.rerun()

# 앱 실행
if __name__ == "__main__":
    main()

# Supabase 테이블 설계 가이드
"""
추가로 필요한 테이블들:

1. user_comments 테이블:
   - id (bigint, primary key)
   - user_id (uuid, 사용자 ID)
   - username (text, 사용자명)
   - content (text, 댓글 내용)
   - type (text, 'comment' 또는 'question')
   - created_at (timestamp with time zone)

2. comment_replies 테이블:
   - id (bigint, primary key)
   - comment_id (bigint, 댓글 ID 참조)
   - user_id (uuid, 사용자 ID)
   - username (text, 사용자명)
   - content (text, 답글 내용)
   - created_at (timestamp with time zone)

SQL 생성 명령어:
```sql
-- 댓글 테이블
CREATE TABLE user_comments (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    username TEXT NOT NULL,
    content TEXT NOT NULL,
    type TEXT CHECK (type IN ('comment', 'question')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 답글 테이블
CREATE TABLE comment_replies (
    id BIGSERIAL PRIMARY KEY,
    comment_id BIGINT REFERENCES user_comments(id) ON DELETE CASCADE,
    user_id UUID,
    username TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 추가
CREATE INDEX idx_comments_created_at ON user_comments(created_at DESC);
CREATE INDEX idx_replies_comment_id ON comment_replies(comment_id);
```
"""