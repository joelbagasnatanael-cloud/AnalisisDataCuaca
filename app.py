# -*- coding: utf-8 -*-
"""
Weather Dashboard Streamlit Application
=========================================
Dashboard interaktif untuk visualisasi data historis cuaca
menggunakan Altair untuk tampilan yang elegant dan interactive.
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta
import os

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
    <style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Metric cards */
    .metric-container {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    /* Header */
    h1 {
        color: #1f77b4;
        text-align: center;
        margin-bottom: 30px;
    }
    
    h2 {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
    }
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background: #ecf0f1;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# LOAD DATA (CACHED)
# =============================================================================

@st.cache_data
def load_weather_data():
    """Load CSV file dengan error handling."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(base_dir, "weather_history_2025_2026.csv")

    if not os.path.exists(csv_file):
        return None, f"❌ File '{csv_file}' tidak ditemukan di folder {os.getcwd()}"

    try:
        df = pd.read_csv(csv_file)
        
        # Validasi kolom
        required_cols = ['datetime', 'temp_c', 'humidity', 'wind_speed', 
                        'pressure', 'clouds_pct', 'weather_main']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return None, f"❌ Kolom tidak lengkap: {missing_cols}"
        
        # Convert datetime
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        df = df.sort_values('datetime')
        
        # Handle missing values
        df['temp_c'] = df['temp_c'].fillna(df['temp_c'].mean())
        df['humidity'] = df['humidity'].fillna(df['humidity'].mean())
        df['wind_speed'] = df['wind_speed'].fillna(0)
        df['pressure'] = df['pressure'].fillna(df['pressure'].mean())
        df['clouds_pct'] = df['clouds_pct'].fillna(0)
        
        # Create date column for grouping
        df['date'] = df['datetime'].dt.date
        
        return df, "✅ Data berhasil dimuat"
    
    except Exception as e:
        return None, f"❌ Error membaca file: {str(e)}"

# =============================================================================
# MAIN APP
# =============================================================================

st.title("🌤️ Weather Dashboard (Chicago 2025-2026)")

# Load data
df, message = load_weather_data()

if df is None:
    st.error(message)
    st.stop()

# =============================================================================
# SIDEBAR - FILTER
# =============================================================================

