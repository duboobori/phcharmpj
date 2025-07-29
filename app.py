import streamlit as st
from firebase_admin import credentials, firestore, initialize_app, storage
import pandas as pd
import tempfile
import os, json

# Firebase 초기화 (Streamlit 실행 시 최초 1회만)
if "firebase_initialized" not in st.session_state:
    firebase_key = json.loads(os.environ["FIREBASE_KEY"])
    cred = credentials.Certificate("firebase_key.json")  # 비공개 키 파일 필요
    initialize_app(cred, {'storageBucket': 'class-recorder-7d71c.firebasestorage.app'})
    st.session_state["firebase_initialized"] = True

db = firestore.client()

# ---------- 화면 구분 ----------
menu = st.sidebar.selectbox("메뉴 선택", [
    "관리 교과 등록",
    "교과 목록 조회",
    "수업 등록",
    "학생 등록",
    "진도 기록",
    "출결 기록"
])

# ---------- 관리 교과 등록 ----------
if menu == "관리 교과 등록":
    st.subheader("관리 교과 등록")
    col1, col2 = st.columns(2)
    with col1:
        subject_name = st.text_input("교과명")
        year = st.selectbox("학년도", list(range(2020, 2031)))
    with col2:
        semester = st.selectbox("학기", [1, 2])
        pdf_file = st.file_uploader("수업 및 평가계획서(PDF, 10MB 이내)", type="pdf")

    if st.button("저장"):
        if subject_name and pdf_file:
            file_path = f"plans/{subject_name}_{year}_{semester}.pdf"
            bucket = storage.bucket()
            blob = bucket.blob(file_path)
            blob.upload_from_file(pdf_file, content_type='application/pdf')
            url = blob.public_url

            db.collection("subjects").add({
                "subject_name": subject_name,
                "year": year,
                "semester": semester,
                "pdf_url": url
            })
            st.success("교과가 등록되었습니다.")
        else:
            st.warning("모든 항목을 입력해주세요.")

# ---------- 교과 목록 조회 ----------
elif menu == "교과 목록 조회":
    st.subheader("교과 목록 조회")
    subjects = db.collection("subjects").stream()
    data = []
    for doc in subjects:
        d = doc.to_dict()
        d["id"] = doc.id
        data.append(d)
    df = pd.DataFrame(data)
    if not df.empty:
        st.dataframe(df[["subject_name", "year", "semester"]])
        selected = st.selectbox("PDF 보기", df["subject_name"])
        link = df[df["subject_name"] == selected]["pdf_url"].values[0]
        st.markdown(f"[PDF 보기]({link})", unsafe_allow_html=True)
    else:
        st.info("등록된 교과가 없습니다.")

# ---------- 수업 등록 ----------
elif menu == "수업 등록":
    st.subheader("수업 등록")
    year = st.selectbox("학년도", list(range(2020, 2031)))
    semester = st.selectbox("학기", [1, 2])
    subjects = db.collection("subjects").where("year", "==", year).where("semester", "==", semester).stream()
    subject_options = [doc.to_dict()["subject_name"] for doc in subjects]
    subject = st.selectbox("교과 선택", subject_options)
    class_name = st.text_input("학반(예: 1-1)")
    weekday = st.selectbox("요일", ["월", "화", "수", "목", "금"])
    periods = st.multiselect("수업 교시", list(range(1, 8)))

    if st.button("수업 저장"):
        if subject and class_name and periods:
            db.collection("classes").add({
                "year": year,
                "semester": semester,
                "subject": subject,
                "class_name": class_name,
                "weekday": weekday,
                "periods": periods
            })
            st.success("수업이 저장되었습니다.")
        else:
            st.warning("모든 항목을 입력하세요.")

# ---------- 학생 등록 ----------
elif menu == "학생 등록":
    st.subheader("학생 등록")
    class_name = st.text_input("수업반 (예: 1-1)")
    mode = st.radio("등록 방식", ["CSV 업로드", "직접 입력"])

    if mode == "CSV 업로드":
        file = st.file_uploader("CSV 파일 업로드 (반, 번호, 이름)", type=["csv"])
        if file:
            df = pd.read_csv(file)
            for _, row in df.iterrows():
                student_id = f"{row['반']:01d}{int(row['번호']):02d}"
                db.collection("students").add({
                    "class_name": class_name,
                    "student_id": student_id,
                    "name": row['이름']
                })
            st.success("학생 명단이 등록되었습니다.")

    else:
        name = st.text_input("학생 이름")
        sid = st.text_input("학번 (5자리)")
        if st.button("학생 추가"):
            db.collection("students").add({
                "class_name": class_name,
                "student_id": sid,
                "name": name
            })
            st.success("학생이 추가되었습니다.")

# ---------- 진도 기록 ----------
elif menu == "진도 기록":
    st.subheader("진도 기록")
    class_name = st.text_input("수업반")
    date = st.date_input("일자")
    period = st.selectbox("교시", list(range(1, 8)))
    content = st.text_area("진도 내용")
    note = st.text_area("특기사항")

    if st.button("기록 저장"):
        db.collection("progress").add({
            "class_name": class_name,
            "date": date.strftime("%Y-%m-%d"),
            "period": period,
            "content": content,
            "note": note
        })
        st.success("진도 기록이 저장되었습니다.")

# ---------- 출결 기록 ----------
elif menu == "출결 기록":
    st.subheader("출결 기록")
    class_name = st.text_input("수업반")
    date = st.date_input("일자")
    student_name = st.text_input("학생 이름")
    attendance_type = st.selectbox("출결 종류", ["출석", "지각", "조퇴", "결석"])

    justification = None
    if attendance_type in ["지각", "조퇴", "결석"]:
        justification = st.selectbox("인정 유형", ["인정", "병", "미인정"])

    result_periods = st.multiselect("해당 교시", list(range(1, 8)))
    note = st.text_area("특기사항")

    if st.button("출결 저장"):
        record = {
            "class_name": class_name,
            "date": date.strftime("%Y-%m-%d"),
            "student_name": student_name,
            "attendance_type": attendance_type,
            "periods": result_periods,
            "note": note
        }
        if justification:
            record["justification"] = justification

        db.collection("attendance").add(record)
        st.success("출결 정보가 저장되었습니다.")
