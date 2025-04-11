import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# === CONFIG ===
@st.cache_data
def load_data(default_path):
    try:
        return pd.read_csv(default_path)
    except Exception as e:
        st.error(f"Error loading default file: {e}")
        return pd.DataFrame()

# === Default CSV file ===
default_file_path = "/Users/bharatkumar/Downloads/icp_segments_final.csv"

# === Streamlit Page Setup ===
st.set_page_config(page_title="ICP Segment Explorer", layout="wide")
st.title("📊 SMB ICP Segment Visualizer")

# === Upload or Load ===
st.sidebar.markdown("### 📁 Load Data")
uploaded_file = st.sidebar.file_uploader("Upload a CSV to override the default", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ Loaded uploaded file.")
else:
    df = load_data(default_file_path)
    st.info(f"Using default file: `{default_file_path}`")

if df.empty:
    st.stop()

st.markdown(f"Loaded {len(df):,} ICP records.")

# === Rename Location Column if Needed ===
if "Aggregated Location" in df.columns and "location_clean" not in df.columns:
    df.rename(columns={"Aggregated Location": "location_clean"}, inplace=True)

# === Filters ===
st.sidebar.header("🔍 Filters")

unique_roles = sorted(set(
    role.strip() for roles in df["cleaned_roles"].dropna().astype(str) for role in roles.split(",")
)) if "cleaned_roles" in df.columns else []

unique_industries = sorted(set(
    ind.strip() for inds in df["gpt_industry"].dropna().astype(str) for ind in inds.split(",")
)) if "gpt_industry" in df.columns else []

unique_locations = sorted(df["location_clean"].dropna().astype(str).unique()) if "location_clean" in df.columns else []

selected_roles = st.sidebar.multiselect("Filter by Role", unique_roles)
selected_industries = st.sidebar.multiselect("Filter by GPT Industry", unique_industries)
selected_locations = st.sidebar.multiselect("Filter by Location", unique_locations)

# === Filtering Logic ===
filtered_df = df.copy()

if selected_roles and "cleaned_roles" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["cleaned_roles"].apply(
        lambda x: isinstance(x, str) and any(role in x for role in selected_roles)
    )]
if selected_industries:
    filtered_df = filtered_df[filtered_df["gpt_industry"].isin(selected_industries)]
if selected_locations:
    filtered_df = filtered_df[filtered_df["location_clean"].isin(selected_locations)]

# === Drop columns ===
columns_to_drop = ["industries_clean"]
for col in columns_to_drop:
    if col in filtered_df.columns:
        filtered_df.drop(columns=[col], inplace=True)

# === Format PC Link Column ===
if "PC URL" in filtered_df.columns:
    filtered_df["PC Link"] = filtered_df["PC URL"].apply(
        lambda x: x if pd.notna(x) and x.startswith("http") else ""
    )
    filtered_df.drop(columns=["PC URL"], inplace=True)

# === Sorting ===
st.sidebar.header("🔢 Sort")
sort_column = st.sidebar.selectbox("Sort by column", options=filtered_df.columns, index=list(filtered_df.columns).index("pool_size") if "pool_size" in filtered_df.columns else 0)
sort_ascending = st.sidebar.radio("Sort order", ["Ascending", "Descending"]) == "Ascending"

filtered_df = filtered_df.sort_values(by=sort_column, ascending=sort_ascending)

# === Display ===
st.subheader("📈 Filtered Data")
st.dataframe(filtered_df, use_container_width=True)

# === Summary Stats for Pool Size ===
if "pool_size" in filtered_df.columns:
    st.markdown("### 📊 Summary Statistics for Pool Size")
    st.write("**Mean Pool Size:**", int(filtered_df["pool_size"].mean()))
    st.write("**Median Pool Size:**", int(filtered_df["pool_size"].median()))
    mode_val = filtered_df["pool_size"].mode()
    if not mode_val.empty:
        st.write("**Mode Pool Size:**", int(mode_val.iloc[0]))
    st.bar_chart(filtered_df["pool_size"].value_counts().sort_index())

# === GPT Summary (optional) ===
if "gpt_industry" in filtered_df.columns:
    st.markdown("### 🧠 GPT-Inferred Industries Breakdown")
    st.dataframe(
        filtered_df["gpt_industry"]
        .value_counts()
        .rename_axis("GPT Industry")
        .reset_index(name="Count")
    )

# === Top Roles by Location Chart ===
if "primary_role" in df.columns and "location_clean" in df.columns:
    st.markdown("### 📊 Top Roles in Selected Locations")
    chart_data = (
        filtered_df.groupby(["location_clean", "primary_role"])
        .size()
        .reset_index(name="Count")
    )
    if not chart_data.empty:
        top_roles = chart_data.sort_values("Count", ascending=False).head(20)
        st.bar_chart(top_roles.set_index("primary_role")["Count"])

# === Download Button ===
st.markdown("### 📥 Download Filtered Data")
st.download_button("Download CSV", data=filtered_df.to_csv(index=False), file_name="filtered_icp_data.csv")