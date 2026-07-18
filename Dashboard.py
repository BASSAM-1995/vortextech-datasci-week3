import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# ======================
# ⚙️ Page Config
# ======================
st.set_page_config(
    page_title="VortexTech Investment Dashboard",
    page_icon="🚀",
    layout="wide"
)

# ======================
# 🌙 Dark Mode Toggle
# ======================
dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=False)

# ======================
# 🎨 Custom CSS (Dynamic)
# ======================
css_light = """
<style>
    .main { background-color: #f8f9fa; }
    .card { padding: 20px; border-radius: 10px; background-color: white; box-shadow: 0px 2px 6px rgba(0,0,0,0.1); }
    [data-testid="stMetric"] { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; padding: 10px; }
    [data-testid="stMetricLabel"] { color: white !important; }
    [data-testid="stMetricValue"] { color: white !important; font-size: 24px !important; }
    [data-testid="stMetricDelta"] { color: #ffd700 !important; }
</style>
"""

css_dark = """
<style>
    .main { background-color: #0e1117; color: #fafafa; }
    .card { padding: 20px; border-radius: 10px; background-color: #262730; box-shadow: 0px 2px 6px rgba(0,0,0,0.3); }
    h1, h2, h3, h4, h5, h6, p, label { color: #fafafa !important; }
    [data-testid="stMetric"] { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 10px; padding: 10px; border: 1px solid #667eea; }
    [data-testid="stMetricLabel"] { color: #a0a0a0 !important; }
    [data-testid="stMetricValue"] { color: #667eea !important; font-size: 24px !important; }
    [data-testid="stMetricDelta"] { color: #2ecc71 !important; }
    .stDataFrame { background-color: #262730 !important; }
    .stSelectbox label, .stSlider label, .stTextInput label { color: #fafafa !important; }
    /* Fix: Dark mode dropdown/popover styling */
    div[data-baseweb="popover"], ul[data-baseweb="menu"], li[data-baseweb="menu-item"] {
        background-color: #262730 !important;
        color: #fafafa !important;
    }
    div[data-baseweb="popover"] * { color: #fafafa !important; }
    li[data-baseweb="menu-item"]:hover { background-color: #3a3d4a !important; }
</style>
"""

st.markdown(css_dark if dark_mode else css_light, unsafe_allow_html=True)

# ======================
# 🔄 Refresh Data
# ======================
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ======================
# 📂 Helper Functions
# ======================
def safe_value_counts(series, top_n=10, name_col="Category", count_col="Count"):
    """Safe value_counts that works across all pandas versions."""
    counts = series.value_counts().head(top_n)
    return counts.rename_axis(name_col).reset_index(name=count_col)


def get_template():
    """Return plotly template based on dark mode."""
    return 'plotly_dark' if dark_mode else 'plotly_white'


def format_currency(value):
    """Format large numbers as B/M/K."""
    if pd.isna(value) or value == 0:
        return "$0"
    abs_val = abs(value)
    if abs_val >= 1e9:
        return f"${value/1e9:.2f}B"
    elif abs_val >= 1e6:
        return f"${value/1e6:.2f}M"
    elif abs_val >= 1e3:
        return f"${value/1e3:.1f}K"
    else:
        return f"${value:,.0f}"


def get_clean_categories(series, exclude_unknown_flag=False):
    """Split pipe-separated categories, clean whitespace/empties, optionally drop 'Unknown'."""
    tags = series.dropna().str.split('|').explode()
    tags = tags[tags.str.strip() != '']
    tags = tags.str.strip()
    if exclude_unknown_flag:
        tags = tags[tags != 'Unknown']
    return tags


