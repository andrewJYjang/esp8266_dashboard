import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib

# 페이지 설정
st.set_page_config(
    page_title="학습 커뮤니티",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'users' not in st.session_state:
    st.session_state.users = {
        'teacher@school.com': {'name': '선생님', 'password': 'teacher123', 'role': 'teacher'},
        'student1@school.com': {'name': '김학생', 'password': 'student123', 'role': 'student'},
        'student2@school.com': {'name': '이학생', 'password': 'student123', 'role': 'student'}
    }

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'posts' not in st.session_state:
    st.session_state.posts = {
        'learning': [
            {
                'id': 1,
                'title': 'ESP8266 센서 연결 질문',
                'content': 'DHT11 센서가 제대로 읽히지 않아요. 코드를 확인해주세요!\n\n```python\nimport dht\nd = dht.DHT11(Pin(2))\nd.measure()\nprint(d.temperature())\n```',
                'author': '김학생',
                'timestamp': '2024-03-15 14:30',
                'replies': []
            },
            {
                'id': 2,
                'title': 'Supabase 연결 성공했어요!',
                'content': '드디어 센서 데이터가 클라우드에 올라갑니다! 🎉\n\n처음엔 API 키 설정에서 막혔는데, 환경변수로 설정하니까 바로 되네요.',
                'author': '이학생',
                'timestamp': '2024-03-15 13:20',
                'replies': [
                    {'author': '선생님', 'content': '축하합니다! 정말 잘 하셨네요 👏', 'timestamp': '2024-03-15 13:30'}
                ]
            }
        ],
        'free': [
            {
                'id': 3,
                'title': '점심 뭐 먹을까요?',
                'content': '학교 앞 맛집 추천 부탁드려요! 🍜',
                'author': '김학생',
                'timestamp': '2024-03-15 12:00',
                'replies': [
                    {'author': '이학생', 'content': '김치찌개집 강추! 양도 많고 맛있어요', 'timestamp': '2024-03-15 12:05'},
                    {'author': '선생님', 'content': '학교 식당도 나쁘지 않아요 ㅎㅎ', 'timestamp': '2024-03-15 12:10'}
                ]
            }
        ],
        'tech': [
            {
                'id': 4,
                'title': 'Streamlit 차트가 안 나와요',
                'content': 'st.line_chart()를 써도 그래프가 나오지 않습니다. 😢\n\n데이터프레임 형태는 맞는 것 같은데...',
                'author': '김학생',
                'timestamp': '2024-03-15 15:45',
                'replies': [
                    {'author': '선생님', 'content': '데이터프레임 구조를 한번 확인해보세요. st.write(df)로 출력해보시길!', 'timestamp': '2024-03-15 15:50'}
                ]
            }
        ],
        'project': [
            {
                'id': 5,
                'title': '스마트팜 프로젝트 진행상황',
                'content': '온실 모니터링 시스템 1차 완성했습니다! 🌱\n\n- 온습도 센서 ✅\n- 조도 센서 ✅\n- 데이터 저장 ✅\n- 대시보드 ✅\n\n다음은 자동 급수 시스템을 만들어볼 예정입니다.',
                'author': '이학생',
                'timestamp': '2024-03-15 16:20',
                'replies': [
                    {'author': '선생님', 'content': '정말 대단합니다! 자동화까지 구현하면 완벽한 시스템이 되겠네요', 'timestamp': '2024-03-15 16:25'},
                    {'author': '김학생', 'content': '저도 따라해보고 싶어요! 코드 공유 가능한가요?', 'timestamp': '2024-03-15 16:30'}
                ]
            }
        ]
    }

# 게시판 설정
BOARDS = {
    'learning': {'name': '📚 학습 게시판', 'description': '과제, 자료공유, Q&A'},
    'free': {'name': '💬 자유 게시판', 'description': '일상소통, 아이디어, 잡담'},
    'tech': {'name': '🔧 기술 게시판', 'description': '코딩질문, 오류해결, 팁'},
    'project': {'name': '📊 프로젝트 게시판', 'description': '진행상황, 결과물, 협업'}
}

def hash_password(password):
    """비밀번호 해싱"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_page():
    """로그인/회원가입 페이지"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>🎓 학습 커뮤니티</h1>
        <p>센서 프로젝트 & 코딩 학습 공간</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 로그인", "👤 회원가입"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("로그인")
            email = st.text_input("이메일", placeholder="example@school.com")
            password = st.text_input("비밀번호", type="password", placeholder="••••••••")
            
            if st.form_submit_button("로그인", use_container_width=True):
                if email in st.session_state.users:
                    if st.session_state.users[email]['password'] == password:
                        st.session_state.current_user = {
                            'email': email,
                            'name': st.session_state.users[email]['name'],
                            'role': st.session_state.users[email]['role']
                        }
                        st.success(f"환영합니다, {st.session_state.users[email]['name']}님!")
                        st.rerun()
                    else:
                        st.error("비밀번호가 잘못되었습니다.")
                else:
                    st.error("존재하지 않는 이메일입니다.")
    
    with tab2:
        with st.form("signup_form"):
            st.subheader("회원가입")
            name = st.text_input("이름", placeholder="홍길동")
            email = st.text_input("이메일", placeholder="example@school.com")
            password = st.text_input("비밀번호", type="password", placeholder="••••••••")
            confirm_password = st.text_input("비밀번호 확인", type="password", placeholder="••••••••")
            
            if st.form_submit_button("회원가입", use_container_width=True):
                if not all([name, email, password, confirm_password]):
                    st.error("모든 필드를 입력해주세요.")
                elif password != confirm_password:
                    st.error("비밀번호가 일치하지 않습니다.")
                elif email in st.session_state.users:
                    st.error("이미 존재하는 이메일입니다.")
                else:
                    st.session_state.users[email] = {
                        'name': name,
                        'password': password,
                        'role': 'student'
                    }
                    st.success("회원가입이 완료되었습니다! 로그인해주세요.")
    
    # 테스트 계정 안내
    st.markdown("---")
    st.info("**테스트 계정:**\n- teacher@school.com / teacher123 (선생님)\n- student1@school.com / student123 (김학생)")

def main_page():
    """메인 게시판 페이지"""
    # 헤더
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🎓 학습 커뮤니티")
        st.caption("센서 프로젝트 & 코딩 학습")
    
    with col2:
        st.markdown(f"**{st.session_state.current_user['name']}** ({st.session_state.current_user['role']})")
        if st.button("🚪 로그아웃", use_container_width=True):
            st.session_state.current_user = None
            st.rerun()
    
    # 사이드바 - 게시판 선택
    with st.sidebar:
        st.header("📋 게시판 목록")
        
        board_choice = st.radio(
            "",
            options=list(BOARDS.keys()),
            format_func=lambda x: BOARDS[x]['name'],
            key="board_choice"
        )
        
        st.markdown("---")
        st.subheader("👥 접속중인 사용자")
        online_users = ['선생님', '김학생', '이학생']
        for user in online_users:
            st.markdown(f"🟢 {user}")
    
    # 메인 컨텐츠
    current_board = BOARDS[board_choice]
    
    st.header(current_board['name'])
    st.caption(current_board['description'])
    
    # 탭 구성
    tab1, tab2 = st.tabs(["📝 게시글 목록", "✏️ 글쓰기"])
    
    with tab1:
        # 검색
        search_term = st.text_input("🔍 검색", placeholder="제목 또는 내용으로 검색...")
        
        # 게시글 목록
        posts = st.session_state.posts.get(board_choice, [])
        
        if search_term:
            posts = [p for p in posts if search_term.lower() in p['title'].lower() or search_term.lower() in p['content'].lower()]
        
        if not posts:
            st.info("아직 게시글이 없습니다. 첫 번째 게시글을 작성해보세요!")
        else:
            for post in sorted(posts, key=lambda x: x['id'], reverse=True):
                with st.container():
                    st.markdown(f"### {post['title']}")
                    st.markdown(f"**작성자:** {post['author']} | **작성시간:** {post['timestamp']} | **댓글:** {len(post['replies'])}")
                    
                    # 내용 미리보기 (100자 제한)
                    preview = post['content'][:100] + "..." if len(post['content']) > 100 else post['content']
                    st.markdown(preview)
                    
                    # 상세보기/댓글 버튼
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("📖 상세보기", key=f"detail_{post['id']}"):
                            st.session_state.selected_post = post['id']
                    
                    st.markdown("---")
        
        # 선택된 게시글 상세보기
        if 'selected_post' in st.session_state:
            selected_post = None
            for post in posts:
                if post['id'] == st.session_state.selected_post:
                    selected_post = post
                    break
            
            if selected_post:
                st.markdown("## 📖 게시글 상세")
                
                if st.button("⬅️ 목록으로 돌아가기"):
                    del st.session_state.selected_post
                    st.rerun()
                
                st.markdown(f"# {selected_post['title']}")
                st.markdown(f"**작성자:** {selected_post['author']} | **작성시간:** {selected_post['timestamp']}")
                st.markdown("---")
                st.markdown(selected_post['content'])
                
                # 댓글 섹션
                st.markdown("## 💬 댓글")
                
                # 댓글 작성
                with st.form(f"comment_form_{selected_post['id']}"):
                    new_comment = st.text_area("댓글을 입력하세요...", height=100)
                    if st.form_submit_button("💬 댓글 작성"):
                        if new_comment.strip():
                            comment = {
                                'author': st.session_state.current_user['name'],
                                'content': new_comment,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                            }
                            
                            # 게시글 찾아서 댓글 추가
                            for board_posts in st.session_state.posts.values():
                                for post in board_posts:
                                    if post['id'] == selected_post['id']:
                                        post['replies'].append(comment)
                                        break
                            
                            st.success("댓글이 등록되었습니다!")
                            st.rerun()
                        else:
                            st.error("댓글 내용을 입력해주세요.")
                
                # 댓글 목록
                if selected_post['replies']:
                    for reply in selected_post['replies']:
                        with st.container():
                            st.markdown(f"**{reply['author']}** *{reply['timestamp']}*")
                            st.markdown(f"*{reply['content']}*")
                            st.markdown("---")
                else:
                    st.info("아직 댓글이 없습니다. 첫 번째 댓글을 작성해보세요!")
    
    with tab2:
        # 글쓰기 폼
        with st.form("post_form"):
            st.subheader("새 게시글 작성")
            
            post_title = st.text_input("제목", placeholder="제목을 입력하세요")
            post_content = st.text_area("내용", height=300, placeholder="내용을 입력하세요")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                submit_button = st.form_submit_button("📝 게시글 등록", use_container_width=True)
            with col2:
                if st.form_submit_button("🗑️ 초기화", use_container_width=True):
                    st.rerun()
            
            if submit_button:
                if not post_title.strip():
                    st.error("제목을 입력해주세요.")
                elif not post_content.strip():
                    st.error("내용을 입력해주세요.")
                else:
                    # 새 게시글 ID 생성
                    all_posts = []
                    for board_posts in st.session_state.posts.values():
                        all_posts.extend(board_posts)
                    new_id = max([p['id'] for p in all_posts], default=0) + 1
                    
                    new_post = {
                        'id': new_id,
                        'title': post_title,
                        'content': post_content,
                        'author': st.session_state.current_user['name'],
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'replies': []
                    }
                    
                    if board_choice not in st.session_state.posts:
                        st.session_state.posts[board_choice] = []
                    
                    st.session_state.posts[board_choice].append(new_post)
                    
                    st.success("게시글이 등록되었습니다!")
                    st.balloons()
                    
                    # 폼 초기화를 위해 페이지 새로고침
                    st.rerun()

# 메인 실행
def main():
    if st.session_state.current_user is None:
        login_page()
    else:
        main_page()

if __name__ == "__main__":
    main()