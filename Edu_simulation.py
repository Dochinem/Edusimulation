import streamlit as st
import pandas as pd
from datetime import datetime
import io
import time

# ==============================================================================
# 0. 규제 근거 로딩 및 매핑 함수 (규제 근거 파일 및 DI/GAMP 로직 통합)
# ==============================================================================

def load_regulatory_data(snippet_path='regulatory_snippets.txt'):
    """
    regulatory_snippets.txt 파일을 로드하여 규제 코드와 내용을 매핑하고,
    미리 정의된 번역 및 DI/GAMP 원칙을 통합하여 하나의 딕셔너리로 반환합니다.
    """
    snippets = {}
    
    # 1. 원문 및 번역 데이터 정의 (Module 1에서 사용 및 모듈 2, 3에 필요한 보강 데이터)
    translations = {
        "PIC/S_R2": "원본 데이터는 종이에 기록되었거나 전자적으로 기록된 정보의 첫 번째 획득으로 설명할 수 있는 원본 기록(데이터)으로 정의된다. 원래 동적 상태에서 획득한 정보는 해당 상태에서 계속 사용할 수 있어야 한다.",
        "A22_8": "AI 모델의 출력은 설명 가능해야 합니다. 이는 AI 모델이 주어진 출력에 어떻게 도달했는지 설명할 수 있어야 함을 의미합니다.",
        "P11_300": "식별 코드와 암호 발행은 주기적으로 점검, 회수 또는 개정되어야 합니다 (예: 암호 유효 기간 만료와 같은 이벤트를 다루기 위함).",
        
        # --- FDA WL 기반 신규 케이스 규제 근거 추가 ---
        "P11_10_B": "회사는 전자 기록 및 서명의 진위, 무결성 그리고 적절한 경우 **기밀성**을 보장하도록 설계된 절차 및 통제를 적용해야 합니다. (21 CFR Part 11)",
        "21_CFR_211_194_A": "시험소 기록에는 설정된 규격 및 표준 준수를 보장하는 데 필요한 **모든 시험으로부터 도출된 완전한 데이터**가 포함되어야 합니다. (21 CFR 211.194(a))",
        "21_CFR_820_70_I": "컴퓨터 또는 자동화된 데이터 처리 시스템이 품질 시스템의 일부로 사용될 경우, 제조업체는 해당 컴퓨터 소프트웨어가 **의도된 용도에 대해 검증**되었음을 보장하는 절차를 수립해야 합니다. (21 CFR 820.70(i))",
        
        # Module 2 (DI) 토론 근거
        "DI_Contemporaneous": "데이터 기록 및 변경은 발생 시점에 이루어져야 합니다. (PIC/S DI - ALCOA+)",
        "DI_RNR": "각 개인은 자신의 역할에 따른 책임과 권한을 가져야 하며, 시스템 접근 권한은 이 책임에 따라 제한되어야 합니다. (Part 11, Annex 11 - RNR)",
        "DI_Attributable": "데이터를 누가, 언제, 왜 기록 또는 수정했는지 명확히 추적 가능해야 합니다. (PIC/S DI - ALCOA+)",
        
        # Module 3 (GAMP 5) 토론 근거
        "GAMP5_CriticalThinking": "시스템의 복잡성, 기능 및 리스크에 따라 적절한 GAMP Category를 선택해야 하며, 낮은 Category 선택은 Validation 불충분을 의미합니다.",
        "GAMP5_RiskBased": "Validation 노력은 시스템의 품질 및 환자 안전에 미치는 리스크에 비례해야 합니다. 단순 시스템에 과도한 노력을 투입하는 것은 비효율적입니다.",
    }

    # 2. regulatory_snippets.txt 파일 로드 및 파싱 (사용자 제공 파일 내용)
    try:
        with open(snippet_path, 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    code, snippet_en = line.split(':', 1)
                    code = code.strip()
                    snippet_en = snippet_en.strip()
                    
                    # 파일에 있는 항목을 snippets에 저장
                    snippets[code] = {
                        "en": snippet_en,
                        "ko": translations.get(code, f"번역 내용 없음 (코드: {code})")
                    }

    except FileNotFoundError:
        st.error(f"오류: {snippet_path} 파일이 작업 폴더에 없습니다. 규제 근거를 로드할 수 없습니다.")
    
    # 3. 파일에 없지만 로직 구현에 필수적인 DI/GAMP 항목 추가
    for code, ko_text in translations.items():
        if code not in snippets:
             # 파일에 없는 항목은 영어 원문 대신 임시 텍스트를 사용합니다.
             snippets[code] = {
                 "en": f"Regulatory principle related to {code}",
                 "ko": ko_text
             }

    return snippets

REGULATORY_DATA = load_regulatory_data()

# ==============================================================================
# MVP 설정 및 디자인 및 Session State 초기화 (순차적 공개용)
# ==============================================================================
st.set_page_config(layout="wide")
st.title('🔬 교육용 MVP: 2026년 규제 집중 분석')
st.caption('Annex 22, DI, GAMP 5 난제')

# 순차적 공개를 위한 세션 상태 초기화
if 'm2_step' not in st.session_state:
    st.session_state.m2_step = 0

st.markdown("---")

# ==============================================================================
# 상단 탭 내비게이션 적용 (시간 배분 명시)
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "💡 모듈 1 : AI/ML 규제 투명성 (S4, S5)",
    "💡 모듈 2 : Audit Trail DI 심층 분석 (S1, S2, S3, S4)",
    "💡 모듈 3 : GAMP 5 Validation 리스크 (S6)"
])

