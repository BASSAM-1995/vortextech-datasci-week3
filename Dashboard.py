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
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# 🎨 Custom CSS
# ======================
st.markdown("""
<style>
    /* Overall background */
    .main {
        background-color: #f4f6f9;
    }

    /* Headings */
    h1 {
        font-weight: 800 !important;
        color: #1a1f36 !important;
        padding-bottom: 0px !important;
    }
    h2, h3 {
        color: #1a1f36 !important;
        font-weight: 700 !important;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fc 100%);
        border: 1px solid #eef0f5;
        padding: 18px 20px;
        border-radius: 14px;
        box-shadow: 0px 4px 14px rgba(20, 20, 43, 0.06);
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #6b7280;
    }
    div[data-testid="stMetricValue"] {
        color: #1a1f36;
        font-weight: 800;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1a1f36;
    }
    section[data-testid="stSidebar"] * {
        color: #f4f6f9 !important;
    }

    /* Chart containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 14px;
        box-shadow: 0px 4px 14px rgba(20, 20, 43, 0.05);
        padding: 6px;
    }

    /* Divider */
    hr {
        border-color: #e5e7eb !important;
    }

    /* Info / warning boxes */
    div[data-testid="stAlert"] {
        border-radius: 10px;
    }

    /* Dataframe */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_white"
COLOR_SCALE = "Blues"


# ======================
# 📂 Load Data
# ======================
@st.cache_data(ttl=3600)
def load_data():
    try:
        file_path = os.path.join(os.path.dirname(__file__), "cleaned_final.csv")

        if not os.path.exists(file_path):
            st.error(f"❌ File not found: {file_path}")
            return pd.DataFrame()

        df = pd.read_csv(file_path)

        # تنظيف الأعمدة الرقمية الأساسية
        df['funding_total_usd'] = pd.to_numeric(df['funding_total_usd'], errors='coerce')
        df = df.dropna(subset=['funding_total_usd'])

        if 'funding_log' not in df.columns:
            # نبنيها احتياطيًا لو لم تكن موجودة في الملف
            import numpy as np
            df['funding_log'] = np.log10(df['funding_total_usd'].clip(lower=1))

        return df

    except Exception as e:
        st.error(f"🔥 Error loading data: {e}")
        return pd.DataFrame()


def top_value_counts(series: pd.Series, label: str, top_n: int = 10) -> pd.DataFrame:
    """Safe helper: returns a 2-col dataframe [label, 'Count'] regardless of pandas version."""
    counts = series.dropna().value_counts().head(top_n)
    return counts.rename_axis(label).reset_index(name='Count')


df = load_data()

# ======================
# 🏠 Title
# ======================
st.title("🚀 VortexTech Investment Dashboard")
st.caption("لوحة تحليل بيانات الاستثمار في الشركات الناشئة")

if df.empty:
    st.stop()

# ======================
# 🔧 Sidebar Filters
# ======================
st.sidebar.header("🔧 الفلاتر")

# Country Filter
countries = ['الكل'] + sorted(df['country_code'].dropna().unique())
selected_country = st.sidebar.selectbox("🌍 الدولة", countries)

# Status Filter
if 'status' in df.columns:
    statuses = ['الكل'] + sorted(df['status'].dropna().unique())
    selected_status = st.sidebar.selectbox("🏷️ حالة الشركة", statuses)
else:
    selected_status = 'الكل'

# Funding Level Filter (quick categorical filter)
if 'funding_level' in df.columns:
    levels = ['الكل'] + sorted(df['funding_level'].dropna().unique())
    selected_level = st.sidebar.selectbox("💵 مستوى التمويل", levels)
else:
    selected_level = 'الكل'

st.sidebar.divider()

# Exclude zero-funding toggle (يعالج تشوه التوزيع)
exclude_zero = st.sidebar.checkbox("استبعاد الشركات بتمويل = 0", value=True)

# Funding Range — على مقياس لوغاريتمي لأن التوزيع شديد التفاوت
# (من 0 إلى ~30 مليار، بينما الوسيط ~1 مليون)
base_df = df[df['funding_total_usd'] > 0] if exclude_zero else df.copy()

min_val = float(base_df['funding_total_usd'].min())
max_val = float(base_df['funding_total_usd'].max())

if min_val >= max_val:
    st.sidebar.info(f"كل القيم متساوية تقريبًا: ${min_val:,.0f}")
    funding_range = (min_val, max_val)
else:
    use_log_slider = st.sidebar.checkbox("استخدام مقياس لوغاريتمي للتمويل", value=True)
    if use_log_slider:
        import numpy as np
        log_min, log_max = float(np.log10(max(min_val, 1))), float(np.log10(max_val))
        log_range = st.sidebar.slider(
            "💰 نطاق التمويل (لوغاريتمي)",
            min_value=log_min, max_value=log_max,
            value=(log_min, log_max)
        )
        funding_range = (10 ** log_range[0], 10 ** log_range[1])
        st.sidebar.caption(f"≈ ${funding_range[0]:,.0f} → ${funding_range[1]:,.0f}")
    else:
        funding_range = st.sidebar.slider(
            "💰 نطاق التمويل",
            min_value=min_val, max_value=max_val,
            value=(min_val, max_val), format="$%.0f"
        )

# ======================
# Apply Filters
# ======================
filtered_df = df.copy()

if selected_country != 'الكل':
    filtered_df = filtered_df[filtered_df['country_code'] == selected_country]

if selected_status != 'الكل' and 'status' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['status'] == selected_status]

if selected_level != 'الكل' and 'funding_level' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['funding_level'] == selected_level]

if exclude_zero:
    filtered_df = filtered_df[filtered_df['funding_total_usd'] > 0]

filtered_df = filtered_df[
    (filtered_df['funding_total_usd'] >= funding_range[0]) &
    (filtered_df['funding_total_usd'] <= funding_range[1])
]

st.sidebar.divider()
st.sidebar.markdown(f"📊 عدد النتائج: **{len(filtered_df):,}**")

if filtered_df.empty:
    st.warning("⚠️ لا توجد نتائج مطابقة للفلاتر المحددة. جرّب توسيع النطاق.")
    st.stop()

# ======================
# 📊 KPIs
# ======================
col1, col2, col3, col4 = st.columns(4)

total = filtered_df['funding_total_usd'].sum()
avg = filtered_df['funding_total_usd'].mean()
median = filtered_df['funding_total_usd'].median()
count = len(filtered_df)

col1.metric("💰 إجمالي التمويل", f"${total:,.0f}")
col2.metric("📊 متوسط التمويل", f"${avg:,.0f}")
col3.metric("🎯 الوسيط", f"${median:,.0f}")
col4.metric("🏢 عدد الشركات", f"{count:,}")

st.divider()

# ======================
# 📈 Charts Row 1
# ======================
colA, colB = st.columns(2)

# Top Countries
with colA:
    st.subheader("🌍 أكثر الدول نشاطًا")
    top_countries = top_value_counts(filtered_df['country_code'], 'Country')

    fig1 = px.bar(
        top_countries, x='Country', y='Count',
        color='Count', color_continuous_scale=COLOR_SCALE,
        template=PLOTLY_TEMPLATE
    )
    fig1.update_layout(showlegend=False, coloraxis_showscale=False, margin=dict(t=10))
    st.plotly_chart(fig1, use_container_width=True)

# Categories Pie — نستخدم primary_category النظيف بدل category_list متعدد القيم
with colB:
    st.subheader("🏭 أكثر التصنيفات")
    category_col = 'primary_category' if 'primary_category' in filtered_df.columns else 'category_list'
    top_cat = top_value_counts(filtered_df[category_col], 'Category')

    fig2 = px.pie(
        top_cat, names='Category', values='Count',
        hole=0.5, template=PLOTLY_TEMPLATE,
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    fig2.update_layout(margin=dict(t=10))
    st.plotly_chart(fig2, use_container_width=True)

# ======================
# 📈 Charts Row 2
# ======================
colC, colD = st.columns(2)

# Funding Distribution — على مقياس لوغاريتمي بسبب التفاوت الشديد في القيم
with colC:
    st.subheader("📊 توزيع التمويل (مقياس لوغاريتمي)")

    fig3 = px.histogram(
        filtered_df, x='funding_log', nbins=40,
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=['#3b6fd4']
    )
    fig3.update_layout(
        xaxis_title="log10(التمويل بالدولار)",
        yaxis_title="عدد الشركات",
        margin=dict(t=10)
    )
    st.plotly_chart(fig3, use_container_width=True)

# Top Companies
with colD:
    st.subheader("🏆 أعلى الشركات تمويلًا")

    if 'name' in filtered_df.columns:
        top_companies = filtered_df.nlargest(10, 'funding_total_usd')
        fig4 = px.bar(
            top_companies, x='funding_total_usd', y='name',
            orientation='h', color='funding_total_usd',
            color_continuous_scale=COLOR_SCALE, template=PLOTLY_TEMPLATE
        )
        fig4.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            xaxis_title="التمويل ($)", yaxis_title="",
            coloraxis_showscale=False, margin=dict(t=10)
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("عمود أسماء الشركات غير موجود في البيانات.")

# ======================
# 🌍 Map
# ======================
st.subheader("🌍 خريطة التمويل العالمية")

country_map = (
    filtered_df
    .groupby('country_code')['funding_total_usd']
    .sum()
    .reset_index()
)

fig_map = px.choropleth(
    country_map,
    locations='country_code',
    locationmode='ISO-3',
    color='funding_total_usd',
    color_continuous_scale=COLOR_SCALE,
    template=PLOTLY_TEMPLATE
)
fig_map.update_layout(margin=dict(t=10, b=10))
st.plotly_chart(fig_map, use_container_width=True)

# ======================
# 📋 Data Table
# ======================
st.divider()
st.subheader("📋 معاينة البيانات")

cols = ['name', 'country_code', 'primary_category', 'funding_total_usd', 'status', 'funding_level']
cols = [c for c in cols if c in filtered_df.columns]

st.dataframe(
    filtered_df[cols].sort_values('funding_total_usd', ascending=False).head(100),
    use_container_width=True, hide_index=True
)

# ======================
# 📥 Download Button
# ======================
csv = filtered_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 تحميل البيانات المفلترة",
    data=csv,
    file_name="filtered_data.csv",
    mime="text/csv"
)

# ======================
# 🤖 Insight
# ======================
if len(filtered_df) > 0:
    top_country = filtered_df['country_code'].mode()[0]
    top_country_share = (filtered_df['country_code'] == top_country).mean() * 100
    st.info(f"📊 تتركز أغلب الاستثمارات في **{top_country}** بنسبة **{top_country_share:.1f}%** من الشركات المعروضة.")

# ======================
# Footer
# ======================
st.divider()
st.caption("🚀 VortexTech | Data Dashboard")
