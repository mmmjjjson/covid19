import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title = '코로나19 한국 대시보드', layout = 'wide')
st.title('KR 코로나 19 한국 감염자 대시보드')

# 파일 업로드 - csc파일만
uploaded_confirmed = st.file_uploader('확진자 CSV 파일 업로드', type = ['csv'])
uploaded_deaths = st.file_uploader('사망자 CSV 파일 업로드', type = ['csv'])
uploaded_recovered = st.file_uploader('회복자 CSV 파일 업로드', type = ['csv'])

# 모든 파일이 업로드 되었다면 실행
if uploaded_confirmed and uploaded_deaths and uploaded_recovered:
    # csv 파일 내용 읽어 데이터프레임으로 저장
    df_confirmed = pd.read_csv(uploaded_confirmed) # 확진자 데이터프레임
    df_deaths = pd.read_csv(uploaded_deaths) # 사망자 데이터프레임
    df_recovered = pd.read_csv(uploaded_recovered) # 회복자 데이터프레임

    def get_korea_data(df, value_name):
        korea_df = df[df['Country/Region'] == 'Korea, South']
        korea_df = korea_df.drop(columns = ['Province/State', 'Country/Region', 'Lat', 'Long'])
        korea_series = korea_df.sum().reset_index()
        korea_series.columns = ['날짜', value_name]
        # 날짜 형식을 datetime으로 변환
        korea_series['날짜'] = pd.to_datetime(korea_series['날짜'], format = '%m/%d/%y')
        return korea_series

    df_confirmed = get_korea_data(df_confirmed, '확진자')
    df_deaths = get_korea_data(df_deaths, '사망자')
    df_recovered = get_korea_data(df_recovered, '회복자')

    df_merged = df_confirmed.merge(df_deaths, on = '날짜').merge(df_recovered, on = '날짜')

    # 병합 데이터 날짜 부분의 시간 제거
    df_merged['날짜'] = df_merged['날짜'].dt.date

    df_merged['신규 확진자'] = df_merged['확진자'].diff().fillna(0).astype(int)
    df_merged['신규 사망자'] = df_merged['사망자'].diff().fillna(0).astype(int)
    df_merged['신규 회복자'] = df_merged['회복자'].diff().fillna(0).astype(int)

    # 탭 3개 구성(감염 추이, 통계 요약, 비율 분석)
    tab1, tab2, tab3 = st.tabs(['감염 추이', '통계 요약', '비율 분석'])

    with tab1:
        st.subheader('누적 추이 그래프')
        selected = st.multiselect('표시할 항목을 선택하세요.', ['확진자', '사망자', '회복자'], default = ['확진자', '회복자'])
                                                                                    # 기본값: 확진자, 회복자 그래프 나오게
        if selected: # 선택된 값이 있다면 그래프 그리기
            fig = px.line(df_merged, x = '날짜', y = selected, markers = True)
            st.plotly_chart(fig, use_container_width = True) # 부모 너비 기준
        
        st.subheader('일일 증가량 그래프')
        selected_new = st.multiselect('표시할 항목(신규)을 선택하세요.', ['신규 확진자', '신규 사망자', '신규 회복자'])
        if selected_new:
            fig_new = px.bar(df_merged, x = '날짜', y = selected_new)
            st.plotly_chart(fig_new, use_container_width = True)
    
    with tab2:
        st.subheader('일자별 통계 테이블')
        st.dataframe(df_merged.tail(10), use_container_width = True)
                               # 끝에서부터 10개
    
    with tab3:
        st.subheader('최신일 기준 회복률 / 치명률')
        latest = df_merged.iloc[-1] # 최신 날짜가 맨 마지막이므로
        confirmed = latest['확진자']
        deaths = latest['사망자']
        recovered = latest['회복자']
        recovered_rate = (recovered / confirmed) * 100 if confirmed else 0 # 회복률 = (회복자 / 확진자) * 100
                                                       # confirmed에 값이 있으면 계산하고 없으면 0
        deaths_rate = (deaths / confirmed) * 100 if confirmed else 0

        col1, col2 = st.columns(2) # 열을 두 칸 만들고 각각의 이름을 col1, col2로 정함
        col1.metric('회복률', f'{recovered_rate:.2f} %')
        col2.metric('치명률', f'{deaths_rate:.2f} %')

        st.subheader('감염자 분포 비율')
        # 원형 그래프 원본이 될 데이터프레임 생성
        pie_df = pd.DataFrame({
            '구분' : ['회복자', '사망자', '격리중'],
            '인원수' : [recovered, deaths, confirmed - recovered - deaths]
        })
                      # (사용할 데이터, names, values)
        fig_pie = px.pie(pie_df, names ='구분', values = '인원수', title = '감염자 분포')
        st.plotly_chart(fig_pie, use_container_width = True)

else:
    st.info('3개의 CSV 파일(확진자, 사망자, 회복자)을 모두 업로드 해주세요.')