# ==============================================================================
# 모듈 1: AI 규정 근거 및 모델 관리 (S4, S5 통합) - 규제 근거 출력 강화
# ==============================================================================
with tab1:
    
    st.header('1. AI 규정 근거 및 모델 관리 (Annex 22)')
    st.markdown("**📌 ** AI가 '정답'을 제시하는 것보다, **'규제적으로 검증 가능한 근거'**를 제시하는 것이 더 중요합니다. Veeva와 같은 솔루션이 이 요건을 어떻게 충족하는지 논의해보십시오.")
    st.markdown("---")
    
    # ----------------------------------------------------
    # 1-1. AI 규정 근거 투명성 실습 (S4)
    # ----------------------------------------------------
    st.subheader('1-1. AI 결과 근거 투명성 시뮬레이터 (S4)')
    
    # 질문과 정답, 그리고 규제 근거 키를 매핑합니다. (신규 항목 P11_10_B 추가)
    question_options = {
        "AI 결과의 '판단 근거'는 어떻게 제시해야 합니까? (Annex 22.8)": ("AI 모델은 결과를 도출한 방법을 설명할 수 있어야 합니다.", "A22_8"),
        "Raw Data의 정의 및 무결성 요건은 무엇입니까? (PIC/S DI)": ("Raw data는 종이 또는 전자적으로 기록된 정보의 첫 번째 획득이며 동적 상태에서 획득한 정보는 해당 상태에서 계속 사용할 수 있어야 합니다.", "PIC/S_R2"),
        "전자 서명 사용자의 비밀번호 관리 요건은 무엇입니까? (Part 11)": ("식별 코드와 암호 발행은 주기적으로 점검, 회수 또는 개정되어야 합니다 (예: 암호 유효 기간 만료와 같은 이벤트를 다루기 위함).", "P11_300"),
        "AI 소프트웨어가 처리한 환자 PII의 안전 삭제 기능도 검증해야 합니까? (WL 기반)": ("환자의 전자 기록에 대한 기밀성(Confidentiality) 보장 및 소프트웨어 검증이 필요합니다.", "P11_10_B"),
    }

    selected_question = st.selectbox(
        '규제 질문을 선택하세요:',
        list(question_options.keys()),
        key='ai_q'
    )

    if st.button('AI 분석 결과 보기 (Explainability 시연)'):
        answer, citation_key = question_options[selected_question]
        
        # REGULATORY_DATA에서 근거를 찾습니다.
        citation_info = REGULATORY_DATA.get(citation_key)
        
        st.subheader('AI 답변 및 규제 근거:')
        st.success(f"**AI 해석 (결론):** {answer}")
        st.markdown('---')
        st.subheader(f'🚨 심사자 검증 영역: 근거 자료 ({citation_key} 관련)')
        
        if citation_info:
            citation_text_en = citation_info["en"]
            citation_text_ko = citation_info["ko"]
            
            st.markdown(f"**1. 규정 원문 ({citation_key})**")
            st.code(citation_text_en, language='text')

            st.markdown(f"**2. 번역 내용 및 출처 (심사자 이해):**")
            st.info(citation_text_ko)
        else:
            st.warning("경고: 해당 질문에 대한 규제 근거를 찾을 수 없습니다. (Annex 22 위반 가능성)")
            
    st.markdown("---")
    
    # ----------------------------------------------------
    # 1-2. AI 모델 버전 관리 및 밸리데이션 범위 문제 (S5)
    # ----------------------------------------------------
    st.subheader('1-2. AI 모델 변경 관리 리스크 평가 (S5)')
    st.markdown("AI 모델 업데이트 시 **재밸리데이션 범위**의 적정성을 판단합니다. **(Annex 22.10 - Operation)**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        model_change_status = st.selectbox(
            'AI 모델 변경 사항:',
            ('선택 안 함', 'v1.0 -> v1.1 (알고리즘 Minor 변경)', 'v1.0 -> v1.2 (학습 데이터셋 Major 변경)'),
            key='model_change_status'
        )
    
    with col2:
        validation_status = st.selectbox(
            '업데이트된 Validation Plan 검토 결과:',
            ('선택 안 함', '재밸리데이션 범위가 Minor 변경에 맞춰 축소됨', '전체 기능에 대한 Full Validation이 계획됨'),
            key='validation_status'
        )
    
    if st.button('리스크 분석 (Model Drift)'):
        # Annex 22.10에 해당하는 가상의 규제 근거를 사용합니다.
        annex_22_10_ko = "AI 모델의 변경 사항이 모델 성능과 신뢰성에 미치는 영향도에 따라 재밸리데이션 범위를 설정해야 합니다. Major 변경 시 광범위한 재밸리데이션이 필수입니다."
        
        if model_change_status == 'v1.0 -> v1.2 (학습 데이터셋 Major 변경)' and validation_status == '재밸리데이션 범위가 Minor 변경에 맞춰 축소됨':
            st.error("🚨 CRITICAL WARNING: 밸리데이션 범위 불충분")
            st.markdown(f"""
            **규제적 판단:** 학습 데이터셋의 **Major 변경**은 AI 모델 성능에 **심각한 드리프트(Drift)**를 유발할 수 있습니다. 
            **[근거 조항: EU GMP Annex 22.10 (Operation)]**에 따라, 광범위한 재밸리데이션이 필요하나, 계획이 축소되어 **모델 신뢰성에 심각한 위험**이 있습니다.
            """)
            st.markdown(f"**📢 규제 근거:** {annex_22_10_ko}")
            st.markdown("""
            **📌 ** 모델 드리프트가 발생하는 시각화 자료를 제시하며, 변경 관리 시스템이 왜 이 오류를 놓쳤는지 토론을 유도합니다. 
            """)
            st.info("") 
        elif model_change_status == '선택 안 함' or validation_status == '선택 안 함':
            st.warning("항목을 모두 선택해 주세요.")
        else:
            st.success("✅ 현재 검토 결과, 밸리데이션 범위는 적정합니다.")
            st.markdown(f"""
            **규제적 판단:** 모델 변경의 영향도에 따라 밸리데이션 범위를 적절하게 판단하였습니다. **[근거 조항: EU GMP Annex 22.10 (Operation)]**
            """)
            st.markdown(f"**📢 규제 근거:** {annex_22_10_ko}")

