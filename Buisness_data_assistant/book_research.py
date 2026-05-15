import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from pathlib import Path

# =============================================================================
# STREAMLIT MEGA PROJECT — Book Research Dashboard
# Site   : books.toscrape.com
# Covers : Every Streamlit concept Days 19-28
# Run    : streamlit run mega_project.py
# =============================================================================

st.set_page_config(
    page_title="📚 Book Research Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
BASE_URL   = "https://books.toscrape.com/catalogue/"
START_URL  = "https://books.toscrape.com/catalogue/page-1.html"
HEADERS    = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


# ── SESSION STATE INIT ────────────────────────────────────────────────────────
if "df"            not in st.session_state: st.session_state["df"]            = None
if "scraped_pages" not in st.session_state: st.session_state["scraped_pages"] = 0
if "history"       not in st.session_state: st.session_state["history"]       = []


# ── SCRAPING FUNCTIONS ────────────────────────────────────────────────────────
def get_soup(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as e:
        st.warning(f"Failed to fetch {url}: {e}")
        return None


def scrape_page(url):
    soup = get_soup(url)
    if not soup:
        return []

    data = []
    for book in soup.find_all("article", class_="product_pod"):
        try:
            a_tag        = book.h3.a
            title        = a_tag.get("title")
            price_tag    = book.find("p", class_="price_color")
            price        = float(price_tag.get_text(strip=True).replace("£", "")) if price_tag else 0.0
            rating_tag   = book.find("p", class_="star-rating")
            rating       = RATING_MAP.get(rating_tag["class"][1], 0) if rating_tag else 0
            avail_tag    = book.find("p", class_="instock")
            availability = avail_tag.get_text(strip=True) if avail_tag else "Out of Stock"

            data.append({
                "Title"       : title,
                "Price (£)"   : price,
                "Rating"      : rating,
                "Availability": availability,
            })
        except Exception:
            continue
    return data


@st.cache_data(show_spinner=False)
def scrape_all(max_pages):
    all_data    = []
    current_url = START_URL

    for page_num in range(1, max_pages + 1):
        results = scrape_page(current_url)
        all_data.extend(results)
        if page_num < max_pages:
            current_url = f"{BASE_URL}page-{page_num + 1}.html"
            time.sleep(random.uniform(0.3, 0.8))

    return pd.DataFrame(all_data)


def clean_df(df):
    df["Price (£)"]    = pd.to_numeric(df["Price (£)"],  errors="coerce").round(2)
    df["Rating"]       = pd.to_numeric(df["Rating"],     errors="coerce")
    df["Availability"] = df["Availability"].str.strip()
    df.dropna(subset=["Title"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://books.toscrape.com/static/oscar/imgs/catalogue/view_icon.png", width=40)
    st.title("Controls")
    st.divider()

    # Scrape settings
    st.subheader("🔧 Scrape Settings")
    max_pages = st.slider("Pages to scrape", min_value=1, max_value=50, value=5)
    run       = st.button("🚀 Run Scraper", use_container_width=True)

    st.divider()

    # Filter settings
    st.subheader("🔍 Filters")
    min_rating  = st.selectbox("Minimum Rating", options=[1, 2, 3, 4, 5], index=0)
    price_range = st.slider("Price Range (£)", min_value=0, max_value=60, value=(0, 60))
    avail_only  = st.checkbox("In Stock Only", value=False)
    search      = st.text_input("Search by title keyword", value="")

    st.divider()

    # Sort settings
    st.subheader("📊 Sort")
    sort_by  = st.selectbox("Sort by",  options=["Title", "Price (£)", "Rating"])
    sort_asc = st.selectbox("Order",    options=["Ascending", "Descending"])

    st.divider()

    # Clear
    if st.button("🗑️ Clear Results", use_container_width=True):
        st.session_state["df"]            = None
        st.session_state["scraped_pages"] = 0
        st.rerun()


# ── MAIN HEADER ───────────────────────────────────────────────────────────────
st.title("📚 Book Research Dashboard")
st.caption("Scrape · Filter · Analyse · Export — all in one place")
st.divider()


# ── SCRAPE ON BUTTON CLICK ────────────────────────────────────────────────────
if run:
    with st.spinner(f"Scraping {max_pages} pages..."):
        df = scrape_all(max_pages)
        df = clean_df(df)

    st.session_state["df"]            = df
    st.session_state["scraped_pages"] = max_pages
    st.session_state["history"].append(f"Scraped {len(df)} books from {max_pages} pages")
    st.success(f"✅ Scraped {len(df)} books from {max_pages} pages!")


# ── SHOW RESULTS ──────────────────────────────────────────────────────────────
if st.session_state["df"] is not None:
    df = st.session_state["df"].copy()

    # ── APPLY FILTERS ─────────────────────────────────────────────────────────
    df = df[df["Rating"]     >= min_rating]
    df = df[df["Price (£)"]  >= price_range[0]]
    df = df[df["Price (£)"]  <= price_range[1]]

    if avail_only:
        df = df[df["Availability"].str.contains("In stock", case=False)]

    if search:
        df = df[df["Title"].str.contains(search, case=False, na=False)]

    # ── APPLY SORT ────────────────────────────────────────────────────────────
    df = df.sort_values(
        by=sort_by,
        ascending=(sort_asc == "Ascending")
    ).reset_index(drop=True)

    # ── TABS ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Results",
        "📈 Charts",
        "🔢 Summary",
        "🕓 History"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — RESULTS
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Books Shown",    len(df))
        col2.metric("Avg Price",      f"£{df['Price (£)'].mean():.2f}")
        col3.metric("Avg Rating",     f"{df['Rating'].mean():.1f} ⭐")
        col4.metric("In Stock",       df["Availability"].str.contains("In stock", case=False).sum())

        st.divider()

        st.subheader(f"Showing {len(df)} books")
        st.dataframe(df, use_container_width=True, height=400)

        st.divider()

        # Download buttons side by side
        col1, col2 = st.columns(2)

        with col1:
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download CSV",
                data=csv,
                file_name="books.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            # Save Excel locally
            output_dir  = Path("output")
            output_dir.mkdir(exist_ok=True)
            excel_path  = output_dir / "books_report.xlsx"

            with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
                df.to_excel(writer, sheet_name="Books", index=False)
                wb         = writer.book
                header_fmt = wb.add_format({
                    "bold": True, "bg_color": "#1F4E79",
                    "color": "#FFFFFF", "border": 1
                })
                ws = writer.sheets["Books"]
                for col_num, name in enumerate(["Title", "Price (£)", "Rating", "Availability"]):
                    ws.write(0, col_num, name, header_fmt)
                ws.set_column("A:A", 55)
                ws.set_column("B:B", 12)
                ws.set_column("C:C", 10)
                ws.set_column("D:D", 15)

            with open(excel_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Excel",
                    data=f,
                    file_name="books_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — CHARTS
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Books per Rating")
            rating_counts = df["Rating"].value_counts().sort_index()
            st.bar_chart(rating_counts)

        with col2:
            st.subheader("💰 Price Distribution")
            price_buckets = pd.cut(
                df["Price (£)"],
                bins=[0, 10, 20, 30, 40, 50, 60],
                labels=["£0-10","£10-20","£20-30","£30-40","£40-50","£50-60"]
            ).value_counts().sort_index()
            st.bar_chart(price_buckets)

        st.divider()

        st.subheader("⭐ Average Price by Rating")
        avg_price_by_rating = df.groupby("Rating")["Price (£)"].mean().round(2)
        st.bar_chart(avg_price_by_rating)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("📋 Full Summary Statistics")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**💰 Price Stats**")
            price_stats = pd.DataFrame({
                "Metric": ["Average", "Cheapest", "Most Expensive", "Median"],
                "Value" : [
                    f"£{df['Price (£)'].mean():.2f}",
                    f"£{df['Price (£)'].min():.2f}",
                    f"£{df['Price (£)'].max():.2f}",
                    f"£{df['Price (£)'].median():.2f}",
                ]
            })
            st.dataframe(price_stats, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("**⭐ Rating Stats**")
            rating_stats = pd.DataFrame({
                "Rating": [1, 2, 3, 4, 5],
                "Count" : [
                    len(df[df["Rating"] == r]) for r in [1, 2, 3, 4, 5]
                ]
            })
            st.dataframe(rating_stats, use_container_width=True, hide_index=True)

        st.divider()

        st.markdown("**📦 Availability Breakdown**")
        avail_counts = df["Availability"].value_counts().reset_index()
        avail_counts.columns = ["Status", "Count"]
        st.dataframe(avail_counts, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — HISTORY
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("🕓 Scrape History")

        if st.session_state["history"]:
            for i, entry in enumerate(reversed(st.session_state["history"]), 1):
                st.markdown(f"**{i}.** {entry}")
        else:
            st.info("No scrape history yet.")

        if st.button("Clear History"):
            st.session_state["history"] = []
            st.rerun()

else:
    # ── EMPTY STATE ───────────────────────────────────────────────────────────
    st.info("👈 Set your page count in the sidebar and click **Run Scraper** to start!")

    col1, col2, col3 = st.columns(3)
    col1.metric("Site",    "books.toscrape.com")
    col2.metric("Max Pages", "50")
    col3.metric("Books/Page", "20")