with st.sidebar:
    st.header("⚙️ Filter & Controls")
    
    # Date range selector
    min_date = df['datetime'].min().date()
    max_date = df['datetime'].max().date()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "📅 Tanggal Mulai",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
    
    with col2:
        end_date = st.date_input(
            "📅 Tanggal Akhir",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    
    # Validate date range
    if start_date > end_date:
        st.warning("⚠️ Tanggal mulai harus lebih kecil dari tanggal akhir")
        st.stop()
    
    st.markdown("---")
    st.info(f"📊 Total data: {len(df):,} records\n"
            f"📅 Range: {min_date} to {max_date}")

# Filter data berdasarkan date range
df_filtered = df[(df['datetime'].dt.date >= start_date) & 
                 (df['datetime'].dt.date <= end_date)].copy()

if len(df_filtered) == 0:
    st.error("❌ Tidak ada data untuk tanggal yang dipilih")
    st.stop()

# =============================================================================
# TABS
# =============================================================================

tab1, tab2 = st.tabs(["📈 Overview", "📊 Dashboard"])

# =========================================================================
# TAB 1: OVERVIEW (SEDERHANA)
# =========================================================================

with tab1:
    st.header("Overview Cuaca")
    
    # Calculate statistics for filtered data daily
    daily_stats = df_filtered.groupby('date').agg({
        'temp_c': ['min', 'max', 'mean'],
        'humidity': 'mean',
        'wind_speed': 'mean',
        'pressure': 'mean',
        'clouds_pct': 'mean'
    }).reset_index()
    daily_stats.columns = ['date', 'temp_min', 'temp_max', 'temp_mean',
                           'humidity_mean', 'wind_mean', 'pressure_mean', 'clouds_mean']
    
    # Metric Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_temp = df_filtered['temp_c'].mean()
        st.metric("🌡️ Rata-rata Temperatur", f"{avg_temp:.1f}°C")
    
    with col2:
        avg_humidity = df_filtered['humidity'].mean()
        st.metric("💧 Rata-rata Kelembaban", f"{avg_humidity:.1f}%")
    
    with col3:
        avg_wind = df_filtered['wind_speed'].mean()
        st.metric("💨 Rata-rata Kecepatan Angin", f"{avg_wind:.2f} m/s")
    
    with col4:
        avg_pressure = df_filtered['pressure'].mean()
        st.metric("🔽 Rata-rata Tekanan", f"{avg_pressure:.0f} hPa")
    
    st.markdown("---")
    
    # Main Chart - Temperature Timeline
    st.subheader("Grafik Temperatur (Hourly)")
    
    try:
        # Prepare data for hourly chart
        df_hourly = df_filtered[['datetime', 'temp_c']].copy()
        df_hourly['temp_c'] = df_hourly['temp_c'].astype(float)
        
        chart_temp = alt.Chart(df_hourly).mark_line(point=True, color='#e74c3c').encode(
            x=alt.X('datetime:T', title='Waktu'),
            y=alt.Y('temp_c:Q', title='Temperatur (°C)'),
            tooltip=['datetime:T', 'temp_c:Q']
        ).properties(
            height=300,
            width='container'
        ).interactive()
        
        st.altair_chart(chart_temp, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error membuat chart temperatur: {str(e)}")
    
    st.markdown("---")
    
    # Statistics Table
    st.subheader("📊 Statistik Harian")
    st.dataframe(
        daily_stats.style.format({
            'temp_min': '{:.1f}',
            'temp_max': '{:.1f}',
            'temp_mean': '{:.1f}',
            'humidity_mean': '{:.1f}',
            'wind_mean': '{:.2f}',
            'pressure_mean': '{:.0f}',
            'clouds_mean': '{:.1f}'
        }),
        use_container_width=True,
        hide_index=True
    )

# =========================================================================
# TAB 2: DASHBOARD (INDAH DENGAN ALTAIR)
# =========================================================================

with tab2:
    st.header("Dashboard Analisis Cuaca")
    
    # Create daily aggregated data for most charts
    daily_data = df_filtered.groupby('date').agg({
        'temp_c': ['min', 'max', 'mean'],
        'humidity': 'mean',
        'wind_speed': ['mean', 'max'],
        'pressure': 'mean',
        'clouds_pct': 'mean'
    }).reset_index()
    
    daily_data.columns = ['date', 'temp_min', 'temp_max', 'temp_mean',
                          'humidity_mean', 'wind_mean', 'wind_max', 
                          'pressure_mean', 'clouds_mean']
    
    # Melt for easier plotting
    daily_data['date'] = pd.to_datetime(daily_data['date'])
    
    # =====================================================================
    # Chart 1: Temperature (Min, Max, Average)
    # =====================================================================
    
    st.subheader("1️⃣ Grafik Temperatur (Min, Max, Rata-rata)")
    
    try:
        # Melt temperature data
        temp_melted = daily_data.melt(
            id_vars=['date'],
            value_vars=['temp_min', 'temp_max', 'temp_mean'],
            var_name='type',
            value_name='temperature'
        )
        
        temp_melted['type'] = temp_melted['type'].map({
            'temp_min': 'Minimum',
            'temp_max': 'Maximum',
            'temp_mean': 'Rata-rata'
        })
        
        chart1 = alt.Chart(temp_melted).mark_line(point=True).encode(
            x=alt.X('date:T', title='Tanggal'),
            y=alt.Y('temperature:Q', title='Temperatur (°C)'),
            color=alt.Color('type:N', title='Tipe', scale=alt.Scale(
                domain=['Minimum', 'Maximum', 'Rata-rata'],
                range=['#3498db', '#e74c3c', '#f39c12']
            )),
            tooltip=['date:T', 'type:N', 'temperature:Q']
        ).properties(
            height=300,
            width='container'
        ).interactive()
        
        st.altair_chart(chart1, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error Chart 1: {str(e)}")
    
    # =====================================================================
    # Chart 2: Humidity (Line Chart)
    # =====================================================================
    
    st.subheader("2️⃣ Grafik Kelembaban Udara")
    
    try:
        chart2 = alt.Chart(daily_data).mark_area(
            line=True,
            point=True,
            opacity=0.7,
            color='#3498db'
        ).encode(
            x=alt.X('date:T', title='Tanggal'),
            y=alt.Y('humidity_mean:Q', title='Kelembaban (%)', scale=alt.Scale(domain=[0, 100])),
            tooltip=['date:T', 'humidity_mean:Q']
        ).properties(
            height=250,
            width='container'
        ).interactive()
        
        st.altair_chart(chart2, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error Chart 2: {str(e)}")
    
    # =====================================================================
    # Chart 3: Wind Speed
    # =====================================================================
    
    st.subheader("3️⃣ Grafik Kecepatan Angin")
    
    try:
        # Melt wind data
        wind_melted = daily_data.melt(
            id_vars=['date'],
            value_vars=['wind_mean', 'wind_max'],
            var_name='type',
            value_name='speed'
        )
        
        wind_melted['type'] = wind_melted['type'].map({
            'wind_mean': 'Rata-rata',
            'wind_max': 'Maksimum'
        })
        
        chart3 = alt.Chart(wind_melted).mark_bar().encode(
            x=alt.X('date:T', title='Tanggal'),
            y=alt.Y('speed:Q', title='Kecepatan Angin (m/s)'),
            color=alt.Color('type:N', title='Tipe', scale=alt.Scale(
                domain=['Rata-rata', 'Maksimum'],
                range=['#2ecc71', '#e74c3c']
            )),
            xOffset='type:N',
            tooltip=['date:T', 'type:N', 'speed:Q']
        ).properties(
            height=250,
            width='container'
        ).interactive()
        
        st.altair_chart(chart3, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error Chart 3: {str(e)}")
    
    # =====================================================================
    # Chart 4: Atmospheric Pressure
    # =====================================================================
    
    st.subheader("4️⃣ Grafik Tekanan Udara")
    
    try:
        chart4 = alt.Chart(daily_data).mark_line(
            point=True,
            color='#9b59b6',
            size=2
        ).encode(
            x=alt.X('date:T', title='Tanggal'),
            y=alt.Y('pressure_mean:Q', title='Tekanan (hPa)'),
            tooltip=['date:T', 'pressure_mean:Q']
        ).properties(
            height=250,
            width='container'
        ).interactive()
        
        st.altair_chart(chart4, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error Chart 4: {str(e)}")
    
    # =====================================================================
    # Chart 5: Cloud Coverage
    # =====================================================================
    
    st.subheader("5️⃣ Grafik Persentase Awan")
    
    try:
        chart5 = alt.Chart(daily_data).mark_area(
            line=True,
            point=True,
            opacity=0.6,
            color='#95a5a6'
        ).encode(
            x=alt.X('date:T', title='Tanggal'),
            y=alt.Y('clouds_mean:Q', title='Persentase Awan (%)', 
                   scale=alt.Scale(domain=[0, 100])),
            tooltip=['date:T', 'clouds_mean:Q']
        ).properties(
            height=250,
            width='container'
        ).interactive()
        
        st.altair_chart(chart5, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error Chart 5: {str(e)}")
    
    # =====================================================================
    # Chart 6: Trend Analysis (7-day Moving Average)
    # =====================================================================
    
    st.subheader("6️⃣ Analisis Tren (Moving Average 7-hari)")
    
    try:
        # Calculate 7-day moving average
        daily_data_sorted = daily_data.sort_values('date').reset_index(drop=True)
        daily_data_sorted['temp_ma7'] = daily_data_sorted['temp_mean'].rolling(window=7, min_periods=1).mean()
        daily_data_sorted['humidity_ma7'] = daily_data_sorted['humidity_mean'].rolling(window=7, min_periods=1).mean()
        daily_data_sorted['wind_ma7'] = daily_data_sorted['wind_mean'].rolling(window=7, min_periods=1).mean()
        
        # Normalize for visualization (0-100 scale)
        daily_data_sorted['temp_norm'] = ((daily_data_sorted['temp_ma7'] - daily_data_sorted['temp_ma7'].min()) / 
                                          (daily_data_sorted['temp_ma7'].max() - daily_data_sorted['temp_ma7'].min() + 0.1) * 100)
        daily_data_sorted['humidity_norm'] = daily_data_sorted['humidity_ma7']
        daily_data_sorted['wind_norm'] = ((daily_data_sorted['wind_ma7'] - daily_data_sorted['wind_ma7'].min()) / 
                                          (daily_data_sorted['wind_ma7'].max() - daily_data_sorted['wind_ma7'].min() + 0.1) * 100)
        
        # Melt for layered chart
        trend_melted = daily_data_sorted.melt(
            id_vars=['date'],
            value_vars=['temp_norm', 'humidity_norm', 'wind_norm'],
            var_name='metric',
            value_name='normalized_value'
        )
        
        trend_melted['metric'] = trend_melted['metric'].map({
            'temp_norm': 'Temperatur',
            'humidity_norm': 'Kelembaban',
            'wind_norm': 'Kecepatan Angin'
        })
        
        chart6 = alt.Chart(trend_melted).mark_line(point=True, size=2).encode(
            x=alt.X('date:T', title='Tanggal'),
            y=alt.Y('normalized_value:Q', title='Nilai Ternormalisasi (0-100)'),
            color=alt.Color('metric:N', title='Metrik', scale=alt.Scale(
                domain=['Temperatur', 'Kelembaban', 'Kecepatan Angin'],
                range=['#e74c3c', '#3498db', '#2ecc71']
            )),
            tooltip=['date:T', 'metric:N', 'normalized_value:Q']
        ).properties(
            height=300,
            width='container'
        ).interactive()
        
        st.altair_chart(chart6, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error Chart 6: {str(e)}")

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.info(f"📊 Total Records: {len(df_filtered):,}")

with col2:
    st.info(f"📅 Period: {start_date} to {end_date}")

with col3:
    st.info(f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.caption("Weather Dashboard | Data from OpenWeatherMap Historical API | Chicago, Illinois")
