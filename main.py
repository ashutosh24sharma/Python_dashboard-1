import streamlit as st
import pandas as pd
import os
import warnings

warnings.filterwarnings('ignore')

# Try importing Plotly safely
try:
    import plotly.express as px
    import plotly.figure_factory as ff
except Exception as e:
    st.error("⚠️ Required package 'plotly' is not installed or failed to import.")
    st.info("Install it using: `pip install plotly`")
    st.write(f"Import error: {e}")
    st.stop()

# ------------------- Streamlit Page Setup -------------------
st.set_page_config(page_title="Superstore Dashboard", page_icon=":bar_chart:", layout="wide")
st.title(":bar_chart: Sample SuperStore EDA")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

# ------------------- File Upload Section -------------------
fl = st.file_uploader(":file_folder: Upload a file", type=["csv", "txt", "xlsx", "xls"])

if fl is not None:
    filename = fl.name
    st.write(f"✅ Uploaded File: {filename}")
    # Read uploaded file properly
    if filename.endswith('.csv') or filename.endswith('.txt'):
        df = pd.read_csv(fl, encoding="ISO-8859-1")
    else:
        df = pd.read_excel(fl)
else:
    # Fallback to default file path
    default_path = r"C:\Users\ashu9\Desktop\sreamlit project\Sample Superstore.csv"
    if os.path.exists(default_path):
        df = pd.read_csv(default_path, encoding="ISO-8859-1")
    else:
        st.error("❌ Default dataset not found. Please upload a file.")
        st.stop()

# ------------------- Fix Date Parsing -------------------
# Handle mixed date formats safely
df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, errors='coerce')

# Drop rows where date couldn't be parsed
df = df.dropna(subset=["Order Date"])

# ------------------- Date Range Filter -------------------
col1, col2 = st.columns((2))
startDate = df["Order Date"].min()
endDate = df["Order Date"].max()

with col1:
    date1 = pd.to_datetime(st.date_input("Start Date", startDate))

with col2:
    date2 = pd.to_datetime(st.date_input("End Date", endDate))

df = df[(df["Order Date"] >= date1) & (df["Order Date"] <= date2)].copy()

# ------------------- Sidebar Filters -------------------
st.sidebar.header("🔍 Choose your filter:")

region = st.sidebar.multiselect("Pick your Region", df["Region"].unique())
state = st.sidebar.multiselect("Pick your State", df["State"].unique())
city = st.sidebar.multiselect("Pick your City", df["City"].unique())

# Filter logic
filtered_df = df.copy()
if region:
    filtered_df = filtered_df[filtered_df["Region"].isin(region)]
if state:
    filtered_df = filtered_df[filtered_df["State"].isin(state)]
if city:
    filtered_df = filtered_df[filtered_df["City"].isin(city)]

# ------------------- Category and Region Charts -------------------
col1, col2 = st.columns((2))

category_df = filtered_df.groupby("Category", as_index=False)["Sales"].sum()

with col1:
    st.subheader("📊 Category wise Sales")
    fig = px.bar(category_df, x="Category", y="Sales",
                 text=[f'${x:,.2f}' for x in category_df["Sales"]],
                 template="seaborn")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🌍 Region wise Sales")
    region_df = filtered_df.groupby("Region", as_index=False)["Sales"].sum()
    fig = px.pie(region_df, values="Sales", names="Region", hole=0.5)
    st.plotly_chart(fig, use_container_width=True)

# ------------------- Expanders for Viewing Data -------------------
cl1, cl2 = st.columns((2))
with cl1:
    with st.expander("📘 Category Data"):
        st.write(category_df.style.background_gradient(cmap="Blues"))
        st.download_button("Download Category Data", category_df.to_csv(index=False).encode('utf-8'),
                           "Category.csv", "text/csv")

with cl2:
    with st.expander("🧭 Region Data"):
        st.write(region_df.style.background_gradient(cmap="Oranges"))
        st.download_button("Download Region Data", region_df.to_csv(index=False).encode('utf-8'),
                           "Region.csv", "text/csv")

# ------------------- Time Series -------------------
filtered_df["month_year"] = filtered_df["Order Date"].dt.to_period("M")
st.subheader("📈 Time Series Analysis")

linechart = filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y-%b"))["Sales"].sum().reset_index()
fig2 = px.line(linechart, x="month_year", y="Sales", labels={"Sales": "Amount"}, template="gridon")
st.plotly_chart(fig2, use_container_width=True)

with st.expander("View Time Series Data"):
    st.write(linechart.T.style.background_gradient(cmap="Blues"))
    st.download_button("Download Time Series Data", linechart.to_csv(index=False).encode('utf-8'),
                       "TimeSeries.csv", "text/csv")

# ------------------- TreeMap -------------------
st.subheader("🌲 Hierarchical View of Sales")
fig3 = px.treemap(filtered_df, path=["Region", "Category", "Sub-Category"], values="Sales",
                  hover_data=["Sales"], color="Sub-Category")
st.plotly_chart(fig3, use_container_width=True)

# ------------------- Pie Charts -------------------
chart1, chart2 = st.columns((2))
with chart1:
    st.subheader('👥 Segment wise Sales')
    fig = px.pie(filtered_df, values="Sales", names="Segment", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader('📦 Category wise Sales')
    fig = px.pie(filtered_df, values="Sales", names="Category", template="gridon")
    st.plotly_chart(fig, use_container_width=True)

# ------------------- Table + Pivot -------------------
st.subheader("🗂️ Month-wise Sub-Category Sales Summary")
with st.expander("Summary Table"):
    df_sample = filtered_df.head(5)[["Region", "State", "City", "Category", "Sales", "Profit", "Quantity"]]
    fig = ff.create_table(df_sample, colorscale="Cividis")
    st.plotly_chart(fig, use_container_width=True)

    filtered_df["month"] = filtered_df["Order Date"].dt.month_name()
    sub_category_Year = pd.pivot_table(filtered_df, values="Sales", index=["Sub-Category"], columns="month")
    st.write(sub_category_Year.style.background_gradient(cmap="Blues"))

# ------------------- Scatter Plot -------------------
st.subheader("💹 Sales vs Profit Scatter Plot")
scatter_fig = px.scatter(filtered_df, x="Sales", y="Profit", size="Quantity",
                         title="Relationship between Sales and Profit")
st.plotly_chart(scatter_fig, use_container_width=True)

# ------------------- Download Original Dataset -------------------
st.download_button("⬇️ Download Original Data",
                   df.to_csv(index=False).encode('utf-8'),
                   "Data.csv", "text/csv")