# ======================
# 📂 Load Data
# ======================
@st.cache_data(ttl=3600)
def load_data():
    try:
        file_path = os.path.join(os.path.dirname(__file__), "cleaned_final.csv")

        if not os.path.exists(file_path):
            alt_path = "cleaned_final.csv"
            if os.path.exists(alt_path):
                file_path = alt_path
            else:
                st.error(f"❌ File not found: {file_path}")
                return pd.DataFrame()

        df = pd.read_csv(file_path)

        df['funding_total_usd'] = pd.to_numeric(df['funding_total_usd'], errors='coerce')
        df = df.dropna(subset=['funding_total_usd'])

        if 'category_list' in df.columns:
            df['category_list'] = df['category_list'].astype(str).str.strip().str.strip('|')

        if 'primary_category' not in df.columns:
            df['primary_category'] = df['category_list'].str.split('|').str[0]

        df['primary_category'] = df['primary_category'].replace('', np.nan).fillna('Unknown')

        if 'status' in df.columns:
            df['status'] = df['status'].fillna('Unknown')
        if 'country_code' in df.columns:
            df['country_code'] = df['country_code'].fillna('Unknown')
        if 'founded_year' in df.columns:
            df['founded_year'] = pd.to_numeric(df['founded_year'], errors='coerce')

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
    st.warning("⚠️ No data loaded. Please check the CSV file path.")
    st.stop()

# ======================
# 🔧 Sidebar Filters
# ======================
st.sidebar.header("🔧 Filters")

# 🔍 Live Search (literal match, not regex — avoids silent wrong results)
search_query = st.sidebar.text_input("🔍 Search Company", "", placeholder="Type company name...")
if search_query:
    st.sidebar.caption(f"🔎 Filtering names containing: '{search_query}'")

# Exclude zero funding option
exclude_zero = st.sidebar.checkbox("❌ Exclude companies with $0 funding", value=True)

# Exclude 'Unknown' categories option
unknown_count = (df['primary_category'] == 'Unknown').sum() if 'primary_category' in df.columns else 0

exclude_unknown = st.sidebar.checkbox(
    "❓ Exclude 'Unknown' categories",
    value=False,
    help=(f"{unknown_count:,} companies have 'Unknown' as their category. "
          "This only affects the category charts below (Pie & Tag Cloud) — "
          "it does not remove companies from KPIs, the table, or other charts.")
)

working_df = df.copy()
if exclude_zero:
    working_df = working_df[working_df['funding_total_usd'] > 0]

# Country Filter
countries = ['All'] + sorted(working_df['country_code'].dropna().unique().tolist())
selected_country = st.sidebar.selectbox("🌍 Country", countries)

# Status Filter (protected)
if 'status' in working_df.columns:
    statuses = ['All'] + sorted(working_df['status'].dropna().unique().tolist())
    selected_status = st.sidebar.selectbox("📋 Status", statuses)
else:
    selected_status = 'All'

# Funding Level Filter (protected)
if 'funding_level' in working_df.columns:
    funding_levels = ['All'] + sorted(working_df['funding_level'].dropna().unique().tolist())
    selected_funding_level = st.sidebar.selectbox("💎 Funding Level", funding_levels)
else:
    selected_funding_level = 'All'

# Founded Year Range
if 'founded_year' in working_df.columns:
    valid_years = working_df['founded_year'].dropna()
    if len(valid_years) > 0:
        min_year = int(valid_years.min())
        max_year = int(valid_years.max())
        year_range = st.sidebar.slider(
            "📅 Founded Year",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year)
        )
    else:
        year_range = None
else:
    year_range = None

# Funding Range Slider (with protection against equal min/max)
funding_vals = working_df['funding_total_usd'].dropna()

