import streamlit as st
import pandas as pd
from datetime import datetime
import io
import time

# ==============================================================================
# 0. 규제 근거 로딩 및 매핑 함수
# ==============================================================================

def load_regulatory_data(snippet_path='regulatory_snippets.txt'):
    """
    규제 스니펫 및 번역 데이터를 로드합니다.
    """
    snippets = {}
    
    translations = {
        "PIC/S_R2": "원본 데이터는 종이에 기록되었거나 전자적으로 기록된 정보의 첫 번째 획득으로 설명할 수 있는 원본 기록(데이터)으로 정의된다. 원래 동적 상태에서 획득한 정보는 해당 상태에서 계속 사용할 수 있어야 한다.",
        "A22_8": "AI 모델의 출력은 설명 가능해야 합니다. 이는 AI 모델이 주어진 출력에 어떻게 도달했는지 설명할 수 있어야 함을 의미합니다.",
        "P11_300": "식별 코드와 암호 발행은 주기적으로 점검, 회수 또는 개정되어야 합니다 (예: 암호 유효 기간 만료와 같은 이벤트를 다루기 위함).",
        "P11_10_B": "회사는 전자 기록 및 서명의 진위, 무결성 그리고 적절한 경우 **기밀성**을 보장하도록 설계된 절차 및 통제를 적용해야 합니다. (21 CFR Part 11)",
        "21_CFR_211_194_A": "시험소 기록에는 설정된 규격 및 표준 준수를 보장하는 데 필요한 **모든 시험으로부터 도출된 완전한 데이터**가 포함되어야 합니다. (21 CFR 211.194(a))",
        "21_CFR_820_70_I": "컴퓨터 또는 자동화된 데이터 처리 시스템이 품질 시스템의 일부로 사용될 경우, 제조업체는 해당 컴퓨터 소프트웨어가 **의도된 용도에 대해 검증**되었음을 보장하는 절차를 수립해야 합니다. (21 CFR 820.70(i))",
        "DI_Contemporaneous": "데이터 기록 및 변경은 발생 시점에 이루어져야 합니다. (PIC/S DI - ALCOA+)",
        "DI_RNR": "각 개인은 자신의 역할에 따른 책임과 권한을 가져야 하며, 시스템 접근 권한은 이 책임에 따라 제한되어야 합니다. (Part 11, Annex 11 - RNR)",
        "DI_Attributable": "데이터를 누가, 언제, 왜 기록 또는 수정했는지 명확히 추적 가능해야 합니다. (PIC/S DI - ALCOA+)",
        "GAMP5_CriticalThinking": "시스템의 복잡성, 기능 및 리스크에 따라 적절한 GAMP Category를 선택해야 하며, 낮은 Category 선택은 Validation 불충분을 의미합니다.",
        "GAMP5_RiskBased": "Validation 노력은 시스템의 품질 및 환자 안전에 미치는 리스크에 비례해야 합니다. 단순 시스템에 과도한 노력을 투입하는 것은 비효율적입니다.",
    }

    try:
        with open(snippet_path, 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    code, snippet_en = line.split(':', 1)
                    code = code.strip()
                    snippet_en = snippet_en.strip()
                    snippets[code] = {"en": snippet_en, "ko": translations.get(code, f"번역 내용 없음 (코드: {code})")}
    except FileNotFoundError:
        # File not found error handling should be done in the environment where the file is expected to be
        pass
    
    # Ensure all required regulatory texts are present even if file loading fails
    for code, ko_text in translations.items():
        if code not in snippets:
             snippets[code] = {"en": f"Regulatory principle related to {code}", "ko": ko_text}

    return snippets

REGULATORY_DATA = load_regulatory_data()

# ==============================================================================
# MVP 설정 및 디자인 및 Session State 초기화 
# ==============================================================================
st.set_page_config(layout="wide")
st.title('🔬 교육용 MVP: 2026년 규제 집중 분석')
st.caption('Annex 22, DI, GAMP 5 핵심 규제 시각화')

# 순차적 공개 및 탭 상태 관리를 위한 세션 상태 초기화
if 'm2_step' not in st.session_state:
    st.session_state.m2_step = 0

st.markdown("---")

# ==============================================================================
# 상단 탭 내비게이션 적용
# ==============================================================================
tab_names = [
    "💡 모듈 1: AI/ML 규제 투명성",
    "💡 모듈 2: Audit Trail DI 심층 분석",
    "💡 모듈 3: GAMP 5 Validation 리스크"
]
tab1, tab2, tab3 = st.tabs(tab_names)

# --- FDA Warning Letter Citation (21 CFR 820.70(i) - COTS/Excel) ---
WL_SNIPPET_EN = "Your firm failed to adequately validate computer software used as part of the quality system for its intended use, as required by 21 CFR 820.70(i). Specifically, your firm utilized a commercially available software (Excel spreadsheet) to record and manage critical Quality System data, such as CAPA and Complaint records. You did not establish procedures to assure that this spreadsheet was validated for its intended use, including ensuring data integrity, traceability, and access control."
WL_SNIPPET_KO = "귀사는 21 CFR 820.70(i)에 따라 품질 시스템의 일부로 사용되는 컴퓨터 소프트웨어가 의도된 용도에 대해 적절하게 검증되었음을 보장하는 데 실패했습니다. 특히, 귀사는 CAPA 및 불만사항 기록과 같은 중요한 품질 시스템 데이터를 기록하고 관리하기 위해 상용 소프트웨어(Excel 스프레드시트)를 사용했지만, 데이터 무결성, 추적성 및 접근 통제를 포함하여 이 스프레드시트가 의도된 용도에 대해 검증되었음을 보장하는 절차를 수립하지 않았습니다."
# ---------------------------------------------------------------------


# ==============================================================================
# 모듈 1: AI 규정 근거 및 모델 관리 
# ==============================================================================
with tab1:
    # 탭 진입 시, 모듈 2의 상태 초기화 (다른 모듈로 넘어왔음을 감지)
    if st.session_state.m2_step != 0:
        st.session_state.m2_step = 0
    
    st.header('1. AI 규정 근거 및 모델 관리 (Annex 22 집중)')
    st.markdown("---")
    
    subtab_1_1, subtab_1_2 = st.tabs(["1-1. AI 결과 근거 투명성", "1-2. AI 모델 변경 관리 리스크"])
    
    with subtab_1_1:
        st.subheader('AI 결과 근거 투명성 시뮬레이터')
        
        question_options = {
            "AI 결과의 '판단 근거'는 어떻게 제시해야 합니까? (Annex 22.8)": ("AI 모델은 결과를 도출한 방법을 설명할 수 있어야 합니다.", "A22_8"),
            "Raw Data의 정의 및 무결성 요건은 무엇입니까? (PIC/S DI)": ("Raw data는 종이 또는 전자적으로 기록된 정보의 첫 번째 획득이며 동적 상태에서 획득한 정보는 해당 상태에서 계속 사용할 수 있어야 합니다.", "PIC/S_R2"),
            "AI 소프트웨어가 처리한 환자 PII의 안전 삭제 기능도 검증해야 합니까? (WL 기반)": ("환자의 전자 기록에 대한 기밀성(Confidentiality) 보장 및 소프트웨어 검증이 필요합니다.", "P11_10_B"),
        }

        selected_question = st.selectbox(
            '규제 질문을 선택하세요:',
            list(question_options.keys()),
            key='ai_q'
        )

        if st.button('AI 분석 결과 보기 (Explainability 시연)', key='btn_ai_analysis'):
            answer, citation_key = question_options[selected_question]
            citation_info = REGULATORY_DATA.get(citation_key)
            
            st.subheader('AI 답변 및 규제 근거:')
            st.success(f"**AI 해석 (결론):** {answer}")
            st.markdown('---')
            st.subheader(f'🚨 심사자 검증 영역: 근거 자료 ({citation_key} 관련)')
            
            if citation_info:
                st.markdown(f"**1. 규정 원문 ({citation_key})**")
                st.code(citation_info['en'], language='text')

                st.markdown(f"**2. 번역 내용 및 출처 (심사자 이해):**")
                st.info(citation_info['ko'])
                
                # --- 심화 토론 주제 추가 (판단 요소 강화) ---
                if citation_key == "A22_8":
                    st.markdown("""
                    **📢 심화 토론 주제 (AI Explainability):**
                    1. AI 모델이 **'설명 가능해야 한다'**는 요구사항을 충족하기 위해, 모델 개발자는 어떤 형태의 **추론 과정 기록(Inference Log)**을 제출해야 합니까?
                    2. **Black Box 모델**의 경우, Shimotore 기법 등의 **사후 해석(Post-hoc Explainability)** 결과가 Annex 22.8의 규제적 요구사항을 충분히 만족시킬 수 있다고 판단하십니까?
                    """)
                    st.markdown("**(이미지 대체: SHAP 또는 LIME을 이용한 AI 모델 출력 설명 차트)**") 
                
                elif citation_key == "P11_10_B":
                    st.markdown("""
                    **📢 심화 토론 주제 (Part 11/기밀성):**
                    1. Part 11의 **'기밀성(Confidentiality)'** 요구사항은 DI(Data Integrity)의 **'Access Control'**과 어떻게 다릅니까?
                    2. PII(개인 식별 정보)를 포함하는 AI 소프트웨어의 **폐기(Retirement)** 시, 정보의 **안전 삭제(Secure Deletion)**를 Validation 해야 하는 근거 조항은 무엇입니까?
                    """)
                    st.markdown("**(이미지 대체: 데이터 보안 및 접근 통제 매트릭스)**") 
            else:
                st.warning("경고: 해당 질문에 대한 규제 근거를 찾을 수 없습니다.")
            
    with subtab_1_2:
        st.subheader('AI 모델 변경 관리 리스크 평가')
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
        
        if st.button('리스크 분석 (Model Drift)', key='btn_model_drift'):
            annex_22_10_ko = "AI 모델의 변경 사항이 모델 성능과 신뢰성에 미치는 영향도에 따라 재밸리데이션 범위를 설정해야 합니다. Major 변경 시 광범위한 재밸리데이션이 필수입니다."
            
            # --- 1. CRITICAL WARNING: Major 변경 + Validation 축소 (오류) ---
            if model_change_status == 'v1.0 -> v1.2 (학습 데이터셋 Major 변경)' and validation_status == '재밸리데이션 범위가 Minor 변경에 맞춰 축소됨':
                st.error("🚨 CRITICAL WARNING: 밸리데이션 범위 불충분")
                st.markdown(f"""
                **규제적 판단:** 학습 데이터셋의 **Major 변경**은 AI 모델 성능에 **심각한 드리프트(Drift)**를 유발할 수 있습니다. **[근거 조항: EU GMP Annex 22.10 (Operation)]**에 따라, 광범위한 재밸리데이션이 필요하나, 계획이 축소되어 **모델 신뢰성에 심각한 위험**이 있습니다.
                """)
                st.markdown(f"**📢 규제 근거:** {annex_22_10_ko}")
                
                st.markdown("---")
                st.subheader("📢 심화 토론 주제 및 **심사관의 조치 결정**:")
                
                # --- 심화 상호작용 요소: 심사관의 조치 결정 (Selectbox) ---
                action = st.selectbox(
                    '심사관이 현장에서 취해야 할 가장 적절한 긴급 조치를 선택하십시오:',
                    ('선택 안 함', '당장 시스템 사용 중지(System Hold)', '위반 지적 및 Batch Release 중단 권고', '다음 심사 시 추가 자료 요구'),
                    key='auditor_action_m1'
                )
                if action == '당장 시스템 사용 중지(System Hold)' or action == '위반 지적 및 Batch Release 중단 권고':
                    st.success(f"✅ 선택: **{action}**. Major 변경에 대한 불충분한 Validation은 AI 모델의 결과에 대한 신뢰성을 잃게 하므로, **환자 안전에 미치는 리스크가 높다**고 판단하는 것이 합리적입니다.")
                elif action == '다음 심사 시 추가 자료 요구' and action != '선택 안 함':
                    st.error(f"❌ 선택: **{action}**. 이는 CRITICAL WARNING 상황입니다. 다음 심사 시까지 기다리는 것은 **현재 진행 중인 Batch의 품질**을 위험에 빠뜨릴 수 있습니다.")
                # ----------------------------------------------------

                st.markdown("**(이미지 대체: 시계열 차트로 표시된 AI 모델 예측 드리프트)**") 

            # --- 2. SUCCESS: 합리적인 변경 관리 ---
            elif (model_change_status == 'v1.0 -> v1.1 (알고리즘 Minor 변경)' and validation_status == '재밸리데이션 범위가 Minor 변경에 맞춰 축소됨') or \
                 (model_change_status == 'v1.0 -> v1.2 (학습 데이터셋 Major 변경)' and validation_status == '전체 기능에 대한 Full Validation이 계획됨') or \
                 (model_change_status == 'v1.0 -> v1.1 (알고리즘 Minor 변경)' and validation_status == '전체 기능에 대한 Full Validation이 계획됨'):
                 
                st.success("✅ 현재 검토 결과, 밸리데이션 범위는 적정합니다.")
                st.markdown(f"""
                **규제적 판단:** 모델 변경의 영향도에 따라 밸리데이션 범위를 적절하게 판단하였습니다. **[근거 조항: EU GMP Annex 22.10 (Operation)]**
                """)
                st.markdown(f"**📢 규제 근거:** {annex_22_10_ko}")

            # --- 3. WARNING: 선택 안 함 ---
            elif model_change_status == '선택 안 함' or validation_status == '선택 안 함':
                st.warning("항목을 모두 선택해 주세요.")

# ==============================================================================
# 모듈 2: Audit Trail DI 심층 분석 
# ==============================================================================
with tab2:
    
    st.header('2. Audit Trail DI 심층 분석') 
    st.markdown("---")
    
    # 데이터 로딩 및 분석 로직 (변화 없음)
    try:
        # 실제 환경에서는 로컬 파일로 대체해야 함
        df = pd.read_csv('audit_log_error.csv') 
        
        if not df.empty:
            df['TimeStamp(Server)'] = pd.to_datetime(df['TimeStamp(Server)'])
            df['ActionTime(Client)'] = pd.to_datetime(df['ActionTime(Client)'])
            time_diff_threshold = 120 # 2분(120초) 이상 차이
            
            df['TimeDifference'] = (df['TimeStamp(Server)'] - df['ActionTime(Client)']).dt.total_seconds().abs()
            time_error_logs = df[df['TimeDifference'] > time_diff_threshold]
            
            reason_error_logs = df[
                ((df['ActionType'] == 'MODIFY') | (df['ActionType'] == 'CHANGE_STATUS')) &
                (df['ReasonForChange'].isna() | (df['ReasonForChange'].astype(str).str.strip() == ''))
            ]
            
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
            
    except FileNotFoundError:
        st.error("오류: audit_log_error.csv 파일이 작업 폴더에 없습니다. 파일을 생성해 주세요.")
        df = pd.DataFrame()
    except Exception as e:
        # 기타 데이터 로딩 오류 처리
        st.error(f"데이터 로딩 중 예외 발생: {e}")
        df = pd.DataFrame()
        
    
    # ==========================================================================
    # 2-1. Audit Trail 원문 제시 (고정 영역)
    # ==========================================================================
    if not df.empty:
        df_to_display = df_display.drop(columns=['TimeDifference'], errors='ignore')
        
        st.subheader('Audit Trail 원문 (참조)') 
        st.markdown("제약사에서 제출한 가상의 Audit Trail 원문입니다. **DI 위반 행을 찾을 때 참고**하십시오.")
        st.dataframe(df_to_display, use_container_width=True)
        st.markdown("---")
        
        # ==========================================================================
        # Step 0: 초기 화면 
        # ==========================================================================
        if st.session_state.m2_step == 0:
            st.markdown("""
            ### 📢 원칙 위반 가설 설정
            위 로그에서 **PIC/S DI 원칙** 중 위반 가능성이 있는 항목을 찾아 토론해보십시오.
            """)
            
            if st.button('DI 자동 분석 시작 및 심사자 판단 확인', key='audit_start'):
                st.session_state.m2_step = 1
                st.rerun()

        # ==========================================================================
        # Step 1 이상의 모든 단계에서 고정되는 '자동 탐지 결과' 및 '심층 분석 버튼'
        # ==========================================================================
        if st.session_state.m2_step >= 1:
            
            st.subheader('자동 탐지 결과 시각화') 
            st.markdown("🚨 **빨간색 하이라이트 행**은 시스템이 탐지한 DI 위반 가능성 항목입니다.")
            
            styled_df = df_display.drop(columns=['TimeDifference'], errors='ignore').style.apply(highlight_errors, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
            st.markdown("---")
            
            st.subheader('CRITICAL WARNING 심층 분석')
            
            col_seq1, col_seq2, col_seq3, col_seq4 = st.columns(4)
            
            # Step 1 이상의 모든 단계에서 버튼 노출
            with col_seq1:
                if st.button('시간 동기화 오류 심층 분석 시작', key='btn_s1_start', disabled=(st.session_state.m2_step == 2)):
                    st.session_state.m2_step = 2
                    st.rerun()
            
            with col_seq2:
                if st.button('역할 권한 오용 심층 분석 시작', key='btn_s2_start', disabled=(st.session_state.m2_step == 3)):
                    st.session_state.m2_step = 3
                    st.rerun()
            
            with col_seq3:
                if st.button('사유 누락 오류 심층 분석 시작', key='btn_s3_start', disabled=(st.session_state.m2_step == 4)):
                    st.session_state.m2_step = 4
                    st.rerun()
            
            with col_seq4: 
                if st.button('Raw Data 불완전성 심층 분석 시작', key='btn_s4_start', disabled=(st.session_state.m2_step == 5)):
                    st.session_state.m2_step = 5
                    st.rerun()
            
            # ==========================================================================
            # Step 2 이상의 단계에서만 나타나는 '심층 분석 결과'
            # ==========================================================================
            if st.session_state.m2_step >= 2:
                
                if st.session_state.m2_step == 2:
                    contemporaneous_ko = REGULATORY_DATA.get("DI_Contemporaneous", {}).get("ko", "근거 조항을 찾을 수 없습니다.")
                    st.error("🔴 CRITICAL WARNING: 시간 동기화 오류")
                    st.markdown(f"**위반 원칙:** **Contemporaneous** (동시 기록) - 클라이언트와 서버 시간 차이.")
                    st.markdown(f"**📢 규제 근거 (PIC/S DI):** {contemporaneous_ko}")
                    st.markdown("**(이미지 대체: Audit Trail 시간 동기화 위반 시각화)**")
                    st.markdown("""
                    **📢 토론 주제:** 1. 서버/클라이언트 시간 차이가 **데이터의 진실성(Truthfulness)**에 미치는 영향은 무엇입니까?
                    2. 이 오류가 **Batch Record의 최종 승인**에 어떤 영향을 미칠 수 있습니까?
                    """)
                
                elif st.session_state.m2_step == 3:
                    rnr_ko = REGULATORY_DATA.get("DI_RNR", {}).get("ko", "근거 조항을 찾을 수 없습니다.")
                    st.error("🔴 CRITICAL WARNING: 승인되지 않은 역할 개입")
                    st.markdown(f"**위반 원칙:** **RNR (Roles & Responsibilities)** - `QA_REVIEWER`가 `RAW_DATA_PROCESS` 시도.")
                    st.markdown(f"**📢 규제 근거 (Part 11/Annex 11):** {rnr_ko}")
                    st.markdown("**(이미지 대체: 전자 서명 역할 매트릭스)**")
                    st.markdown("""
                    **📢 토론 주제:** 1. 시스템 접근 통제(Access Control) 설정이 왜 실패했습니까?
                    2. Part 11에서 정의하는 **전자 서명의 정당성**은 이 행위로 인해 어떻게 훼손됩니까?
                    """)
                
                elif st.session_state.m2_step == 4:
                    attributable_ko = REGULATORY_DATA.get("DI_Attributable", {}).get("ko", "근거 조항을 찾을 수 없습니다.")
                    st.error("🔴 CRITICAL WARNING: 중요 행위에 대한 사유 누락")
                    st.markdown(f"**위반 원칙:** **Attributable** (책임성) - 변경 사유 누락.")
                    st.markdown(f"**📢 규제 근거 (PIC/S DI):** {attributable_ko}")
                    st.markdown("**(이미지 대체: Audit Trail 책임성 위반 시각화)**")
                    st.markdown("""
                    **📢 토론 주제:** 1. 사유 누락이 **데이터 추적성(Traceability)**을 어떻게 파괴합니까?
                    2. 이 경우, 해당 변경 행위 전체를 **무효(Invalid)** 처리해야 합니까? 심사자 판단은?
                    """)
                
                elif st.session_state.m2_step == 5:
                    incomplete_data_ko = REGULATORY_DATA.get("21_CFR_211_194_A", {}).get("ko", "근거 조항을 찾을 수 없습니다.")
                    st.error("🔴 CRITICAL WARNING: Raw Data 불완전성 - Pre-Injection/Aborted Run 행위")
                    st.markdown(f"**위반 원칙:** **Complete (데이터 완전성)** - QC 분석가가 실제 샘플 분석 전 **'Pre-Injection'**을 실행하거나, OOS 결과가 예상될 때 **분석 시퀀스를 중단(Abort)** 후 해당 원본 데이터를 보존하지 않은 행위를 가정합니다.")
                    st.markdown(f"**📢 규제 근거 (21 CFR 211.194(a) - WL 기반):** {incomplete_data_ko}")
                    st.markdown("**(이미지 대체: 크로마토그래피 Raw Data 불완전성)**")
                    st.markdown("""
                    **📢 토론 주제:** 1. Pre-Injection이 **데이터 조작(Data Fabrication)**으로 간주되는 이유는 무엇입니까?
                    2. Audit Trail에 'Aborted'로 기록된 로그에 대해서도 **원본 Raw Data**를 보존하고 검토해야 하는 규제적 의무가 있습니까?
                    """)
                
            
            elif st.session_state.m2_step == 1:
                st.info("⬆️ 위 **'CRITICAL WARNING 심층 분석'** 영역에서 분석을 원하는 항목의 버튼을 눌러 심층 분석 단계로 진입하십시오.")

    
    elif st.session_state.m2_step == 0 and df.empty:
        st.info("⬆️ Audit Trail 원문을 검토하신 후, 'DI 자동 분석 시작' 버튼을 눌러 시스템 탐지 결과를 확인하십시오.")


# ==============================================================================
# 모듈 3: GAMP 5 Validation 리스크 (심화)
# ==============================================================================
with tab3:
    # 탭 진입 시, 모듈 2의 상태 초기화 (다른 모듈로 넘어왔음을 감지)
    if st.session_state.m2_step != 0:
        st.session_state.m2_step = 0
        
    st.header('3. GAMP 5 기반 CSV 리스크 판단') 
    st.markdown("---")
    
    subtab_3_1, subtab_3_2 = st.tabs(["3-1. GAMP Category 분류 일치", "3-2. QS 소프트웨어 Validation 리스크 (FDA WL 인용)"])
    
    with subtab_3_1:
        st.subheader('시스템 분류 일치 여부 분석')
        st.markdown("**(이미지 대체: GAMP 5 소프트웨어 카테고리 차트)**")
        
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
            
            # --- 1. CRITICAL WARNING: Category 불일치 (리스크 과소평가) ---
            if system_type == '복잡한 Process Parameter 계산/결정 로직 포함' and validation_category in ['Category 3 (Non-Configured Software)', 'Category 4 (Configured Software)']:
                st.error("🚨 CRITICAL WARNING: GAMP 5 Category 불일치 리스크")
                st.markdown(f"""
                **규제적 판단:** 복잡한 계산 로직은 **Category 5**에 해당합니다. 낮은 Category 분류는 **Validation 범위가 불충분**하다는 것을 의미하며, **데이터 무결성 및 제품 품질에 치명적인 위험**이 있습니다.
                **[근거 조항: GAMP 5 Second Edition - Critical Thinking Principle / Category 5 Definition]**
                """)
                st.markdown(f"**📢 규제 근거:** {critical_ko}")
                
                st.markdown("---")
                st.subheader("📢 심화 토론 주제 및 **Validation Gap 검증**:")
                
                # --- 심화 상호작용 요소: 누락 항목 직접 입력 (Textarea) ---
                gap_input = st.text_area(
                    '이 상황에서 Validation 문서에 반드시 누락되었을 **가장 중요한 테스트 항목 3가지**를 입력하십시오. (예: 코드 리뷰, UAT 등)',
                    key='validation_gap_m3'
                )
                if st.button('입력 결과 확인', key='check_gap_m3'):
                    if "코드 리뷰" in gap_input.lower() or "code review" in gap_input.lower() or "사용자 인수 테스트" in gap_input or "uat" in gap_input.lower():
                        st.success("✅ 심사관의 통찰: Custom/Category 5 시스템에서는 **코드 리뷰 (Code Review)**, **사용자 인수 테스트 (UAT)**, 그리고 **컴포넌트 단위 테스트 (Component Testing)**의 상세 문서가 누락되었을 가능성이 가장 높습니다. **Category 5는 설계 및 코딩 단계의 검증이 필수**입니다.")
                    else:
                        st.warning("⚠️ 재검토 필요: 이 시스템이 Category 5일 때, 단순 기능 테스트 이상의 **설계 및 개발 단계 검증**이 누락될 위험을 고려하십시오.")
                # ----------------------------------------------------

            # --- 2. WARNING: Validation 과도 적용 (비효율) ---
            elif system_type == '단순 데이터 로깅/저장 기능' and validation_category == 'Category 5 (Custom Application)':
                st.warning("🟡 WARNING: Validation 과도 적용 리스크 (비효율)")
                st.markdown(f"""
                **규제적 판단:** 단순 로깅 시스템을 Category 5로 분류하면 **불필요한 리소스**가 낭비됩니다. **[근거 조항: GAMP 5 Second Edition - Risk-Based Approach Principle]**
                """)
                st.markdown(f"**📢 규제 근거:** {risk_based_ko}")
                
                st.markdown("---")
                st.subheader("📢 심화 토론 주제 (Risk-Based Approach):")
                st.markdown("""
                1. Category 5 Validation의 **과도한 노력**이 Validation 문서의 **품질 저하**를 유발할 수 있습니까?
                2. 리스크 기반 접근법(RBA) 관점에서 이 시스템을 Category 3 또는 4로 낮추려면, **Validation Plan을 어떻게 재설계**해야 합니까?
                """)
                
            # --- 3. SUCCESS: 적정 분류 ---
            elif (system_type == '단순 데이터 로깅/저장 기능' and validation_category in ['Category 3 (Non-Configured Software)', 'Category 4 (Configured Software)']) or \
                 (system_type == '복잡한 Process Parameter 계산/결정 로직 포함' and validation_category == 'Category 5 (Custom Application)'):
                st.success("✅ GAMP 5 Category 분류가 의도된 용도(URS)와 적절하게 일치합니다.")
                st.markdown(f"""
                **규제적 판단:** 시스템의 리스크 기반으로 Validation 노력을 효율화했습니다. **[근거 조항: GAMP 5 Second Edition - Risk-Based Approach Principle]**
                """)
                st.markdown(f"**📢 규제 근거:** {risk_based_ko}")

            # --- 4. WARNING: 선택 안 함 ---
            elif system_type == '선택 안 함' or validation_category == '선택 안 함':
                st.warning("항목을 모두 선택해 주세요.")

    with subtab_3_2:
        st.subheader('품질 시스템용 상용 소프트웨어 Validation 리스크 (FDA WL 기반)')

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
                **규제적 판단:** 품질 시스템(CAPA, Complaint 등)의 일부로 사용되는 **상용 소프트웨어(Excel 포함)**라도 **의도된 용도**에 대한 검증(Validation)이 필수입니다. 미검증 시, 기록의 무결성 위반으로 **FDA Warning Letter (21 CFR 820.70(i) 위반)**의 주요 원인이 됩니다.
                """)
                st.markdown("---")
                st.subheader("🔥 FDA Warning Letter (WL) 인용문")
                st.code(WL_SNIPPET_EN, language='text')
                st.info(f"**심사관 참고 번역:** {WL_SNIPPET_KO}")
                st.markdown("**(이미지 대체: Excel 스프레드시트 Validation 리스크)**")
                
                st.markdown("---")
                st.subheader("📢 심화 토론 주제 (21 CFR 820.70(i) / WL):")
                st.markdown("""
                1. **Excel 스프레드시트** Validation 시 **데이터 접근 통제(Access Control)**와 **버전 관리(Versioning)** 중 어떤 요소에 집중해야 합니까?
                2. 이 WL 사례를 근거로, 심사관이 요구해야 하는 **가장 중요한 Validation 문서**는 무엇이라고 판단하십니까?
                """)
                
                st.markdown(f"**📢 규제 근거 (21 CFR 820.70(i) - WL 기반):** {qs_validation_ko}")
            elif qs_tool == '선택 안 함' or validation_status_qs == '선택 안 함':
                st.warning("항목을 모두 선택해 주세요.")
            else:
                st.success("✅ 품질 시스템 소프트웨어 Validation 상태는 적절합니다.")
                st.markdown(f"**규제 근거 (21 CFR 820.70(i) - WL 기반):** {qs_validation_ko}")

# ==============================================================================
# 최종 푸터 및 저작권 정보 
# ==============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #808080; font-size: 0.8em; padding-top: 10px;">
    © 2026 Educational Simulation (MVP) | 개발 및 콘텐츠 총괄 책임자: 최영진
</div>
""", unsafe_allow_html=True)