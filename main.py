import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 페이지 기본 설정 (타이틀, 레이아웃)
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# 2. 데이터 불러오기 함수 (캐싱을 통해 속도 최적화)
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/first2022-cyber/contents/main/population_ts_yearly_gender.zip"
    # pandas는 zip 파일 내의 CSV를 자동으로 압축 해제해서 읽습니다.
    df = pd.read_csv(url)
    
    # 데이터에 존재하는 가장 최신 연도만 추출
    max_year = df['연도'].max()
    df_latest = df[df['연도'] == max_year].copy()
    
    return df_latest, max_year

# 앱 실행 시 타이틀 및 안내 메시지
st.title("🏡 우리 동네 인구 피라미드")
st.write("원하는 지역을 선택하면 최신 인구구조를 따뜻한 인구 피라미드 그래프와 주요 지표로 보여드립니다.")

# 데이터 로드
try:
    df, latest_year = load_data()
    st.info(f"💡 현재 **{latest_year}년** 기준 인구 데이터를 바탕으로 조회합니다.")
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 3. 지역 선택 드롭다운 (시도 -> 시군구 -> 동)
col1, col2, col3 = st.columns(3)

with col1:
    sido_list = sorted(df['시도'].dropna().unique())
    selected_sido = st.selectbox("1️⃣ 시·도 선택", sido_list)

# 선택한 시·도에 해당하는 시군구 목록 필터링
df_sido = df[df['시도'] == selected_sido]

with col2:
    sigungu_list = sorted(df_sido['시군구'].dropna().unique())
    selected_sigungu = st.selectbox("2️⃣ 시·군·구 선택", sigungu_list)

# 선택한 시군구에 해당하는 동 목록 필터링
df_sigungu = df_sido[df_sido['시군구'] == selected_sigungu]

with col3:
    dong_list = sorted(df_sigungu['동'].dropna().unique())
    selected_dong = st.selectbox("3️⃣ 읍·면·동 선택", dong_list)

# 4. 최종 선택된 동네 데이터 추출
selected_row = df_sigungu[df_sigungu['동'] == selected_dong]

if selected_row.empty:
    st.warning("선택한 지역의 데이터가 없습니다.")
    st.stop()

# 5. 연령대 라벨 및 남/여 인구 데이터 정리
# 0세부터 99세까지 + '100세 이상' 라벨 생성
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]
age_numbers = list(range(101))  # 평균 연령 계산용 (100세 이상은 100으로 가중치 부여)

male_pop = []
female_pop = []

row = selected_row.iloc[0]

for age in age_labels:
    male_col = f"남_{age}"
    female_col = f"여_{age}"
    
    # 데이터에 컬럼이 있으면 가져오고 없으면 0으로 처리
    m_val = row[male_col] if male_col in row and not pd.isna(row[male_col]) else 0
    f_val = row[female_col] if female_col in row and not pd.isna(row[female_col]) else 0
    
    male_pop.append(m_val)
    female_pop.append(f_val)

# 연령별 총 인구 계산
total_pop_by_age = [m + f for m, f in zip(male_pop, female_pop)]
total_pop = sum(total_pop_by_age)

if total_pop == 0:
    st.warning("선택한 지역의 총 인구가 0명입니다.")
    st.stop()

# 6. 통계 지표 계산 (평균연령, 고령화율, 유소년 비율)
# 평균 연령 = sum(나이 * 해당 나이 인구) / 총인구
weighted_age_sum = sum(age * pop for age, pop in zip(age_numbers, total_pop_by_age))
avg_age = weighted_age_sum / total_pop

# 65세 이상 인구 및 고령화율 (%)
senior_pop = sum(total_pop_by_age[65:])
elderly_ratio = (senior_pop / total_pop) * 100

# 0~14세 유소년 인구 및 유소년 비율 (%)
child_pop = sum(total_pop_by_age[:15])
child_ratio = (child_pop / total_pop) * 100