if len(funding_vals) > 0:
    min_val = float(funding_vals.min())
    max_val = float(funding_vals.max())

    if min_val == max_val:
        st.sidebar.info(f"💡 All funding values are equal: {format_currency(min_val)}")
        funding_range = (min_val, max_val)
    else:
        if max_val / min_val > 1000:
            st.sidebar.markdown("💡 *Using logarithmic funding filter due to wide range*")
            log_min = np.log10(max(min_val, 1))
            log_max = np.log10(max_val)
            log_range = st.sidebar.slider(
                "💰 Funding Range (log scale)",
                min_value=float(log_min),
                max_value=float(log_max),
                value=(float(log_min), float(log_max)),
                format="%.1f"
            )
            funding_range = (10**log_range[0], 10**log_range[1])
        else:
            funding_range = st.sidebar.slider(
                "💰 Funding Range",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                format="$%.0f"
            )
else:
    funding_range = (0, 0)

# Apply Filters
filtered_df = working_df.copy()

if search_query and 'name' in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df['name'].astype(str).str.contains(search_query, case=False, na=False, regex=False)
    ]

if selected_country != 'All':
    filtered_df = filtered_df[filtered_df['country_code'] == selected_country]

if selected_status != 'All' and 'status' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['status'] == selected_status]

if selected_funding_level != 'All' and 'funding_level' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['funding_level'] == selected_funding_level]

if year_range is not None and 'founded_year' in filtered_df.columns:
    filtered_df = filtered_df[
        (filtered_df['founded_year'] >= year_range[0]) &
        (filtered_df['founded_year'] <= year_range[1])
    ]

filtered_df = filtered_df[
    (filtered_df['funding_total_usd'] >= funding_range[0]) &
    (filtered_df['funding_total_usd'] <= funding_range[1])
]

st.sidebar.markdown(f"📊 **Results: {len(filtered_df):,}** companies")
st.sidebar.caption("💡 Filter options are independent (not cascading) for better UX")

