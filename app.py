import streamlit as st

# 페이지 제목
st.title("🧪 Streamlit 테스트 페이지")

# 사이드바 메뉴
st.sidebar.header("메뉴")
option = st.sidebar.selectbox("원하는 기능을 선택하세요:", (
    "인사말 출력",
    "숫자 입력 및 제곱 계산",
    "파일 업로드"
))

# 기능 1: 인사말 출력
if option == "인사말 출력":
    name = st.text_input("이름을 입력하세요:", "홍길동")
    if st.button("인사하기"):
        st.success(f"안녕하세요, {name}님! Streamlit에 오신 것을 환영합니다! 🎉")

# 기능 2: 숫자 입력 및 제곱 계산
elif option == "숫자 입력 및 제곱 계산":
    num = st.number_input("숫자를 입력하세요", value=0)
    if st.button("제곱 계산"):
        st.write(f"{num}의 제곱은 {num ** 2}입니다.")

# 기능 3: 파일 업로드
elif option == "파일 업로드":
    uploaded_file = st.file_uploader("파일을 업로드하세요")
    if uploaded_file is not None:
        st.write("파일 이름:", uploaded_file.name)
        st.write("파일 타입:", uploaded_file.type)
        st.write("파일 크기:", uploaded_file.size, "bytes")

        # 텍스트 파일인 경우 내용 출력
        if uploaded_file.type.startswith("text"):
            content = uploaded_file.read().decode("utf-8")
            st.text_area("파일 내용:", content, height=300)
