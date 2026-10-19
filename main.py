import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import plotly.express as px

1. 페이지 기본 설정

st.set_page_config(
page_title="전국 고령화 단계구분도",
page_icon="🗺️",
layout="wide"
)

st.title("🗺️ 2026년 전국 시·군·구 고령화 단계구분도")
st.write("전국 읍·면·동 인구 데이터를 시·군·구 단위(행정구역 코드 5자리)로 집계하여 65세 이상 고령화율(%)을 단계구분도로 시각화합니다.")

2. 데이터 및 GeoJSON 로드 (캐싱을 적용하여 성능 최적화)

@st.cache_data
def load_data_and_geojson():
# 2-1. 인구 데이터 불러오기 (Raw GitHub URL 사용)
# pandas는 zip 파일 내부의 CSV를 자동으로 압축 해제하여 읽습니다.
pop_url = "https://raw.githubusercontent.com/andyji06/population/main/population_ts_yearly_gender.zip"
df = pd.read_csv(pop_url)

# '2026년' 데이터만 필터링
df_2026 = df[df['연도'] == 2026].copy()

# 2-2. GeoJSON 경계 데이터 불러오기
geojson_url = "https://raw.githubusercontent.com/andyji06/population/main/sigungu_kr.geojson.txt"
response = requests.get(geojson_url)
geojson_data = response.json()

return df_2026, geojson_data


try:
df_2026, geojson_data = load_data_and_geojson()
except Exception as e:
st.error(f"데이터를 불러오는 도중 오류가 발생했습니다: {e}")
st.stop()

3. 데이터 가공 및 고령화율 계산

동 코드를 문자열로 변환하고, 앞 5자리를 추출하여 시군구 코드로 설정

df_2026['코드_str'] = df_2026['코드'].astype(str).str.zfill(8)  # 8자리 포맷 맞춤
df_2026['sigungu_code'] = df_2026['코드_str'].str[:5]

열 이름 중 '계_'로 시작하는 전체 인구 열 필터링

total_cols = [c for c in df_2026.columns if c.startswith('계_')]

65세 이상 인구 열 생성 ('계_65세' ~ '계_99세' + '계_100세 이상')

senior_cols = [f"계_{i}세" for i in range(65, 100)]
if "계_100세 이상" in df_2026.columns:
senior_cols.append("계_100세 이상")
elif "계_100세이상" in df_2026.columns:
senior_cols.append("계_100세이상")

각 행(동)별 전체 인구수 및 65세 이상 인구수 합산

df_2026['전체인구'] = df_2026[total_cols].sum(axis=1)
df_2026['고령인구'] = df_2026[senior_cols].sum(axis=1)

시군구 코드(5자리) 기준으로 그룹화하여 합산

sigungu_df = df_2026.groupby('sigungu_code')[['전체인구', '고령인구']].sum().reset_index()

고령화율 (%) 계산

sigungu_df['고령화율'] = np.where(
sigungu_df['전체인구'] > 0,
(sigungu_df['고령인구'] / sigungu_df['전체인구']) * 100,
0
)

소수점 둘째 자리까지 반올림

sigungu_df['고령화율'] = sigungu_df['고령화율'].round(2)

4. GeoJSON 데이터에서 시군구 코드 및 지역명 매핑 추출

features = geojson_data.get('features', [])
geojson_map = []
for f in features:
props = f.get('properties', {})
code = str(props.get('코드', '')).zfill(5)
sido = props.get('시도', '')
sigungu = props.get('시군구', '')
full_name = f"{sido} {sigungu}".strip()
geojson_map.append({'sigungu_code': code, '시군구명': full_name})

df_geo_names = pd.DataFrame(geojson_map)

인구 데이터와 GeoJSON 지역명 결합

sigungu_df = pd.merge(sigungu_df, df_geo_names, on='sigungu_code', how='inner')

5. Plotly 단계구분도 (Choropleth Mapbox) 생성

fig = px.choropleth_mapbox(
sigungu_df,
geojson=geojson_data,
locations='sigungu_code',
featureidkey="properties.코드",
color='고령화율',
color_continuous_scale="Reds",  # 고령화율이 높을수록 진한 빨간색
range_color=(5, 35),            # 고령화율 색상 범주
hover_name='시군구명',
hover_data={'sigungu_code': False, '고령화율': ':.2f'},
labels={'고령화율': '고령화율 (%)', '시군구명': '지역명'},
mapbox_style="white-bg",        # 지도 배경 타일 없이 경계만 사용
center={"lat": 35.9, "lon": 127.8},  # 대한민국 중심 위치
zoom=6.2
)

fig.update_layout(
margin={"r": 0, "t": 30, "l": 0, "b": 0},
height=750,
coloraxis_colorbar=dict(
title="고령화율 (%)",
ticksuffix="%"
)
)

호버 레이블 가독성 및 경계선 설정 강화

fig.update_traces(
marker_line_width=0.5,
marker_line_color="gray"
)

6. Streamlit 화면 출력

st.plotly_chart(fig, use_container_width=True)

7. 주요 통계 요약 카드

st.markdown("---")
st.markdown("### 📊 2026년 전국 고령화 통계 요약")

col1, col2, col3 = st.columns(3)
avg_ratio = sigungu_df['고령화율'].mean()
max_row = sigungu_df.loc[sigungu_df['고령화율'].idxmax()]
min_row = sigungu_df.loc[sigungu_df['고령화율'].idxmin()]

col1.metric("전국 시·군·구 평균 고령화율", f"{avg_ratio:.1f}%")
col2.metric("최고 고령화 지역", f"{max_row['시군구명']}", f"{max_row['고령화율']}%")
col3.metric("최저 고령화 지역", f"{min_row['시군구명']}", f"{min_row['고령화율']}%")