# ==============================================================================
# 모듈 2: Audit Trail DI 심층 분석 (S1, S2, S3, S4 통합)
# ==============================================================================
with tab2:
    
    st.header('2. Audit Trail DI 심층 분석 (S1, S2, S3, S4 통합 훈련)')
    st.markdown("---")
    
    try:
        df = pd.read_csv('audit_log_error.csv')
        
    except FileNotFoundError:
        st.error("오류: audit_log_error.csv 파일이 작업 폴더에 없습니다. 파일을 생성해 주세요.")
        df = pd.DataFrame()
        
    # --- Analysis Logic (DI 오류 행 탐지) ---
    if not df.empty:
        df['TimeStamp(Server)'] = pd.to_datetime(df['TimeStamp(Server)'])
        df['ActionTime(Client)'] = pd.to_datetime(df['ActionTime(Client)'])
        time_diff_threshold = 120 # 2분(120초) 이상 차이
        
        # S1: 시간 동기화 오류 (Contemporaneous)
        df['TimeDifference'] = (df['TimeStamp(Server)'] - df['ActionTime(Client)']).dt.total_seconds().abs()
        time_error_logs = df[df['TimeDifference'] > time_diff_threshold]
        
        # S3: 사유 누락 오류 (Attributable)
        reason_error_logs = df[
            ((df['ActionType'] == 'MODIFY') | (df['ActionType'] == 'CHANGE_STATUS')) &
            (df['ReasonForChange'].isna() | (df['ReasonForChange'].astype(str).str.strip() == ''))
        ]
        
        # S2: 역할 권한 오용 오류 (RNR)
        role_error_logs = df[
            (df['Role'] == 'QA_REVIEWER') & (df['ActionType'] == 'RAW_DATA_PROCESS')
        ]
        
        error_indices = time_error_logs.index.union(reason_error_logs.index).union(role_error_logs.index)

        def highlight_errors(row):
            styles = [''] * len(row)
            if row.name in error_indices:
                styles = ['color: red; background-color: #ffeeee'] * len(row)
            return styles

        df_display = df.copy()
        df_display['TimeStamp(Server)'] = df_display['TimeStamp(Server)'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_display['ActionTime(Client)'] = df_display['ActionTime(Client)'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_display = df_display.drop(columns=['TimeDifference'])
        
        
    if not df.empty:
        st.subheader('2-1. Audit Trail 원문 제시 및 수동 분석')
        st.markdown("제약사에서 제출한 가상의 Audit Trail 원문입니다. **DI 분석 툴을 돌리기 전,** 심사자의 관점으로 DI 위반 행을 **최소 1개 이상** 찾아보십시오.")
        st.dataframe(df_display.drop(columns=['TimeDifference']) if 'TimeDifference' in df_display.columns else df_display, use_container_width=True)
        
        st.markdown("""
        ### 📢 [토론 1] 원칙 위반 가설 설정
        이 로그에서 **PIC/S DI 원칙** 중 어떤 원칙이 위반되었을지 토론해보십시오.
        """)
        
        st.markdown("---")
        
        # --- [1단계] DI 자동 분석 시작 버튼 ---
        if st.button('DI 자동 분석 시작 및 심사자 판단 확인', key='audit_start'):
            st.session_state.m2_step = 1 # Step 1: Show highlighted table
            
        if st.session_state.m2_step >= 1:
            
            # ----------------------------------------------------
            # 2-2. [10분] 자동 탐지 결과 시각화
            # ----------------------------------------------------
            st.subheader('2-2. [10분] 자동 탐지 결과 시각화')
            st.markdown("🚨 **빨간색 하이라이트 행**은 시스템이 탐지한 DI 위반 가능성 항목입니다. **심사자의 관점과 시스템 분석 결과를 비교**해보십시오.")
            styled_df = df_display.style.apply(highlight_errors, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            st.info("")
            
            st.markdown("---")
            
            st.subheader('2-3. CRITICAL WARNING 심층 분석 (순차적 토론)')
            
            # --- Sequential Buttons for Discussion (S4 추가) ---
            col_seq1, col_seq2, col_seq3, col_seq4 = st.columns(4)
            
            with col_seq1:
                if st.button('S1: 시간 동기화 오류 심층 토론 시작'):
                    st.session_state.m2_step = 2
            with col_seq2:
                if st.session_state.m2_step >= 2: 
                    if st.button('S2: 역할 권한 오용 심층 토론 시작'):
                        st.session_state.m2_step = 3
                elif st.session_state.m2_step == 1:
                    st.warning("")
            with col_seq3:
                if st.session_state.m2_step >= 3: 
                    if st.button('S3: 사유 누락 오류 심층 토론 시작'):
                        st.session_state.m2_step = 4
                elif st.session_state.m2_step == 2:
                    st.warning("")
            with col_seq4: # New S4 Button: Pre-Injection/데이터 불완전성
                if st.session_state.m2_step >= 4: 
                    if st.button('S4: Pre-Injection/데이터 불완전성 토론 시작'):
                        st.session_state.m2_step = 5
                elif st.session_state.m2_step == 3:
                    st.warning("")

            st.markdown("---")

            # --- S1 Analysis Display (Step 2) - 규제 근거 추가
            if st.session_state.m2_step >= 2:
                # DI_Contemporaneous 근거 로드
                contemporaneous_ko = REGULATORY_DATA.get("DI_Contemporaneous", {}).get("ko", "근거 조항을 찾을 수 없습니다.")
                
                if not time_error_logs.empty:
                    st.error("🔴 CRITICAL WARNING (S1): 시간 동기화 오류")
                    st.markdown(f"**위반 원칙:** **Contemporaneous** (동시 기록) - 클라이언트와 서버 시간 차이. (발견 행: {time_error_logs.index.tolist()})")
                    st.markdown(f"**📢 규제 근거 (PIC/S DI):** {contemporaneous_ko}") # 규제 근거 제시
                    st.markdown("""
                    **📢 토론 주제:** 1. 서버/클라이언트 시간 차이가 **데이터의 진실성**에 미치는 영향은 무엇입니까?
                    2. 이 오류가 **Batch Record의 최종 승인**에 어떤 영향을 미칠 수 있습니까?
                    """)
                else:
                    st.success("✅ S1 (시간 동기화 오류): 탐지된 오류 없음.")
                st.markdown("---")

            # --- S2 Analysis Display (Step 3) - 규제 근거 추가
            if st.session_state.m2_step >= 3:
                # DI_RNR 근거 로드
                rnr_ko = REGULATORY_DATA.get("DI_RNR", {}).get("ko", "근거 조항을 찾을 수 없습니다.")
                
                if not role_error_logs.empty:
                    st.error("🔴 CRITICAL WARNING (S2): 승인되지 않은 역할 개입")
                    st.markdown(f"**위반 원칙:** **RNR (Roles & Responsibilities)** - `QA_REVIEWER`가 `RAW_DATA_PROCESS` 시도. (발견 행: {role_error_logs.index.tolist()})")
                    st.markdown(f"**📢 규제 근거 (Part 11/Annex 11):** {rnr_ko}") # 규제 근거 제시
                    st.markdown("""
                    **📢 토론 주제:** 1. 시스템 접근 통제(Access Control) 설정이 왜 실패했습니까?
                    2. Part 11에서 정의하는 **전자 서명의 정당성**은 이 행위로 인해 어떻게 훼손됩니까?
                    """)
                else:
                    st.success("✅ S2 (역할 권한 오용 오류): 탐지된 오류 없음.")
                st.markdown("---")
            
            # --- S3 Analysis Display (Step 4) - 규제 근거 추가
            if st.session_state.m2_step >= 4:
                # DI_Attributable 근거 로드
                attributable_ko = REGULATORY_DATA.get("DI_Attributable", {}).get("ko", "근거 조항을 찾을 수 없습니다.")
                
                if not reason_error_logs.empty:
                    st.error("🔴 CRITICAL WARNING (S3): 중요 행위에 대한 사유 누락")
                    st.markdown(f"**위반 원칙:** **Attributable** (책임성) - 변경 사유 누락. (발견 행: {reason_error_logs.index.tolist()})")
                    st.markdown(f"**📢 규제 근거 (PIC/S DI):** {attributable_ko}") # 규제 근거 제시
                    st.markdown("""
                    **📢 토론 주제:** 1. 사유 누락이 **데이터 추적성(Traceability)**을 어떻게 파괴합니까?
                    2. 이 경우, 해당 변경 행위 전체를 **무효(Invalid)** 처리해야 합니까? 심사자 판단은?
                    """)
                else:
                    st.success("✅ S3 (사유 누락 오류): 탐지된 오류 없음.")
                st.markdown("---")
                
            # --- S4 Analysis Display (Step 5) - 신규 FDA WL 기반 DI 사례 추가
            if st.session_state.m2_step >= 5:
                # 21_CFR_211_194_A 근거 로드
                incomplete_data_ko = REGULATORY_DATA.get("21_CFR_211_194_A", {}).get("ko", "근거 조항을 찾을 수 없습니다.")
                
                # S4는 Audit Log에서 직접 탐지되지 않는, '숨겨진' 행위를 가정한 CRITICAL WARNING입니다.
                st.error("🔴 CRITICAL WARNING (S4): Raw Data 불완전성 - Pre-Injection/Aborted Run 행위")
                st.markdown(f"**위반 원칙:** **Complete (데이터 완전성)** - QC 분석가가 실제 샘플 분석 전 **'Pre-Injection'**을 실행하거나, OOS 결과가 예상될 때 **분석 시퀀스를 중단(Abort)** 후 해당 원본 데이터를 보존하지 않은 행위를 가정합니다.")
                st.markdown(f"**📢 규제 근거 (21 CFR 211.194(a) - WL 기반):** {incomplete_data_ko}") # 규제 근거 제시
                st.markdown("""
                **📢 토론 주제:** 1. Pre-Injection이 **데이터 조작(Data Fabrication)**으로 간주되는 이유는 무엇입니까?
                2. Audit Trail에 'Aborted'로 기록된 로그에 대해서도 **원본 Raw Data**를 보존하고 검토해야 하는 규제적 의무가 있습니까? (Complete 원칙)
                """)
                st.markdown("---")
            
            # Final message if all steps are completed
            if st.session_state.m2_step == 5:
                st.success("✅ 모든 시나리오 분석 완료: 심화된 DI 오류 유형에 대한 학습을 마쳤습니다.")
            
        elif st.session_state.m2_step == 0:
            st.info("⬆️ Audit Trail 원문을 검토하신 후, 'DI 자동 분석 시작' 버튼을 눌러 시스템 탐지 결과를 확인하십시오.")

# ==============================================================================
# 모듈 3: GAMP 5 Validation 리스크 (S6 통합)
# ==============================================================================
with tab3:
    
    st.header('3. GAMP 5 기반 CSV 리스크 판단 (S6)')
    st.markdown("**📌 ** GAMP 5의 **Critical Thinking**은 비용 절감이 아닌 **리스크 기반 분류**입니다. 시스템 기능과 Category 불일치 시 발생하는 심각한 위험에 대해 논의해보십시오.")
    st.markdown("---")
    
    st.subheader('3-1. 시스템 분류 일치 여부 분석 (S6)')
    
    col1, col2 = st.columns(2)
    with col1:
        system_type = st.selectbox(
            'URS(User Requirement Spec.)에 명시된 시스템의 핵심 기능:',
            ('선택 안 함', '단순 데이터 로깅/저장 기능', '복잡한 Process Parameter 계산/결정 로직 포함', '데이터 처리 로직은 있으나 비판적이지 않은 시스템'),
            key='system_type_gamp'
        )
    
    with col2:
        validation_category = st.selectbox(
            'Validation Plan에 명시된 GAMP 5 Category:',
            ('선택 안 함', 'Category 3 (Non-Configured Software)', 'Category 4 (Configured Software)', 'Category 5 (Custom Application)'),
            key='validation_category_gamp'
        )
    
    if st.button('GAMP 5 리스크 일치 분석', key='gamp_start'):
        
        critical_ko = REGULATORY_DATA.get("GAMP5_CriticalThinking", {}).get("ko", "근거 조항을 찾을 수 없습니다.")
        risk_based_ko = REGULATORY_DATA.get("GAMP5_RiskBased", {}).get("ko", "근거 조항을 찾을 수 없습니다.")
        
        if system_type == '복잡한 Process Parameter 계산/결정 로직 포함' and validation_category in ['Category 3 (Non-Configured Software)', 'Category 4 (Configured Software)']:
            st.error("🚨 CRITICAL WARNING: GAMP 5 Category 불일치 리스크")
            st.markdown("""
            **규제적 판단:** 복잡한 계산 로직은 **Category 5**에 해당합니다. 낮은 Category 분류는 **Validation 범위가 불충분**하다는 것을 의미하며, **데이터 무결성 및 제품 품질에 치명적인 위험**이 있습니다.
            **[근거 조항: GAMP 5 Second Edition - Critical Thinking Principle / Category 5 Definition]**
            """)
            st.markdown(f"**📢 규제 근거:** {critical_ko}")
            st.markdown("""
            **📌 ** GAMP 5의 분류 차트를 제시하며, 왜 이 시스템이 Category 5여야 하는지, Validation 문서의 어떤 부분이 누락되었을지 토론을 유도합니다.
            """)
            st.info("") 
        elif system_type == '단순 데이터 로깅/저장 기능' and validation_category == 'Category 5 (Custom Application)':
            st.warning("🟡 WARNING: Validation 과도 적용 리스크 (비효율)")
            st.markdown("""
            **규제적 판단:** 단순 로깅 시스템을 Category 5로 분류하면 **불필요한 리소스**가 낭비됩니다. **[근거 조항: GAMP 5 Second Edition - Risk-Based Approach Principle]**
            """)
            st.markdown(f"**📢 규제 근거:** {risk_based_ko}")
        elif system_type == '선택 안 함' or validation_category == '선택 안 함':
            st.warning("항목을 모두 선택해 주세요.")
        else:
            st.success("✅ GAMP 5 Category 분류가 의도된 용도(URS)와 적절하게 일치합니다.")
            st.markdown("""
            **규제적 판단:** 시스템의 리스크 기반으로 Validation 노력을 효율화했습니다. **[근거 조항: GAMP 5 Second Edition - Risk-Based Approach Principle]**
            """)
            st.markdown(f"**📢 규제 근거:** {risk_based_ko}")

    st.markdown("---")

    # ----------------------------------------------------
    # 3-2. 품질 시스템용 상용 소프트웨어 Validation 리스크
    # ----------------------------------------------------
    st.subheader('3-2. 품질 시스템용 상용 소프트웨어 Validation 리스크 (FDA WL 기반)')

    col3, col4 = st.columns(2)
    with col3:
        qs_tool = st.selectbox(
            '품질 시스템(Quality System)에서 사용되는 소프트웨어:',
            ('선택 안 함', 'Batch Record 관리용 Custom ERP', 'CAPA/Complaint 기록용 Excel 스프레드시트', '장비 제어용 펌웨어'),
            key='qs_tool_gamp'
        )
    with col4:
        validation_status_qs = st.selectbox(
            '해당 소프트웨어에 대한 Validation 수행 여부:',
            ('선택 안 함', 'Full Validation 수행', 'Vendor Qualification만 수행', '미수행 (상용 소프트웨어라 가정)'),
            key='validation_status_qs'
        )

    if st.button('QS 소프트웨어 Validation 리스크 분석', key='qs_validation_start'):
        
        qs_validation_ko = REGULATORY_DATA.get("21_CFR_820_70_I", {}).get("ko", "근거 조항을 찾을 수 없습니다.")

        if qs_tool == 'CAPA/Complaint 기록용 Excel 스프레드시트' and validation_status_qs == '미수행 (상용 소프트웨어라 가정)':
            st.error("🚨 CRITICAL WARNING: 품질 시스템 소프트웨어 Validation 실패")
            st.markdown("""
            **규제적 판단:** 품질 시스템(CAPA, Complaint 등)의 일부로 사용되는 **상용 소프트웨어(Excel 포함)**라도 **의도된 용도**에 대한 검증(Validation)이 필수입니다. 미검증 시, 기록의 무결성(데이터 수정/삭제 가능, Audit Trail 부재) 위반으로 **FDA Warning Letter (21 CFR 820.70(i) 위반)**의 주요 원인이 됩니다.
            """)
            st.markdown(f"**📢 규제 근거 (21 CFR 820.70(i) - WL 기반):** {qs_validation_ko}")
            st.markdown("""
            **📌 강사 토론 유도 Tip:** '엑셀'이 상용 소프트웨어인데 왜 Validation이 필요한지, 어떤 Validation 항목(예: 접근 통제, 데이터 백업, 계산식 정확성)이 필요한지 토론을 유도합니다. (20분)
            """)
            st.info("")
        elif qs_tool == '선택 안 함' or validation_status_qs == '선택 안 함':
            st.warning("항목을 모두 선택해 주세요.")
        else:
            st.success("✅ 품질 시스템 소프트웨어 Validation 상태는 적절합니다.")
            st.markdown(f"**규제 근거 (21 CFR 820.70(i) - WL 기반):** {qs_validation_ko}")