# 7. 상단 지표 카드 출력 (그래프 위)
st.markdown("### 📊 주요 인구 지표")
m_col1, m_col2, m_col3 = st.columns(3)

m_col1.metric("👥 총인구", f"{total_pop:,} 명")
m_col2.metric("🎂 평균연령", f"{avg_age:.1f} 세")

# 고령화율이 20% 이상인 경우 초고령사회 경고 표시 추가
if elderly_ratio >= 20:
    m_col3.metric("🧓 고령화율 (65세+)", f"{elderly_ratio:.1f} %", delta="⚠️ 초고령 (20% 초과)", delta_color="inverse")
else:
    m_col3.metric("🧓 고령화율 (65세+)", f"{elderly_ratio:.1f} %")

st.write("")  # 여백 추가

# 8. Plotly 가로 막대 그래프 생성 (피라미드)
# 피라미드 표현을 위해 남성 인구수는 음수로 변환
male_pop_neg = [-x for x in male_pop]

fig = go.Figure()

# 남성 막대 그래프 (왼쪽, 따뜻한 코랄/오렌지 톤)
fig.add_trace(go.Bar(
    y=age_labels,
    x=male_pop_neg,
    name='남성',
    orientation='h',
    marker_color='#FF8A65',
    hovertemplate='<b>%{y} 남성</b>: %{customdata:,}명<extra></extra>',
    customdata=male_pop
))

# 여성 막대 그래프 (오른쪽, 따뜻한 핑크/버건디 톤)
fig.add_trace(go.Bar(
    y=age_labels,
    x=female_pop,
    name='여성',
    orientation='h',
    marker_color='#EC407A',
    hovertemplate='<b>%{y} 여성</b>: %{x:,}명<extra></extra>'
))

# 그래프 레이아웃 설정
max_val = max(max(male_pop) if male_pop else 1, max(female_pop) if female_pop else 1)
tick_interval = max(1, int(max_val / 4))
tick_vals = list(range(-((max_val // tick_interval) + 1) * tick_interval, 
                       ((max_val // tick_interval) + 2) * tick_interval, 
                       tick_interval))
tick_text = [str(abs(x)) for x in tick_vals]

fig.update_layout(
    title=dict(
        text=f"<b>{selected_sido} {selected_sigungu} {selected_dong}</b> 인구 피라미드",
        x=0.5,
        font=dict(size=20)
    ),
    barmode='overlay',
    xaxis=dict(
        title="인구수 (명)",
        tickvals=tick_vals,
        ticktext=tick_text,
        gridcolor='#F0F0F0'
    ),
    yaxis=dict(
        title="연령",
        type='category',
        categoryorder='array',
        categoryarray=age_labels,
        dtick=5  # 눈금을 5세 단위로 표시하여 가독성 확보
    ),
    legend=dict(
        orient='h',
        yanchor='bottom',
        y=1.02,
        xanchor='right',
        x=1
    ),
    plot_bgcolor='white',
    height=800,
    margin=dict(l=50, r=50, t=100, b=50)
)

# 스트림릿 화면에 그래프 출력
st.plotly_chart(fig, use_container_width=True)

# 9. 피라미드 하단 자동 한 줄 분석 메시지
st.markdown("---")
st.markdown("### 💬 이 동네는 어떤 특성을 갖고 있을까요?")

# 아이와 어르신 비율에 따른 자동 문구 생성
if child_ratio > elderly_ratio:
    desc = f"🎈 **어르신보다 아이들이 더 많은 젊은 동네입니다!** (유소년 비율 {child_ratio:.1f}% > 고령화율 {elderly_ratio:.1f}%)"
elif elderly_ratio > child_ratio:
    desc = f"🏡 **아이들보다 어르신이 상대적으로 더 많은 동네입니다.** (고령화율 {elderly_ratio:.1f}% > 유소년 비율 {child_ratio:.1f}%)"
else:
    desc = f"⚖️ **유소년 비율과 고령인구 비율이 비슷한 균형 잡힌 동네입니다.** (각각 {elderly_ratio:.1f}%)"

st.info(desc)
