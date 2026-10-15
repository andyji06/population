import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인 (따뜻한 톤)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="우리 동네 인구 피라미드",
    page_icon="🏘️",
    layout="wide"
)

# 따뜻한 느낌의 CSS 스타일 적용
st.markdown("""
    <style>
    .main {
        background-color: #FFFDF9;
    }
    h1 {
        color: #8B4513;
        font-family: 'Nanum Gothic', sans-serif;
    }
    .stSelectbox label {
        color: #5C4033 !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_unsafe_html=True)

st.title("🏘️ 우리 동네 인구 피라미드")
st.write("우리 동네의 나이별, 성별 인구 구조를 따뜻한 시선으로 살펴봅니다.")
st.markdown("---")

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 (캐싱 적용으로 속도 최적화)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # GitHub blob 주소를 원본(raw) 파일 다운로드 주소로 변환
    url = "https://github.com/andyji06/population/raw/main/population_ts_yearly_gender.zip"
    
    # pandas는 zip 압축 파일 내의 CSV를 자동으로 읽을 수 있습니다.
    df = pd.read_csv(url, compression='zip')
    
    # 가장 최신 연도 데이터만 필터링
    latest_year = df['연도'].max()
    df_latest = df[df['연도'] == latest_year].copy()
    
    return df_latest, latest_year

# 데이터 로딩 상태 표시
with st.spinner("지역별 인구 데이터를 불러오는 중입니다... ☕"):
    df, latest_year = load_data()

st.success(f"기준 연도: **{latest_year}년** 최신 데이터 로드 완료!")

# -----------------------------------------------------------------------------
# 3. 드롭다운 선택 상자 (시도 → 시군구 → 동)
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    sido_list = sorted(df['시도'].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

# 선택한 시·도에 해당하는 시군구 목록 추출
df_sido = df[df['시도'] == selected_sido]

with col2:
    sigungu_list = sorted(df_sido['시군구'].dropna().unique())
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

# 선택한 시군구에 해당하는 동 목록 추출
df_sigungu = df_sido[df_sido['시군구'] == selected_sigungu]

with col3:
    dong_list = sorted(df_sigungu['동'].dropna().unique())
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)

# 최종 선택된 동네 데이터 1행 추출
target_row = df_sigungu[df_sigungu['동'] == selected_dong].iloc[0]

# -----------------------------------------------------------------------------
# 4. 나이 및 남녀 인구 데이터 정제
# -----------------------------------------------------------------------------
# 나이 라벨 생성: '0세', '1세', ..., '99세', '100세 이상' (정확히 0세가 index 0)
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

male_pop = []
female_pop = []

# 데이터 프레임 열에서 남/여 인구수 추출
for age in age_labels:
    m_col = f"남_{age}"
    f_col = f"여_{age}"
    
    # 해당 열의 값이 없으면 0 처리
    m_val = target_row[m_col] if m_col in target_row else 0
    f_val = target_row[f_col] if f_col in target_row else 0
    
    male_pop.append(m_val)
    female_pop.append(f_val)

# 남성 인구는 피라미드 왼쪽(음수)으로 배치
male_pop_neg = [-val for val in male_pop]

# -----------------------------------------------------------------------------
# 5. Plotly 가로 막대 그래프 (인구 피라미드)
# -----------------------------------------------------------------------------
fig = go.Figure()

# 남성 막대 그래프 (왼쪽, 포근한 블루 톤)
fig.add_trace(go.Bar(
    y=age_labels,
    x=male_pop_neg,
    name='남성',
    orientation='h',
    hoverinfo='text',
    # 호버(마우스 올렸을 때) 시 음수가 아닌 실제 인구수 표시
    text=[f"남성 ({age}): {abs(val):,}명" for age, val in zip(age_labels, male_pop)],
    marker=dict(color='#6C9BCF')
))

# 여성 막대 그래프 (오른쪽, 따뜻한 핑크/코랄 톤)
fig.add_trace(go.Bar(
    y=age_labels,
    x=female_pop,
    name='여성',
    orientation='h',
    hoverinfo='text',
    text=[f"여성 ({age}): {val:,}명" for age, val in zip(age_labels, female_pop)],
    marker=dict(color='#FF8E9E')
))

# 축 및 레이아웃 설정
fig.update_layout(
    title=dict(
        text=f"<b>[{selected_sido} {selected_sigungu} {selected_dong}] 인구 피라미드</b>",
        font=dict(size=20, color='#5C4033')
    ),
    barmode='relative',
    bargap=0.1,
    height=800,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(255,253,249,1)',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    # X축: 음수 눈금을 양수로 표시하고 천 단위 쉼표 적용
    xaxis=dict(
        title="인구수 (명)",
        tickformat=",d",
        tickvals=[-x for x in range(0, max(max(male_pop), max(female_pop)) + 1, 100 if max(max(male_pop), max(female_pop)) < 1000 else 500)] + 
                 [x for x in range(0, max(max(male_pop), max(female_pop)) + 1, 100 if max(max(male_pop), max(female_pop)) < 1000 else 500)],
        ticktext=[f"{abs(x):,}" for x in range(0, max(max(male_pop), max(female_pop)) + 1, 100 if max(max(male_pop), max(female_pop)) < 1000 else 500)] + 
                 [f"{x:,}" for x in range(0, max(max(male_pop), max(female_pop)) + 1, 100 if max(max(male_pop), max(female_pop)) < 1000 else 500)]
    ),
    # Y축: 순서를 뒤집지 않고 age_labels 배열 순서 그대로 0세가 맨 아래에 위치하도록 지정
    yaxis=dict(
        title="연령",
        type='category',
        categoryorder='array',
        categoryarray=age_labels,  # 0세 -> 100세 이상 순서 고정 (0세가 최하단)
        autorange=True
    )
)

# -----------------------------------------------------------------------------
# 6. 결과 출력
# -----------------------------------------------------------------------------
st.plotly_chart(fig, use_container_width=True)

# 요약 정보 카드
total_m = sum(male_pop)
total_f = sum(female_pop)
total_pop = total_m + total_f

m_col, f_col, t_col = st.columns(3)
m_col.metric("총 남성 인구", f"{total_m:,} 명")
f_col.metric("총 여성 인구", f"{total_f:,} 명")
t_col.metric("총 지역 인구", f"{total_pop:,} 명")
