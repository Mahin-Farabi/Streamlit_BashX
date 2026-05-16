import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import io

st.set_page_config(
    page_title="Business Data Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "df"         not in st.session_state: st.session_state["df"]         = None
if "cleaned_df" not in st.session_state: st.session_state["cleaned_df"] = None
if "filename"   not in st.session_state: st.session_state["filename"]   = None
if "history"    not in st.session_state: st.session_state["history"]    = []


# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_df():
    """Return cleaned_df if available, else raw df."""
    c = st.session_state["cleaned_df"]
    r = st.session_state["df"]
    if c is not None:
        return c
    return r


def load_file(uploaded_file):
    try:
        if uploaded_file.name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        else:
            return pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return None


def clean_dataframe(df, remove_dup, clean_text, fill_missing, drop_bad_cols):
    cleaned = df.copy()
    if remove_dup:
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates()
        st.session_state["history"].append(f"Removed {before - len(cleaned)} duplicate rows")
    if clean_text:
        for col in cleaned.select_dtypes(include="object").columns:
            cleaned[col] = cleaned[col].astype(str).str.strip()
        st.session_state["history"].append("Stripped whitespace from text columns")
    if fill_missing:
        num_cols = cleaned.select_dtypes(include="number").columns
        cleaned[num_cols] = cleaned[num_cols].fillna(cleaned[num_cols].mean())
        obj_cols = cleaned.select_dtypes(include="object").columns
        cleaned[obj_cols] = cleaned[obj_cols].fillna("Unknown")
        st.session_state["history"].append("Filled missing values with mean/Unknown")
    if drop_bad_cols:
        before = len(cleaned.columns)
        cleaned = cleaned.dropna(axis=1, thresh=int(len(cleaned) * 0.5))
        st.session_state["history"].append(f"Dropped {before - len(cleaned.columns)} columns with >50% missing")
    return cleaned


def to_excel_bytes(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Data", index=False)
        wb = writer.book
        ws = writer.sheets["Data"]
        header_fmt = wb.add_format({"bold": True, "bg_color": "#1F4E79", "color": "#FFFFFF", "border": 1})
        for col_num, col_name in enumerate(df.columns):
            ws.write(0, col_num, col_name, header_fmt)
            ws.set_column(col_num, col_num, max(len(str(col_name)) + 5, 15))
    return buffer.getvalue()


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Data Assistant")
    st.divider()

    nav = st.radio("Navigate", [
        "🏠 Home",
        "📁 Upload & Clean",
        "🔍 Explore",
        "📈 Visualise",
        "📋 Report",
        "🕓 History"
    ])

    st.divider()

    if st.session_state["filename"]:
        st.success(f"✅ Loaded: {st.session_state['filename']}")
        if st.button("🗑️ Clear Data", use_container_width=True):
            st.session_state["df"]         = None
            st.session_state["cleaned_df"] = None
            st.session_state["filename"]   = None
            st.rerun()
    else:
        st.info("No file loaded yet")


# ═════════════════════════════════════════════════════════════════════════════
# HOME
# ═════════════════════════════════════════════════════════════════════════════
if nav == "🏠 Home":
    st.title("📊 Business Data Assistant")
    st.markdown("#### Turn your messy data into clean insights — in seconds.")
    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Supported Formats", "CSV · Excel")
    col2.metric("Chart Types",       "6+")
    col3.metric("Export Options",    "CSV · Excel")
    col4.metric("Steps",             "4")

    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### 📁 1. Upload")
        st.markdown("Upload any CSV or Excel file.")
    with col2:
        st.markdown("### 🧹 2. Clean")
        st.markdown("Remove duplicates, fix missing values.")
    with col3:
        st.markdown("### 🔍 3. Explore")
        st.markdown("See structure, statistics, missing data.")
    with col4:
        st.markdown("### 📈 4. Visualise")
        st.markdown("Build interactive charts and reports.")

    st.divider()
    st.info("👈 Start by clicking **Upload & Clean** in the sidebar!")


# ═════════════════════════════════════════════════════════════════════════════
# UPLOAD & CLEAN
# ═════════════════════════════════════════════════════════════════════════════
elif nav == "📁 Upload & Clean":
    st.title("📁 Upload & Clean")
    st.divider()

    uploaded = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx", "xls"])

    if uploaded:
        df = load_file(uploaded)
        if df is not None:
            st.session_state["df"]       = df
            st.session_state["filename"] = uploaded.name
            st.session_state["history"].append(f"Loaded file: {uploaded.name} ({len(df)} rows)")

    if st.session_state["df"] is not None:
        df = st.session_state["df"]

        st.subheader("📄 Raw Data Preview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows",    len(df))
        col2.metric("Columns", len(df.columns))
        col3.metric("Missing", int(df.isnull().sum().sum()))
        st.dataframe(df.head(10), use_container_width=True)

        st.divider()
        st.subheader("🧹 Cleaning Options")

        col1, col2 = st.columns(2)
        with col1:
            remove_dup    = st.checkbox("✅ Remove Duplicate Rows",          value=True)
            clean_text    = st.checkbox("✅ Strip Whitespace from Text",      value=True)
        with col2:
            fill_missing  = st.checkbox("✅ Fill Missing Values",             value=True)
            drop_bad_cols = st.checkbox("⚠️ Drop Columns with >50% Missing",  value=False)

        st.divider()

        if st.button("🧹 Clean My Data", use_container_width=True, type="primary"):
            with st.spinner("Cleaning..."):
                cleaned = clean_dataframe(df, remove_dup, clean_text, fill_missing, drop_bad_cols)
                st.session_state["cleaned_df"] = cleaned
            st.success(f"✅ Done! {len(df) - len(cleaned)} rows removed, "
                       f"{int(df.isnull().sum().sum()) - int(cleaned.isnull().sum().sum())} missing values fixed.")

        if st.session_state["cleaned_df"] is not None:
            cleaned = st.session_state["cleaned_df"]
            st.subheader("✨ Cleaned Data Preview")
            st.dataframe(cleaned.head(10), use_container_width=True)
            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                csv = cleaned.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download Cleaned CSV",   data=csv,
                                   file_name="cleaned_data.csv", mime="text/csv",
                                   use_container_width=True)
            with col2:
                st.download_button("⬇️ Download Cleaned Excel", data=to_excel_bytes(cleaned),
                                   file_name="cleaned_data.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
    else:
        st.info("👆 Upload a file to get started!")


# ═════════════════════════════════════════════════════════════════════════════
# EXPLORE
# ═════════════════════════════════════════════════════════════════════════════
elif nav == "🔍 Explore":
    st.title("🔍 Data Explorer")
    st.divider()

    df = get_df()   # ← fixed: uses helper instead of `or`

    if df is not None:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Rows",     len(df))
        col2.metric("Total Columns",  len(df.columns))
        col3.metric("Missing Values", int(df.isnull().sum().sum()))
        col4.metric("Duplicate Rows", int(df.duplicated().sum()))

        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs(["👀 Preview", "📊 Statistics", "❓ Missing Values", "🔠 Column Info"])

        with tab1:
            rows = st.slider("Rows to preview", 5, min(100, len(df)), 10)
            st.dataframe(df.head(rows), use_container_width=True)

        with tab2:
            st.subheader("Numeric Column Statistics")
            st.dataframe(df.describe().round(2), use_container_width=True)

        with tab3:
            missing = df.isnull().sum().reset_index()
            missing.columns = ["Column", "Missing Count"]
            missing["Missing %"] = (missing["Missing Count"] / len(df) * 100).round(2)
            missing = missing[missing["Missing Count"] > 0].sort_values("Missing %", ascending=False)
            if len(missing) > 0:
                st.dataframe(missing, use_container_width=True, hide_index=True)
                fig = px.bar(missing, x="Column", y="Missing %", title="Missing Values by Column")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("✅ No missing values found!")

        with tab4:
            col_info = pd.DataFrame({
                "Column": df.columns,
                "Type":   df.dtypes.values,
                "Unique": [df[c].nunique() for c in df.columns],
                "Sample": [str(df[c].iloc[0]) if len(df) > 0 else "N/A" for c in df.columns],
            })
            st.dataframe(col_info, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No data loaded. Go to Upload & Clean first!")


# ═════════════════════════════════════════════════════════════════════════════
# VISUALISE
# ═════════════════════════════════════════════════════════════════════════════
elif nav == "📈 Visualise":
    st.title("📈 Interactive Visualizations")
    st.divider()

    df = get_df()   # ← fixed

    if df is not None:
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(include="object").columns.tolist()
        all_cols = df.columns.tolist()

        chart_type = st.selectbox("Select Chart Type", [
            "📊 Bar Chart", "📈 Line Chart", "🔵 Scatter Plot",
            "🥧 Pie Chart", "📦 Box Plot",   "🔥 Correlation Heatmap",
        ])
        st.divider()

        if chart_type == "📊 Bar Chart":
            if cat_cols and num_cols:
                col1, col2 = st.columns(2)
                with col1: x = st.selectbox("X Axis (Category)", cat_cols)
                with col2: y = st.selectbox("Y Axis (Numeric)",  num_cols)
                agg     = st.selectbox("Aggregation", ["Sum", "Mean", "Count", "Max", "Min"])
                agg_map = {"Sum":"sum","Mean":"mean","Count":"count","Max":"max","Min":"min"}
                chart_df = df.groupby(x)[y].agg(agg_map[agg]).reset_index()
                chart_df.columns = [x, y]
                fig = px.bar(chart_df, x=x, y=y, title=f"{agg} of {y} by {x}",
                             color=y, color_continuous_scale="Blues")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Need at least one numeric and one text column.")

        elif chart_type == "📈 Line Chart":
            if num_cols:
                col1, col2 = st.columns(2)
                with col1: x = st.selectbox("X Axis", all_cols)
                with col2: y = st.multiselect("Y Axis", num_cols, default=num_cols[:1])
                if y:
                    fig = px.line(df, x=x, y=y, title=f"Line Chart: {', '.join(y)} over {x}")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Need at least one numeric column.")

        elif chart_type == "🔵 Scatter Plot":
            if len(num_cols) >= 2:
                col1, col2, col3 = st.columns(3)
                with col1: x     = st.selectbox("X Axis", num_cols)
                with col2: y     = st.selectbox("Y Axis", num_cols, index=1)
                with col3: color = st.selectbox("Color by", ["None"] + cat_cols)
                fig = px.scatter(df, x=x, y=y,
                                 color=None if color == "None" else color,
                                 title=f"{y} vs {x}", trendline="ols")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Need at least 2 numeric columns.")

        elif chart_type == "🥧 Pie Chart":
            if cat_cols and num_cols:
                col1, col2 = st.columns(2)
                with col1: names  = st.selectbox("Category Column", cat_cols)
                with col2: values = st.selectbox("Value Column",    num_cols)
                top_n  = st.slider("Show top N categories", 3, 20, 8)
                pie_df = df.groupby(names)[values].sum().nlargest(top_n).reset_index()
                fig    = px.pie(pie_df, names=names, values=values,
                                title=f"{values} breakdown by {names}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Need at least one numeric and one text column.")

        elif chart_type == "📦 Box Plot":
            if num_cols:
                col1, col2 = st.columns(2)
                with col1: y     = st.selectbox("Numeric Column",    num_cols)
                with col2: group = st.selectbox("Group by (optional)", ["None"] + cat_cols)
                fig = px.box(df, y=y,
                             x=None if group == "None" else group,
                             title=f"Distribution of {y}",
                             color=None if group == "None" else group)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Need at least one numeric column.")

        elif chart_type == "🔥 Correlation Heatmap":
            if len(num_cols) >= 2:
                corr = df[num_cols].corr().round(2)
                fig  = px.imshow(corr, text_auto=True,
                                 color_continuous_scale="RdBu",
                                 title="Correlation Heatmap", aspect="auto")
                st.plotly_chart(fig, use_container_width=True)
                st.subheader("Interpretation")
                st.markdown("""
- **1.0** = Perfect positive correlation
- **-1.0** = Perfect negative correlation
- **0.0** = No correlation
- Above **0.7** or below **-0.7** = strong correlation
                """)
            else:
                st.warning("Need at least 2 numeric columns.")
    else:
        st.warning("⚠️ No data loaded. Go to Upload & Clean first!")


# ═════════════════════════════════════════════════════════════════════════════
# REPORT
# ═════════════════════════════════════════════════════════════════════════════
elif nav == "📋 Report":
    st.title("📋 Full Data Report")
    st.divider()

    df = get_df()   # ← fixed

    if df is not None:
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(include="object").columns.tolist()

        st.subheader("📌 Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Rows",    len(df))
        col2.metric("Total Columns", len(df.columns))
        col3.metric("Numeric Cols",  len(num_cols))
        col4.metric("Text Cols",     len(cat_cols))

        st.divider()

        if num_cols:
            st.subheader("💰 Numeric Summary")
            st.dataframe(df[num_cols].describe().round(2), use_container_width=True)

        st.divider()

        if cat_cols:
            st.subheader("🔠 Top Values per Category Column")
            for col in cat_cols[:5]:
                with st.expander(f"📌 {col}"):
                    top = df[col].value_counts().head(10).reset_index()
                    top.columns = [col, "Count"]
                    c1, c2 = st.columns(2)
                    with c1:
                        st.dataframe(top, use_container_width=True, hide_index=True)
                    with c2:
                        fig = px.bar(top, x=col, y="Count", title=f"Top {col} values")
                        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("⬇️ Download Report")
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV Report",   data=csv,
                               file_name="full_report.csv", mime="text/csv",
                               use_container_width=True)
        with col2:
            st.download_button("⬇️ Download Excel Report", data=to_excel_bytes(df),
                               file_name="full_report.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
    else:
        st.warning("⚠️ No data loaded. Go to Upload & Clean first!")


# ═════════════════════════════════════════════════════════════════════════════
# HISTORY
# ═════════════════════════════════════════════════════════════════════════════
elif nav == "🕓 History":
    st.title("🕓 Action History")
    st.divider()

    if st.session_state["history"]:
        for i, entry in enumerate(reversed(st.session_state["history"]), 1):
            st.markdown(f"**{i}.** {entry}")
        st.divider()
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state["history"] = []
            st.rerun()
    else:
        st.info("No actions recorded yet.")


st.divider()
st.caption("📊 Business Data Assistant — Built with Python & Streamlit")