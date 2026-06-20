import streamlit as st
import re

# 세션 상태 초기화
if "page" not in st.session_state:
    st.session_state.page = "home"

st.set_page_config(page_title="서·논술형 자동 채점 시스템", layout="wide")

st.title("📝 중등 국어 서·논술형 자동 채점 및 피드백 시스템")
st.caption("다양한 설명 방법 및 매체의 복합양식성 평가 도구 (2회고사 대비 모의 문항)")

# 사이드바 메뉴 구성
set_choice = st.sidebar.selectbox(
    "💡 채점할 문항 세트를 선택하세요",
    ["1세트: 사회적 촉진과 억제", "2세트: 겨울철 불청객 정전기", "3세트: 음식과 삶의 태도 비유"]
)

# 동의어 및 핵심어 사전 정의 (로직 반영)
SYNONYMS = {
    "혼자": ["혼자", "홀로", "독립된", "스스로", "타인 없이", "단독"],
    "함께": ["함께", "같이", "모임", "도서관", "커피숍", "다른 사람"],
    "정지": ["정지", "멈춤", "고여 있는", "이동하지 않는", "움직이지 않는"],
    "음미": ["음미", "천천히", "여유", "깊이 있게", "살펴보는"]
}

def check_synonyms(text, key):
    """텍스트에 핵심어 또는 동의어가 포함되어 있는지 확인하는 함수"""
    return any(word in text for word in SYNONYMS.get(key, [key]))