# ======================
# 📊 KPIs
# ======================
if filtered_df.empty:
    st.warning("⚠️ No companies match the selected filters. Try adjusting your criteria.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)

total = filtered_df['funding_total_usd'].sum()
avg = filtered_df['funding_total_usd'].mean()
median = filtered_df['funding_total_usd'].median()
count = len(filtered_df)

with col1:
    st.metric("💰 Total Funding", format_currency(total))
with col2:
    st.metric("📊 Avg Funding", format_currency(avg))
with col3:
    st.metric("📈 Median Funding", format_currency(median))
with col4:
    st.metric("🏢 Companies", f"{count:,}")

st.divider()

# ======================
# 📈 Charts Row 1
# ======================
colA, colB = st.columns(2)

# Top Countries
with colA:
    st.subheader("🌍 Top Countries by Company Count")

    if 'country_code' in filtered_df.columns:
        top_countries = safe_value_counts(filtered_df['country_code'], top_n=10, name_col='Country', count_col='Count')

        fig1 = px.bar(
            top_countries,
            x='Country',
            y='Count',
            color='Count',
            color_continuous_scale='Blues',
            template=get_template()
        )
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Country data not available")

# Categories Pie
with colB:
    st.subheader("🏭 Top Categories")

    if 'category_list' in filtered_df.columns:
        all_cats = get_clean_categories(filtered_df['category_list'], exclude_unknown)
        top_cat = safe_value_counts(all_cats, top_n=10, name_col='Category', count_col='Count')

        fig2 = px.pie(
            top_cat,
            names='Category',
            values='Count',
            hole=0.5,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Category data not available")

# ======================
# 🏷️ Category Tag Cloud (Creative HTML Grid)
# ======================
st.subheader("🏷️ Category Tag Cloud")

if 'category_list' in filtered_df.columns:
    all_tags = get_clean_categories(filtered_df['category_list'], exclude_unknown)
    tag_counts = all_tags.value_counts().head(20)

    if len(tag_counts) > 0:
        max_count = tag_counts.max()
        min_count = tag_counts.min()

        if dark_mode:
            bg_colors = ['#1e3a5f', '#2c5282', '#3182ce', '#4299e1', '#63b3ed']
            text_color = '#ffffff'
            border_color = '#4a5568'
            container_bg = '#0e1117'
        else:
            bg_colors = ['#1a365d', '#2c5282', '#2b6cb0', '#3182ce', '#4299e1']
            text_color = '#ffffff'
            border_color = '#e2e8f0'
            container_bg = '#f8f9fa'

        tags_html = []
        for i, (tag, count) in enumerate(tag_counts.items()):
            if max_count != min_count:
                size = 14 + (count - min_count) / (max_count - min_count) * 18
            else:
                size = 20
            color_idx = i % len(bg_colors)
            bg = bg_colors[color_idx]

            tags_html.append(
                f'<span style="display:inline-block;background:{bg};color:{text_color};'
                f'font-size:{size:.0f}px;font-weight:600;padding:8px 16px;margin:6px;'
                f'border-radius:20px;border:1px solid {border_color};'
                f'box-shadow:0 2px 8px rgba(0,0,0,0.15);white-space:nowrap;'
                f'transition:all 0.2s ease;cursor:default;" '
                f"onmouseover=\"this.style.transform=\'scale(1.08)\';this.style.boxShadow=\'0 4px 16px rgba(0,0,0,0.25)\'\" "
                f"onmouseout=\"this.style.transform=\'scale(1)\';this.style.boxShadow=\'0 2px 8px rgba(0,0,0,0.15)\'\">"
                f'{tag} <small style="opacity:0.7;font-size:0.6em">({count:,})</small></span>'
            )

        cloud_html = (
            f'<div style="text-align:center;padding:20px;line-height:1.6;'
            f'background:{container_bg};border-radius:12px;border:1px solid {border_color}">'
            f'{"".join(tags_html)}</div>'
        )

        st.markdown(cloud_html, unsafe_allow_html=True)

        # Bar chart below
        st.markdown("<br>", unsafe_allow_html=True)
        tag_bar = tag_counts.head(10).rename_axis('Category').reset_index(name='Count')
        fig_tags_bar = px.bar(
            tag_bar, x='Count', y='Category', orientation='h',
            color='Count', color_continuous_scale='Blues',
            template=get_template(), height=300
        )
        fig_tags_bar.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            xaxis_title="Number of Companies", yaxis_title="",
            showlegend=False, margin=dict(l=20, r=20, t=10, b=10)
        )
        st.plotly_chart(fig_tags_bar, use_container_width=True)
    else:
        st.info("No category tags to display")
else:
    st.info("Category data not available")

st.divider()

# ======================
# 📈 Charts Row 2
# ======================
colC, colD = st.columns(2)

with colC:
    st.subheader("📊 Funding Distribution")
    funding_for_hist = filtered_df[filtered_df['funding_total_usd'] > 0]['funding_total_usd']

    if len(funding_for_hist) > 0:
        log_vals = np.log10(funding_for_hist.replace(0, 1))
        fig3 = px.histogram(
            x=log_vals,
            nbins=30,
            template=get_template(),
            color_discrete_sequence=['#667eea']
        )
        tick_vals = list(range(int(np.floor(log_vals.min())), int(np.ceil(log_vals.max())) + 1))
        fig3.update_xaxes(
            tickvals=tick_vals,
            ticktext=[f"${10**v:,.0f}" for v in tick_vals],
            title_text="Funding (USD)"
        )
        fig3.update_layout(
            yaxis_title="Number of Companies",
            height=400
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No funding data to display")

with colD:
    st.subheader("🏆 Top Funded Companies")
    if 'name' in filtered_df.columns:
        top_companies = filtered_df.nlargest(10, 'funding_total_usd')[['name', 'funding_total_usd', 'country_code']]

        fig4 = px.bar(
            top_companies,
            x='funding_total_usd',
            y='name',
            orientation='h',
            color='funding_total_usd',
            color_continuous_scale='Blues',
            template=get_template()
        )
        fig4.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            xaxis_title="Funding (USD)",
            yaxis_title="",
            height=400
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Company name data not available")

# ======================
# 📈 Charts Row 3
# ======================
colE, colF = st.columns(2)

with colE:
    st.subheader("📋 Company Status Breakdown")
    if 'status' in filtered_df.columns:
        status_counts = safe_value_counts(filtered_df['status'], top_n=10, name_col='Status', count_col='Count')
        colors = {'operating': '#2ecc71', 'acquired': '#3498db', 'closed': '#e74c3c', 'Unknown': '#95a5a6'}
        fig5 = px.bar(
            status_counts,
            x='Status',
            y='Count',
            color='Status',
            color_discrete_map=colors,
            template=get_template()
        )
        fig5.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig5, use_container_width=True)

with colF:
    st.subheader("💎 Funding Level Distribution")
    if 'funding_level' in filtered_df.columns:
        level_counts = safe_value_counts(filtered_df['funding_level'], top_n=10, name_col='Level', count_col='Count')
        level_order = {'Low': 0, 'Medium': 1, 'High': 2}
        level_counts['_sort'] = level_counts['Level'].map(level_order)
        level_counts = level_counts.sort_values('_sort', na_position='last').drop('_sort', axis=1)

        level_colors = {'Low': '#e74c3c', 'Medium': '#f39c12', 'High': '#2ecc71'}
        fig6 = px.bar(
            level_counts,
            x='Level',
            y='Count',
            color='Level',
            color_discrete_map=level_colors,
            template=get_template()
        )
        fig6.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig6, use_container_width=True)

