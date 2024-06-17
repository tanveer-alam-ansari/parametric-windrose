import os, sys, math
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import epw as ep
from tempfile import NamedTemporaryFile

st.set_page_config(page_title='Customizable Wind Rose Diagram', layout='wide')
STREAMLIT_SCRIPT_FILE_PATH = os.path.dirname(os.path.abspath(__file__))

def windrose_app():
    #creating sidebar
    sidebar = st.sidebar
    sidebar.header('Parametric Wind Rose')
    file = sidebar.file_uploader('Upload .epw file')

    if file is not None:
        #st.write(f"EPW File : {file.name}")
        local_file_path = os.path.join(STREAMLIT_SCRIPT_FILE_PATH, file.name)

        with open(local_file_path, "wb") as f:
            f.write(file.getbuffer())
        sidebar.success("EPW data acquired successfully")
        epw_data=ep.epw()
        epw_data.read(local_file_path)
        df_epw = epw_data.dataframe
        os.remove(local_file_path)
    #st.dataframe(df_epw)

    #create wind speed and direction dataframe

    try:
        df_wind = df_epw[['Month', 'Day', 'Hour', 'Wind Speed', 'Wind Direction']]
        max_speed = round(df_wind['Wind Speed'].max(), 2)
        min_speed = round(df_wind['Wind Speed'].min(), 2)
        period = round((max_speed - min_speed)/6, 2)

        #st.write(max_speed, min_speed, period)

        #Filer based on parametric variables
        #Slider for time range
        col_par,col_wr = st.columns([1, 1.6], gap='medium')
        col_par1,col_par2, col_par3 = col_par.columns(3, gap='medium')

        #Start time
        col_par1.subheader('Start Period')
        start_month = col_par1.slider('Month',1,12,1, key=1)
        month_day_pair = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31,
                        9:30, 10:31, 11:30, 12:31}
        start_day = col_par1.slider('Day',1,month_day_pair[start_month], key=2)
        start_hour = col_par1.slider('Hour',1,24,1, key=3)

        #End time
        col_par2.subheader('End Period')
        end_month = col_par2.slider('Month',1,12,12, key=4)
        end_day = col_par2.slider('Day',1,month_day_pair[end_month],month_day_pair[start_month], key=5)
        end_hour = col_par2.slider('Hour',1,24,24, key=6)

        #Filter database based on the time
        df_wind= df_wind[(df_wind['Month']>=start_month) &
                        (df_wind['Month']<=end_month)]
        df_wind= df_wind[(df_wind['Day']>=start_day) &               
                        (df_wind['Day']<=end_day)]
        df_wind= df_wind.drop(df_wind[(df_wind['Day']==start_day) &               
                        (df_wind['Hour']<start_hour)].index)
        df_wind= df_wind.drop(df_wind[(df_wind['Day']==end_day) &               
                        (df_wind['Hour']>end_hour)].index)


        #Interval paramtric selection
        col_par3.subheader('Speed Range')
        #start_speed = col_par3.slider('Start Speed',min_speed,max_speed,0.0, format="%f")
        min_speed = round(col_par3.slider('Min Speed',min_speed,float(math.ceil(max_speed)+6),
                                    min_speed, step=0.5), 2)
        max_speed = round(col_par3.slider(' Max Speed',min_speed,float(math.ceil(max_speed)+6),
                                    max_speed, step=0.5), 2)
        period = round((max_speed - min_speed)/6, 2)
        #st.write(min_speed, max_speed,period)

        df_wind= df_wind[(df_wind['Wind Speed']>=min_speed) &
                        (df_wind['Wind Speed']<=max_speed)]
        st.markdown('---')
        st.header('Filtered Wind Data')
        st.dataframe(df_wind)
        st.markdown('---')
        st.header('Full EPW Data')


        #creating bins for magnitudes and directions (directions in my dataset are in
        # degrees, I am converting them to direction abbreviations like N, NNW, NNE, S etc
        bins_mag= [min_speed, min_speed+period, min_speed+period*2, min_speed+period*3,
                min_speed+period*4, min_speed+period*5, min_speed+period*6]
        bins_mag_labels = [f'{min_speed:.2f}-{min_speed+period:.2f}',
                        f'{min_speed+period:.2f}-{min_speed+period*2:.2f}',
                        f'{min_speed+period*2:.2f}-{min_speed+period*3:.2f}',
                        f'{min_speed+period*3:.2f}-{min_speed+period*4:.2f}',
                        f'{min_speed+period*4:.2f}-{min_speed+period*5:.2f}',
                        f'{min_speed+period*5:.2f}-{min_speed+period*6:.2f}']
        #st.write(bins_mag, bins_mag_labels)

        bins_dir = [0, 11.25, 33.75, 56.25, 78.75,101.25,123.75,146.25,168.75,191.25,213.75,236.25,258.75,281.25,303.75,326.25,348.75,360]
        bins_dir_labels = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW','North']

        df_wind['mag_binned'] = pd.cut(df_wind['Wind Speed'],
                                    bins_mag, labels=bins_mag_labels)
        df_wind['dir_binned'] = pd.cut(df_wind['Wind Direction'],
                                    bins_dir, labels=bins_dir_labels, include_lowest=True)

        #create frequency based on wind speed and direction
        df_wind_grouped = df_wind.groupby(['mag_binned', 'dir_binned']).size().reset_index(name='freq')
        df_wind_grouped = df_wind_grouped.replace(r'North', 'N', regex=True)
        df_wind_grouped['percentage'] = df_wind_grouped['freq']/df_wind_grouped['freq'].sum()
        df_wind_grouped['percentage%'] = df_wind_grouped['percentage']*100
        #st.dataframe(df_wind_grouped)

        #plot the windrose using plotly
        #plotly color schemes
        color_schemes_dict = {'Plotly3': px.colors.sequential.Plotly3,
                        'Plotly3_r': px.colors.sequential.Plotly3_r,
                        'Viridis': px.colors.sequential.Viridis,
                        'Viridis_r': px.colors.sequential.Viridis_r,
                        'Inferno': px.colors.sequential.Inferno,
                        'Inferno_r': px.colors.sequential.Inferno_r,
                        'Plasma': px.colors.sequential.Plasma,
                        'Plasma_r': px.colors.sequential.Plasma_r,
                        'Rainbow': px.colors.sequential.Rainbow,
                        'Rainbow_r': px.colors.sequential.Rainbow_r,
                        'Sunset': px.colors.sequential.Sunset,
                        'Sunset_r': px.colors.sequential.Sunset_r,
                        'Ice': px.colors.sequential.ice,
                        'Ice_r': px.colors.sequential.ice_r,
                        'Mint': px.colors.sequential.Mint,
                        'Mint_r': px.colors.sequential.Mint_r,
                        'Brwnyl': px.colors.sequential.Brwnyl,
                        'Brwnyl_r': px.colors.sequential.Brwnyl_r,
                        'Blues': px.colors.sequential.Blues,
                        'Blues_r': px.colors.sequential.Blues_r,
                        'Greens': px.colors.sequential.Greens,
                        'Greens_r': px.colors.sequential.Greens_r,
                        'Greys': px.colors.sequential.Greys,
                        'Greys_r': px.colors.sequential.Greys_r,
                        'Oranges': px.colors.sequential.Oranges,
                        'Oranges_r': px.colors.sequential.Oranges_r,
                        'Purples': px.colors.sequential.Purples,
                        'Purples_r': px.colors.sequential.Purples_r,
                        'Reds': px.colors.sequential.Reds,
                        'Reds_r': px.colors.sequential.Reds_r}
        color_schemes_keys_list = list(color_schemes_dict.keys())
        color_schemes_values_list = list(color_schemes_dict.values())
        color_scheme = col_par.selectbox('Color Scheme', color_schemes_keys_list,
                                        index=color_schemes_values_list.index((px.colors.sequential.Plasma_r)))

        #plotly color templates
        color_templates_list =  ['ggplot2', 'seaborn', 'simple_white', 'plotly','plotly_white', 'plotly_dark',
                            'presentation', 'none']
        color_template = col_par.selectbox('Color Template', color_templates_list,
                                        index=color_templates_list.index('plotly'))
        
        fig = px.bar_polar(df_wind_grouped, r='percentage%', theta='dir_binned',
                        color='mag_binned', template=color_template,
                        color_discrete_sequence = color_schemes_dict[color_scheme],
                        width=600, height=500)
        fig.update_layout(polar = dict(radialaxis = dict(showticklabels = False)),
                        font_size=15,
                        legend_font_size=15,
                        legend_title="Wind Speed (m/s)",
                        legend_title_font_size=15)

        col_wr.plotly_chart(fig)
        st.dataframe(df_epw)

        #reset button
        #col_par3.markdown('\n')
        #reset_button = col_par3.button('Reset')
        #return reset_button   

    except:
        st.error("Upload appropriate weather file !")

if __name__ == "__main__":
    windrose_app()
    #if reset:
        #st.session_state.key = None
        #windrose_app()