# ==========================================
# 채점 엔진 함수 핵심 로직
# ==========================================
def score_set_1(q1_1, q1_2, q1_3, q2_1, q2_2, q3_si, q3_si_eff, q3_au, q3_au_eff):
    scores = {}
    feedbacks = {}
    
    # [서1] 표 빈칸 채우기 채점
    # (1) 쉬운 과제 의미 포함 여부
    if check_synonyms(q1_1, "함께") or any(x in q1_1 for x in ["쉬운", "친숙", "노력 없는"]):
        scores["서1-(1)"] = 2
        feedbacks["서1-(1)"] = "정확하게 요약되었습니다."
    else:
        scores["서1-(1)"] = 0
        feedbacks["서1-(1)"] = "과제의 특성(쉬운 과제, 친숙한 과목 등) 누락 또는 잘못된 환경 매칭입니다."
        
    # (2) 어려운 과제 해결 방식
    if check_synonyms(q1_2, "혼자") and ("집중" in q1_2 or "시간" in q1_2 or "익숙" in q1_2):
        scores["서1-(2)"] = 2
        feedbacks["서1-(2)"] = "정확하게 요약되었습니다."
    else:
        scores["서1-(2)"] = 0
        feedbacks["서1-(2)"] = "'혼자 차분히 집중한다'는 핵심 해결 방식이 누락되었습니다."
        
    # (3) 용어 확인 (공식 용어 필수)
    if "억제" in q1_3:
        scores["서1-(3)"] = 2
        feedbacks["서1-(3)"] = "공식 심리학 용어를 정확히 기술했습니다."
    elif "반대" in q1_3:
        scores["서1-(3)"] = 1
        feedbacks["서1-(3)"] = "맥락은 파악했으나 정확한 용어('사회적 억제')가 아닙니다. (부분 점수)"
    else:
        scores["서1-(3)"] = 0
        feedbacks["서1-(3)"] = "오답입니다. 정답은 '사회적 억제'입니다."

    # [서2] 설명문 작성 채점
    def score_q2_sentence(text, num_str):
        method_match = re.search(r'\(([^)]+)\)', text)
        if not method_match:
            return 0, f"({num_str}) 문장 끝에 설명 방법 명칭 괄호 표기 조건이 누락되었습니다."
        
        method = method_match.group(1).strip()
        clean_text = re.sub(r'\(.*?\)', '', text)
        
        # 오개념 및 결론 방향 체크
        if "쉬운" in clean_text and check_synonyms(clean_text, "혼자"):
            return 0, f"({num_str}) 오개념 오류: 쉬운 과제는 함께할 때 효율이 오릅니다."
        if "어려운" in clean_text and check_synonyms(clean_text, "함께"):
            return 0, f"({num_str}) 오개념 오류: 어려운 과제는 혼자 집중해야 합니다."
            
        # 설명 방법별 특성 양식 일치 확인
        if "예시" in method or "예" in method:
            if any(x in clean_text for x in ["예를 들어", "예로", "예컨대"]):
                return 4, f"({num_str}) [예시]의 특성을 살려 올바른 결론 문장을 작성했습니다."
            return 2, f"({num_str}) 내용 방향은 맞으나 '예를 들어' 등 예시 고유의 표현 형식이 부족합니다."
        elif "대조" in method or "비교" in method:
            if any(x in clean_text for x in ["반면", "다르게", "대조적으로", "와 달리"]):
                return 4, f"({num_str}) [대조]의 문장 구조로 차이점을 명확히 밝혔습니다."
            return 2, f"({num_str}) 내용 방향은 맞으나 대조를 나타내는 접속어나 조사 표현이 부족합니다."
        elif "인과" in method:
            if any(x in clean_text for x in ["때문에", "까닭에", "하므로", "결과"]):
                return 4, f"({num_str}) [인과]의 구조로 인과 관계를 명확히 작성했습니다."
            return 2, f"({num_str}) 원인과 결과의 연결 표현 형식이 미흡합니다."
        return 1, f"({num_str}) 지식 내용에 명시되지 않은 설명 방법 명칭({method})을 사용했습니다."

    scores["서2-(1)"], feedbacks["서2-(1)"] = score_q2_sentence(q2_1, "1")
    scores["서2-(2)"], feedbacks["서2-(2)"] = score_q2_sentence(q2_2, "2")
    
    if scores["서2-(1)"] > 0 and scores["서2-(2)"] > 0:
        m1 = re.search(r'\(([^)]+)\)', q2_1).group(1)
        m2 = re.search(r'\(([^)]+)\)', q2_2).group(1)
        if m1 == m2:
            scores["서2-(2)"] -= 1
            feedbacks["서2-(2)"] += " (경고: 문항 (1)과 (2)에 서로 다른 설명 방법을 써야 한다는 조건을 위반하여 감점됩니다.)"

    # [서3] 영상 기획 복합양식성 채점
    # 시각 연출 및 효과
    if check_synonyms(q3_si, "혼자"):
        if "환경" in q3_si_eff or "집중" in q3_si_eff or "전달" in q3_si_eff:
            scores["서3-시각"] = 3
            feedbacks["서3-시각"] = "시각 연출과 텍스트 의미 전달 효과의 인과가 우수합니다."
        else:
            scores["서3-시각"] = 1.5
            feedbacks["서3-시각"] = "시각 연출은 적절하나 효과 서술이 추상적입니다('집중이 잘 됨' 등)."
    else:
        scores["서3-시각"] = 0
        feedbacks["서3-시각"] = "어려운 과제 조건인 '혼자/차분함'의 시각 연출 방향이 잘못되었습니다."

    # 청각 연출 및 효과
    if any(x in q3_au for x in ["음악을 끄", "묵음", "조용한", "사각", "소리 제거"]):
        if "정적" in q3_au_eff or "몰입" in q3_au_eff or "집중" in q3_au_eff:
            scores["서3-청각"] = 3
            feedbacks["서3-청각"] = "청각 연출(복합양식성) 및 몰입 효과 분석이 완벽합니다."
        else:
            scores["서3-청각"] = 1.5
            feedbacks["서3-청각"] = "청각 기획은 맞으나 구체적인 청각 효과 서술이 부족합니다."
    else:
        scores["서3-청각"] = 0
        feedbacks["서3-청각"] = "어려운 과제의 분위기에 맞지 않는 소리 연출 기획입니다."
        
    return scores, feedbacks