# ======================
# 📅 Temporal Analysis
# ======================
st.subheader("📅 Funding Trends Over Time")

if 'founded_year' in filtered_df.columns:
    year_df = filtered_df[filtered_df['founded_year'].notna()].copy()
    year_df['founded_year'] = year_df['founded_year'].astype(int)

    current_year = pd.Timestamp.now().year
    year_df = year_df[(year_df['founded_year'] >= 1970) & (year_df['founded_year'] <= current_year)]

    excluded_count = len(filtered_df) - len(year_df)
    if excluded_count > 0:
        st.caption(f"📊 Excludes {excluded_count:,} companies with invalid/outlier founding years (before 1970 or future dates)")

    if len(year_df) > 0:
        colTime1, colTime2 = st.columns(2)

        with colTime1:
            st.markdown("**💰 Total Funding by Year**")
            yearly_funding = year_df.groupby('founded_year')['funding_total_usd'].sum().reset_index()
            fig_time = px.area(
                yearly_funding,
                x='founded_year',
                y='funding_total_usd',
                template=get_template(),
                color_discrete_sequence=['#667eea']
            )
            fig_time.update_layout(height=350, xaxis_title="Year Founded", yaxis_title="Total Funding (USD)")
            st.plotly_chart(fig_time, use_container_width=True)

        with colTime2:
            st.markdown("**🏢 Companies Founded by Year**")
            yearly_count = year_df.groupby('founded_year').size().reset_index(name='count')
            fig_count = px.bar(
                yearly_count,
                x='founded_year',
                y='count',
                template=get_template(),
                color_discrete_sequence=['#764ba2']
            )
            fig_count.update_layout(height=350, xaxis_title="Year Founded", yaxis_title="Number of Companies")
            st.plotly_chart(fig_count, use_container_width=True)
    else:
        st.info("📊 No valid founding year data available for temporal analysis")
else:
    st.info("📅 Founding year data not available")

st.divider()

# ======================
# 🌍 Map
# ======================
st.subheader("🌍 Global Funding Heatmap")

