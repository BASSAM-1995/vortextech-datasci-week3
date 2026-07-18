import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ======================
# ⚙️ Page Config
# ======================
st.set_page_config(
    page_title="VortexTech Dashboard",
    page_icon="🚀",
    layout="wide"
)

# ======================
# 🎨 Custom CSS
# ======================
st.markdown("""
<style>
.main {
    background-color: #f8f9fa;
}
.card {
    padding: 20px;
    border-radius: 10px;
    background-color: white;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# ======================
# 📂 Load Data (PRO)
# ======================
@st.cache_data(ttl=3600)
def load_data():
    try:
        file_path = os.path.join(os.path.dirname(__file__), "cleaned_final.csv")

        if not os.path.exists(file_path):
            st.error(f"❌ File not found: {file_path}")
            return pd.DataFrame()

        df = pd.read_csv(file_path)

        # تنظيف
        df['funding_total_usd'] = pd.to_numeric(df['funding_total_usd'], errors='coerce')
        df = df.dropna(subset=['funding_total_usd'])

        return df

    except Exception as e:
        st.error(f"🔥 Error loading data: {e}")
        return pd.DataFrame()


df = load_data()

# ======================
# 🏠 Title
# ======================
st.title("🚀 VortexTech Investment Dashboard")

if df.empty:
    st.stop()

# ======================
# 🔧 Sidebar Filters
# ======================
st.sidebar.header("🔧 Filters")

# Country Filter
countries = ['All'] + sorted(df['country_code'].dropna().unique())
selected_country = st.sidebar.selectbox("🌍 Country", countries)

# Funding Range
min_val = float(df['funding_total_usd'].min())
max_val = float(df['funding_total_usd'].max())

funding_range = st.sidebar.slider(
    "💰 Funding Range",
    min_value=min_val,
    max_value=max_val,
    value=(min_val, max_val),
    format="$%.0f"
)

# Apply Filters
filtered_df = df.copy()

if selected_country != 'All':
    filtered_df = filtered_df[filtered_df['country_code'] == selected_country]

filtered_df = filtered_df[
    (filtered_df['funding_total_usd'] >= funding_range[0]) &
    (filtered_df['funding_total_usd'] <= funding_range[1])
]

st.sidebar.markdown(f"📊 Results: **{len(filtered_df)}**")

# ======================
# 📊 KPIs
# ======================
col1, col2, col3 = st.columns(3)

total = filtered_df['funding_total_usd'].sum()
avg = filtered_df['funding_total_usd'].mean()
count = len(filtered_df)

col1.metric("💰 Total Funding", f"${total:,.0f}")
col2.metric("📊 Avg Funding", f"${avg:,.0f}")
col3.metric("🏢 Companies", count)

st.divider()

# ======================
# 📈 Charts Row 1
# ======================
colA, colB = st.columns(2)

# Top Countries
with colA:
    st.subheader("🌍 Top Countries")

    top_countries = (
        filtered_df['country_code']
        .value_counts()
        .head(10)
        .reset_index()
    )
    top_countries.columns = ['Country', 'Count']

    fig1 = px.bar(
        top_countries,
        x='Country',
        y='Count',
        color='Count',
        template='plotly_white'
    )
    st.plotly_chart(fig1, use_container_width=True)

# Categories Pie
with colB:
    st.subheader("🏭 Categories")

    top_cat = (
        filtered_df['category_list']
        .value_counts()
        .head(10)
        .reset_index()
    )
    top_cat.columns = ['Category', 'Count']

    fig2 = px.pie(
        top_cat,
        names='Category',
        values='Count',
        hole=0.5
    )
    st.plotly_chart(fig2, use_container_width=True)

# ======================
# 📈 Charts Row 2
# ======================
colC, colD = st.columns(2)

# Funding Distribution
with colC:
    st.subheader("📊 Funding Distribution")

    fig3 = px.histogram(
        filtered_df,
        x='funding_total_usd',
        nbins=40
    )
    st.plotly_chart(fig3, use_container_width=True)

# Top Companies
with colD:
    st.subheader("🏆 Top Companies")

    top_companies = filtered_df.nlargest(10, 'funding_total_usd')

    fig4 = px.bar(
        top_companies,
        x='funding_total_usd',
        y='name',
        orientation='h',
        color='funding_total_usd'
    )
    fig4.update_layout(yaxis={'categoryorder':'total ascending'})

    st.plotly_chart(fig4, use_container_width=True)

# ======================
# 🌍 Map (WOW Feature)
# ======================
st.subheader("🌍 Global Funding Map")

country_map = (
    filtered_df
    .groupby('country_code')['funding_total_usd']
    .sum()
    .reset_index()
)

fig_map = px.choropleth(
    country_map,
    locations='country_code',
    color='funding_total_usd',
    color_continuous_scale='Blues'
)

st.plotly_chart(fig_map, use_container_width=True)

# ======================
# 📋 Data Table
# ======================
st.divider()
st.subheader("📋 Data Preview")

cols = ['name', 'country_code', 'category_list', 'funding_total_usd']
cols = [c for c in cols if c in filtered_df.columns]

st.dataframe(filtered_df[cols].head(100), use_container_width=True)

# ======================
# 📥 Download Button
# ======================
csv = filtered_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Download Data",
    data=csv,
    file_name="filtered_data.csv",
    mime="text/csv"
)

# ======================
# 🤖 Insight
# ======================
if len(filtered_df) > 0:
    top_country = filtered_df['country_code'].mode()[0]
    st.info(f"📊 Most investments are concentrated in {top_country}")

# ======================
# Footer
# ======================
st.divider()
st.caption("🚀 VortexTech | Data Dashboard by You 😎")