# ==========================================
# 2세트 및 3세트 채점 함수도 동일한 논리 로직으로 구현
# ==========================================
def score_set_2(q1_1, q1_2, q1_3, q2_1, q2_2, q3_si, q3_si_eff, q3_au, q3_au_eff):
    scores = {}
    feedbacks = {}
    if "고여" in q1_1 and "물" in q1_1:
        scores["서1-(1)"] = 2; feedbacks["서1-(1)"] = "비유적 요약이 완벽합니다."
    else:
        scores["서1-(1)"] = 0; feedbacks["서1-(1)"] = "표의 기준인 '물에 비유' 형태가 아닙니다."
        
    if check_synonyms(q1_2, "정지"):
        scores["서1-(2)"] = 2; feedbacks["서1-(2)"] = "정확합니다."
    else:
        scores["서1-(2)"] = 0; feedbacks["서1-(2)"] = "전하가 이동하지 않고 멈춘 성질이 누락되었습니다."
        
    if "위험하지" in q1_3 or "피해" in q1_3:
        scores["서1-(3)"] = 2; feedbacks["서1-(3)"] = "정확합니다."
    else:
        scores["서1-(3)"] = 0; feedbacks["서1-(3)"] = "위험성 결론 서술 오류입니다."

    # 서2 정전기 설명문 양식 판별
    def score_q2_set2(text, num_str):
        method_match = re.search(r'\(([^)]+)\)', text)
        if not method_match: return 0, "괄호 표기 누락"
        m = method_match.group(1).strip()
        if "정의" in m and "현상을 말한다" in text: return 4, "[정의] 충족"
        if "대조" in m and "반면" in text: return 4, "[대조] 충족"
        if "비유" in m: return 0, "오류: '비유'는 1쪽에 제시된 정식 설명 방법 용어가 아닙니다."
        return 2, "의미 소통 가능하나 형식 미흡"
        
    scores["서2-(1)"], feedbacks["서2-(1)"] = score_q2_set2(q2_1, "1")
    scores["서2-(2)"], feedbacks["서2-(2)"] = score_q2_set2(q2_2, "2")
    
    # 서3 복합양식성 (댐, 고인 물 기획 매칭)
    if "고인" in q3_si or "멈춘" in q3_si or "댐" in q3_si:
        scores["서3-시각"] = 3; feedbacks["서3-시각"] = "비유적 시각 연출 통과."
    else:
        scores["서3-시각"] = 0; feedbacks["서3-시각"] = "고여 있는 물의 시각화 실패."
        
    if "조용한" in q3_au or "묵음" in q3_au or "없" in q3_au:
        scores["서3-청각"] = 3; feedbacks["서3-청각"] = "청각 연출 통과."
    else:
        scores["서3-청각"] = 0; feedbacks["서3-청각"] = "정적감 연출 실패."
        
    return scores, feedbacks

def score_set_3(q1_1, q1_2, q1_3, q2_1, q2_2, q3_si, q3_si_eff, q3_au, q3_au_eff):
    scores = {}
    feedbacks = {}
    
    # 서1 요약 채점
    if "느낄 수 없다" in q1_1 or "삼켜" in q1_1:
        scores["서1-(1)"] = 2; feedbacks["서1-(1)"] = "통과"
    else: scores["서1-(1)"] = 0; feedbacks["서1-(1)"] = "부정적 결과 오기"
        
    if "다르게" in q1_2 or "차이" in q1_2:
        scores["서1-(2)"] = 2; feedbacks["서1-(2)"] = "통과"
    else: scores["서1-(2)"] = 0; feedbacks["서1-(2)"] = "개인적 차이 누락"
        
    if check_synonyms(q1_3, "음미"):
        scores["서1-(3)"] = 2; feedbacks["서1-(3)"] = "통과"
    else: scores["서1-(3)"] = 0; feedbacks["서1-(3)"] = "필요한 태도 오류"

    # 서2 설명문
    if "비유" in q2_1 or "비유" in q2_2:
        scores["서2-오류"] = 0
        feedbacks["서2-통합"] = "감점: 1쪽 기준에 없는 '(비유)' 표기 유형입니다. 대조 또는 비교를 써야 합니다."
    else:
        scores["서2-통합"] = 6
        feedbacks["서2-통합"] = "설명 방법 조건 만족 문장형식 통과."

    # 서3 결론 방향성 검사 알고리즘 적용
    if "아름다움" in q3_si_eff or "다채로움" in q3_si_eff or "포착" in q3_si_eff:
        scores["서3-시각"] = 3; feedbacks["서3-시각"] = "요구한 결론 방향성 명확히 표현됨."
    else:
        scores["scores_서3-시각"] = 0
        feedbacks["서3-시각"] = "최종 결론(아름다움 포착 가치) 서술이 누락되었습니다."
        
    scores["서3-청각"] = 3 if "여유" in q3_au_eff or "편안" in q3_au_eff else 0
    feedbacks["서3-청각"] = "청각 연출 통과" if scores["서3-청각"] == 3 else "청각 효과가 미흡합니다."
    
    return scores, feedbacks


# ==========================================
# 화면 레이아웃 및 폼 렌더링 영역
# ==========================================
st.subheader(f"📋 학생 답안 작성 및 입력 란 - [{set_choice}]")