if 'country_code' in filtered_df.columns:
    country_map = (
        filtered_df
        .groupby('country_code')['funding_total_usd']
        .agg(['sum', 'count'])
        .reset_index()
    )
    country_map.columns = ['country_code', 'funding_total_usd', 'company_count']

    fig_map = px.choropleth(
        country_map,
        locations='country_code',
        color='funding_total_usd',
        hover_name='country_code',
        hover_data={'company_count': True, 'funding_total_usd': ':,.0f'},
        color_continuous_scale='Blues',
        locationmode='ISO-3',
        template=get_template()
    )
    fig_map.update_layout(height=500)
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("Country data not available for map")

# ======================
# 📋 Data Table
# ======================
st.divider()
st.subheader("📋 Data Preview")

display_cols = ['name', 'country_code', 'primary_category', 'funding_total_usd', 'status', 'founded_year', 'funding_level']
display_cols = [c for c in display_cols if c in filtered_df.columns]

preview_df = filtered_df[display_cols].head(100).copy()

if 'category_list' in filtered_df.columns:
    preview_df['all_categories'] = filtered_df['category_list'].head(100).str.replace('|', ', ')
    insert_at = display_cols.index('primary_category') + 1 if 'primary_category' in display_cols else len(display_cols)
    display_cols.insert(insert_at, 'all_categories')
    preview_df = preview_df[display_cols]

col_config = {}
if 'funding_total_usd' in preview_df.columns:
    col_config["funding_total_usd"] = st.column_config.NumberColumn(
        "💰 Funding (USD)", format="$%,.0f", help="Total funding raised in US Dollars"
    )
if 'founded_year' in preview_df.columns:
    col_config["founded_year"] = st.column_config.NumberColumn(
        "📅 Year", format="%.0f", help="Year the company was founded"
    )
if 'name' in preview_df.columns:
    col_config["name"] = st.column_config.TextColumn("🏢 Company Name")
if 'country_code' in preview_df.columns:
    col_config["country_code"] = st.column_config.TextColumn("🌍 Country")
if 'primary_category' in preview_df.columns:
    col_config["primary_category"] = st.column_config.TextColumn("🏷️ Primary Category")
if 'all_categories' in preview_df.columns:
    col_config["all_categories"] = st.column_config.TextColumn("🏭 All Categories", width="large")
if 'status' in preview_df.columns:
    col_config["status"] = st.column_config.TextColumn("📋 Status")
if 'funding_level' in preview_df.columns:
    col_config["funding_level"] = st.column_config.TextColumn("💎 Level")

st.dataframe(
    preview_df,
    column_config=col_config,
    use_container_width=True,
    hide_index=True
)

# ======================
# 📥 Download Button
# ======================
csv = filtered_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Download Filtered Data (CSV)",
    data=csv,
    file_name="filtered_investment_data.csv",
    mime="text/csv"
)

# ======================
# 🤖 Smart Insights
# ======================
st.divider()
st.subheader("🤖 Smart Insights")

insights = []

if len(filtered_df) > 0:
    if 'country_code' in filtered_df.columns:
        top_country = filtered_df['country_code'].mode()[0]
        country_pct = (filtered_df['country_code'] == top_country).mean() * 100
        insights.append(f"🌍 **{top_country}** leads with **{country_pct:.1f}%** of filtered companies")

    if 'primary_category' in filtered_df.columns:
        top_cat = filtered_df['primary_category'].mode()[0]
        insights.append(f"🏭 **{top_cat}** is the most common primary category")

    high_fund = (filtered_df['funding_total_usd'] > filtered_df['funding_total_usd'].quantile(0.9)).sum()
    insights.append(f"💰 **{high_fund}** companies ({high_fund/len(filtered_df)*100:.1f}%) are in the top 10% of funding")

    if 'status' in filtered_df.columns:
        operating_pct = (filtered_df['status'] == 'operating').mean() * 100
        insights.append(f"📈 **{operating_pct:.1f}%** of companies are still operating")

    for insight in insights:
        st.info(insight)

# ======================
# Footer
# ======================
st.divider()
st.caption("🚀 VortexTech | Data Dashboard | Built with ❤️ using Streamlit + Plotly")