if set_choice == "1세트: 사회적 촉진과 억제":
    st.info("💡 모범 선택지 가이드: 서2 문항 끝에반드시 (예시), (대조) 등의 정식 설명 용어를 기술해야 통과됩니다.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        q1_1 = st.text_input("서1-(1) 빈칸 입력", placeholder="예시: 쉬운 취미 생활 과제")
    with col2:
        q1_2 = st.text_input("서1-(2) 빈칸 입력", placeholder="예시: 차분하게 혼자 집중하는 시간을 가짐")
    with col3:
        q1_3 = st.text_input("서1-(3) 빈칸 입력", placeholder="예시: 사회적 억제")
        
    st.divider()
    q2_1 = st.text_area("서2 문항 (1) 답안 문장 입력", placeholder="문장 끝에 (설명방법) 표기 필수\n예: 예를 들어 쉬운 과제는 도서관에서 함께 하는 것이 좋습니다. (예시)")
    q2_2 = st.text_area("서2 문항 (2) 답안 문장 입력", placeholder="예: 반면 지나치게 어려운 과제는 혼자 집중해야 능률이 오릅니다. (대조)")
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        q3_si = st.text_input("서3 (1) 시각 요소(Ⓐ) 연출 계획", placeholder="예: 혼자 조용히 방에서 공부하는 모습")
        q3_si_eff = st.text_area("시각 요소(Ⓐ)의 효과 서술", placeholder="예: 혼자 집중하는 환경을 직관적으로 전달한다.")
    with c2:
        q3_au = st.text_input("서3 (2) 청각 요소(Ⓑ) 연출 계획", placeholder="예: 모든 배경음악을 끄고 사각거리는 필기 소리만 배치")
        q3_au_eff = st.text_area("청각 요소(Ⓑ)의 효과 서술", placeholder="예: 깊은 몰입감과 차분한 분위기를 극대화한다.")

    if st.button("🚀 자동 채점 실행"):
        sc, fb = score_set_1(q1_1, q1_2, q1_3, q2_1, q2_2, q3_si, q3_si_eff, q3_au, q3_au_eff)
        
        st.success("🎯 채점 결과 분석 리포트")
        total_score = sum(sc.values())
        st.metric(label="총점 / 만점 (20점)", value=f"{total_score}점")
        
        for key in sc.keys():
            st.write(f"**[{key}]** 배점 결과: `{sc[key]}점` ➔ {fb[key]}")

elif set_choice == "2세트: 겨울철 불청객 정전기":
    col1, col2, col3 = st.columns(3)
    with col1: q1_1 = st.text_input("서1-(1) 물의 비유 빈칸", placeholder="예시: 높은 곳에 고여 있는 물")
    with col2: q1_2 = st.text_input("서1-(2) 전하 상태 빈칸", placeholder="예시: 전하가 이동하지 않고 머물러 있음")
    with col3: q1_3 = st.text_input("서1-(3) 위험성 빈칸", placeholder="예시: 위험하지 않음")
    
    q2_1 = st.text_area("서2 문항 (1) 답안 문장", placeholder="예시 형태 기술...")
    q2_2 = st.text_area("서2 문항 (2) 답안 문장", placeholder="예시 형태 기술...")
    
    q3_si = st.text_input("서3 시각 연출 계획")
    q3_si_eff = st.text_area("시각 효과 서술")
    q3_au = st.text_input("서3 청각 연출 계획")
    q3_au_eff = st.text_area("청각 효과 서술")
    
    if st.button("🚀 자동 채점 실행"):
        sc, fb = score_set_2(q1_1, q1_2, q1_3, q2_1, q2_2, q3_si, q3_si_eff, q3_au, q3_au_eff)
        st.success(f"🎯 총점: {sum(sc.values())}점")
        for key in sc.keys(): st.write(f"**[{key}]**: {fb[key]} ({sc[key]}점)")

else: # 3세트
    q1_1 = st.text_input("서1-ⓒ 빈칸")
    q1_2 = st.text_input("서1-ⓓ 빈칸")
    q1_3 = st.text_input("서1-ⓔ 빈칸")
    q2_1 = st.text_area("서2 문항 (1)")
    q2_2 = st.text_area("서2 문항 (2)")
    q3_si = st.text_input("서3 시각 연출")
    q3_si_eff = st.text_area("시각 효과(최종 결론 방향성 검증)")
    q3_au = st.text_input("서3 청각 연출")
    q3_au_eff = st.text_area("청각 효과")
    
    if st.button("🚀 자동 채점 실행"):
        sc, fb = score_set_3(q1_1, q1_2, q1_3, q2_1, q2_2, q3_si, q3_si_eff, q3_au, q3_au_eff)
        st.success(f"🎯 총점: {sum(sc.values())}점")
        for key in sc.keys(): st.write(f"**[{key}]**: {fb[key]} ({sc[key]}점)")