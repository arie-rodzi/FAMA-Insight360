import re
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="FAMA Agrosedia Dashboard", page_icon="🌾", layout="wide")

FAMA_NAVY = "#06213F"
FAMA_GOLD = "#C7A64A"
FAMA_GREEN = "#7AB800"
FAMA_BLUE = "#005EB8"
FAMA_CYAN = "#00A6D6"
FAMA_RED = "#C0392B"
BG = "#F6F8FB"
CARD = "#FFFFFF"
PLOTLY_TEMPLATE = "plotly_white"
CAT_COLORS = {
    "ABR": FAMA_NAVY,
    "GBBS": FAMA_GREEN,
    "MEDAN GBBS": FAMA_BLUE,
    "KARAVAN TANI": FAMA_GOLD,
    "MEDAN FOOD TRUCK": FAMA_CYAN,
}

st.markdown(f"""
<style>
    .stApp {{ background: {BG}; }}
    .main .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; }}
    div[data-testid="stMetric"] {{
        background: linear-gradient(135deg, {FAMA_NAVY} 0%, #0E3A67 100%);
        border-radius: 22px;
        padding: 20px 18px;
        color: white;
        box-shadow: 0 10px 30px rgba(6,33,63,.13);
        border: 1px solid rgba(199,166,74,.35);
    }}
    div[data-testid="stMetric"] label, div[data-testid="stMetric"] span {{ color: white !important; }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{ color: {FAMA_GOLD} !important; font-weight: 900; }}
    .hero {{
        background: radial-gradient(circle at top right, rgba(122,184,0,.23), transparent 26%),
                    linear-gradient(135deg, {FAMA_NAVY} 0%, #0A2F55 56%, #071A31 100%);
        border-radius: 28px;
        padding: 28px 32px;
        color: white;
        border: 1px solid rgba(199,166,74,.55);
        box-shadow: 0 18px 45px rgba(6,33,63,.20);
        margin-bottom: 18px;
    }}
    .hero h1 {{ font-size: 2.15rem; margin: 0; font-weight: 900; letter-spacing: -.03em; }}
    .hero p {{ margin: .45rem 0 0 0; opacity: .88; font-size: 1.02rem; }}
    .pill {{ display:inline-block; background:{FAMA_GOLD}; color:{FAMA_NAVY}; padding:6px 13px; border-radius:999px; font-weight:800; margin-bottom:10px; }}
    .panel {{
        background: {CARD};
        border-radius: 24px;
        padding: 18px 20px;
        border: 1px solid rgba(6,33,63,.08);
        box-shadow: 0 10px 28px rgba(6,33,63,.07);
        margin-bottom: 1rem;
    }}
    .section-title {{ color:{FAMA_NAVY}; font-weight:900; font-size:1.25rem; margin-bottom: .25rem; }}
    .small-muted {{ color:#607086; font-size:.9rem; }}
    .status-good {{color:#1D7A34; font-weight:800;}}
    .status-warn {{color:#B47F00; font-weight:800;}}
    .status-bad {{color:#B42318; font-weight:800;}}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def read_workbook(uploaded_file):
    return pd.read_excel(uploaded_file, sheet_name=None)

def clean_col(x):
    return re.sub(r"\s+", " ", str(x).strip().upper())

def detect_category(sheet_name):
    s = clean_col(sheet_name)
    if "ABR" in s:
        return "ABR"
    if "MEDAN" in s and "GBBS" in s:
        return "MEDAN GBBS"
    if "MEDAN" in s and ("FT" in s or "FOOD" in s):
        return "MEDAN FOOD TRUCK"
    if "KARAVAN" in s:
        return "KARAVAN TANI"
    if "GBBS" in s or "GABUNGAN" in s:
        return "GBBS"
    return None

def find_first(cols, keywords):
    for c in cols:
        cc = clean_col(c)
        if any(k in cc for k in keywords):
            return c
    return None

def normalize_sheet(df, sheet_name):
    category = detect_category(sheet_name)
    if category is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    cols = list(df.columns)

    negeri_col = find_first(cols, ["NEGERI", "STATE"])
    nama_col = find_first(cols, ["NAMA USAHAWAN", "NAMA", "USAHAWAN"])
    lokasi_col = find_first(cols, ["LOKASI", "BANDAR", "DAERAH", "MEDAN"])
    usahawan_col = find_first(cols, ["BIL USAHAWAN", "BIL. USAHAWAN"])
    r_col = find_first(cols, [" R", "R"])
    yoy_cols = [c for c in cols if "YOY" in clean_col(c)]

    year_cols = []
    annualize = {}
    for c in cols:
        cc = clean_col(c)
        years = re.findall(r"20(21|22|23|24|25)", cc)
        if years and "YOY" not in cc:
            year = int("20" + years[-1])
            year_cols.append((c, year))
            annualize[c] = 12 if "AVG_MONTHLY" in cc or "MONTHLY" in cc else 1

    records = []
    for _, row in df.iterrows():
        negeri = row.get(negeri_col, None) if negeri_col else None
        nama = row.get(nama_col, None) if nama_col else None
        lokasi = row.get(lokasi_col, None) if lokasi_col else None
        bil_usahawan = row.get(usahawan_col, np.nan) if usahawan_col else np.nan
        r_val = row.get(r_col, np.nan) if r_col else np.nan
        entity = nama if pd.notna(nama) and str(nama).strip() else lokasi
        for c, year in year_cols:
            val = pd.to_numeric(row.get(c), errors="coerce")
            if pd.notna(val):
                records.append({
                    "Kategori": category,
                    "Sheet": sheet_name,
                    "Tahun": year,
                    "Jualan": val * annualize[c],
                    "Negeri": str(negeri).strip().title() if pd.notna(negeri) else "Tidak Dinyatakan",
                    "Nama/Lokasi": str(entity).strip().title() if pd.notna(entity) else "Tidak Dinyatakan",
                    "Bil Usahawan": pd.to_numeric(bil_usahawan, errors="coerce"),
                    "R": pd.to_numeric(r_val, errors="coerce"),
                })
    return pd.DataFrame(records)

def build_dataset(sheets):
    frames = []
    for name, df in sheets.items():
        if clean_col(name) == "SUMMARY":
            continue
        tmp = normalize_sheet(df, name)
        if not tmp.empty:
            frames.append(tmp)
    if not frames:
        return pd.DataFrame()
    data = pd.concat(frames, ignore_index=True)
    # Avoid duplicated Karavan if both raw and clean sheets are uploaded
    if (data["Sheet"].str.contains("KARAVAN", case=False, na=False).sum() > 0 and
        data["Sheet"].str.contains("CLEAN", case=False, na=False).sum() > 0):
        data = data[~((data["Kategori"] == "KARAVAN TANI") & (~data["Sheet"].str.contains("CLEAN", case=False, na=False)))]
    return data

def fmt_rm(x):
    if pd.isna(x): return "-"
    x = float(x)
    if abs(x) >= 1_000_000_000: return f"RM{x/1_000_000_000:.2f}b"
    if abs(x) >= 1_000_000: return f"RM{x/1_000_000:.2f}j"
    if abs(x) >= 1_000: return f"RM{x/1_000:.1f}k"
    return f"RM{x:,.0f}"

def pct(x):
    if pd.isna(x): return "-"
    return f"{x*100:.1f}%"

def outcome_status(r):
    if pd.isna(r): return "Tiada data"
    if r >= .15: return "Melepasi sasaran"
    if r >= 0: return "Hampir sasaran"
    return "Tidak mencapai"

def plot_config(fig, height=420):
    fig.update_layout(
        height=height,
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", color="#24364B"),
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig

st.markdown("""
<div class="hero">
  <div class="pill">FAMA • AGROSEDIA RMK-12</div>
  <h1>Dashboard Outcome Jualan & Prestasi Usahawan</h1>
  <p>Sistem upload Excel untuk analisis 5 komponen: ABR, GBBS, Medan GBBS, Karavan Tani dan Medan Food Truck.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/FAMA_Logo.svg/512px-FAMA_Logo.svg.png", width=120)
    st.title("Kawalan Dashboard")
    uploaded = st.file_uploader("Upload fail Excel gabungan", type=["xlsx", "xls"])
    st.caption("Fail perlu ada sheet mengikut kategori: ABR, GBBS, Medan GBBS, Karavan/KT, Medan FT/Food Truck.")

if not uploaded:
    st.markdown("<div class='panel'><div class='section-title'>Mula guna sistem</div><div class='small-muted'>Upload fail Excel gabungan untuk jana dashboard automatik.</div></div>", unsafe_allow_html=True)
    st.stop()

sheets = read_workbook(uploaded)
data = build_dataset(sheets)
if data.empty:
    st.error("Data tidak dapat dibaca. Pastikan sheet mempunyai nama kategori dan kolum tahun 2021–2025.")
    st.stop()

with st.sidebar:
    kategori = st.multiselect("Kategori", sorted(data["Kategori"].unique()), default=sorted(data["Kategori"].unique()))
    tahun_min, tahun_max = int(data["Tahun"].min()), int(data["Tahun"].max())
    tahun_range = st.slider("Tahun", tahun_min, tahun_max, (tahun_min, tahun_max))
    negeri = st.multiselect("Negeri", sorted(data["Negeri"].dropna().unique()), default=[])
    target = st.number_input("Sasaran Outcome R", value=0.15, step=0.01, format="%.2f")

f = data[data["Kategori"].isin(kategori) & data["Tahun"].between(tahun_range[0], tahun_range[1])]
if negeri:
    f = f[f["Negeri"].isin(negeri)]

# KPI
sales_total = f["Jualan"].sum()
entity_count = f["Nama/Lokasi"].nunique()
cat_count = f["Kategori"].nunique()
latest_year = f["Tahun"].max()
latest_sales = f[f["Tahun"] == latest_year]["Jualan"].sum()
prev_sales = f[f["Tahun"] == latest_year - 1]["Jualan"].sum() if latest_year - 1 in f["Tahun"].values else np.nan
yoy_latest = (latest_sales - prev_sales) / prev_sales if prev_sales and prev_sales > 0 else np.nan

k1, k2, k3, k4 = st.columns(4)
k1.metric("Jumlah Jualan", fmt_rm(sales_total))
k2.metric("Bil. Entiti/Outlet", f"{entity_count:,}")
k3.metric("Kategori Aktif", f"{cat_count}/5")
k4.metric(f"YoY {latest_year}", pct(yoy_latest))

# Summary table by category
cat_summary = (f.groupby("Kategori")
    .agg(Jumlah_Jualan=("Jualan", "sum"), Entiti=("Nama/Lokasi", "nunique"), Negeri=("Negeri", "nunique"), R_Median=("R", "median"))
    .reset_index())
cat_summary["Status"] = cat_summary["R_Median"].apply(lambda x: outcome_status(x if pd.notna(x) else np.nan))

left, right = st.columns([1.45, 1])
with left:
    st.markdown("<div class='panel'><div class='section-title'>Trend Jualan Tahunan Mengikut Kategori</div><div class='small-muted'>Paparan keseluruhan 2021–2025 berdasarkan data Excel yang dimuat naik.</div>", unsafe_allow_html=True)
    trend = f.groupby(["Tahun", "Kategori"], as_index=False)["Jualan"].sum()
    fig = px.area(trend, x="Tahun", y="Jualan", color="Kategori", markers=True, color_discrete_map=CAT_COLORS)
    fig.update_yaxes(tickprefix="RM", separatethousands=True)
    st.plotly_chart(plot_config(fig, 430), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='panel'><div class='section-title'>Komposisi Jualan Mengikut Kategori</div><div class='small-muted'>Sumbangan setiap komponen kepada jumlah jualan terpilih.</div>", unsafe_allow_html=True)
    pie = f.groupby("Kategori", as_index=False)["Jualan"].sum()
    fig = px.pie(pie, names="Kategori", values="Jualan", hole=.58, color="Kategori", color_discrete_map=CAT_COLORS)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(plot_config(fig, 430), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("<div class='panel'><div class='section-title'>Ranking Negeri Berdasarkan Jualan</div>", unsafe_allow_html=True)
    state = f.groupby("Negeri", as_index=False)["Jualan"].sum().sort_values("Jualan", ascending=False).head(15)
    fig = px.bar(state, x="Jualan", y="Negeri", orientation="h", text_auto=".2s", color_discrete_sequence=[FAMA_BLUE])
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_xaxes(tickprefix="RM", separatethousands=True)
    st.plotly_chart(plot_config(fig, 460), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='panel'><div class='section-title'>Outcome R Mengikut Kategori</div><div class='small-muted'>Garis sasaran default = 15%.</div>", unsafe_allow_html=True)
    rdata = cat_summary.dropna(subset=["R_Median"]).sort_values("R_Median", ascending=False)
    fig = px.bar(rdata, x="Kategori", y="R_Median", text=rdata["R_Median"].map(lambda x: f"{x*100:.1f}%"), color="Kategori", color_discrete_map=CAT_COLORS)
    fig.add_hline(y=target, line_dash="dash", line_color=FAMA_RED, annotation_text="Sasaran")
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(plot_config(fig, 460), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

t1, t2 = st.columns([1,1])
with t1:
    st.markdown("<div class='panel'><div class='section-title'>Top 20 Entiti / Outlet</div>", unsafe_allow_html=True)
    top = f.groupby(["Kategori", "Negeri", "Nama/Lokasi"], as_index=False)["Jualan"].sum().sort_values("Jualan", ascending=False).head(20)
    top["Jualan"] = top["Jualan"].map(lambda x: f"RM{x:,.0f}")
    st.dataframe(top, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
with t2:
    st.markdown("<div class='panel'><div class='section-title'>Senarai Risiko / Perlu Intervensi</div><div class='small-muted'>Entiti dengan R negatif atau di bawah sasaran.</div>", unsafe_allow_html=True)
    risk = (f.groupby(["Kategori", "Negeri", "Nama/Lokasi"], as_index=False)
            .agg(Jualan=("Jualan", "sum"), R=("R", "median")))
    risk = risk[pd.notna(risk["R"]) & (risk["R"] < target)].sort_values("R").head(25)
    risk["Jualan"] = risk["Jualan"].map(lambda x: f"RM{x:,.0f}")
    risk["R"] = risk["R"].map(lambda x: f"{x*100:.1f}%")
    st.dataframe(risk, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='panel'><div class='section-title'>Ringkasan Kategori</div>", unsafe_allow_html=True)
display = cat_summary.copy()
display["Jumlah_Jualan"] = display["Jumlah_Jualan"].map(lambda x: f"RM{x:,.0f}")
display["R_Median"] = display["R_Median"].map(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "-")
display.columns = ["Kategori", "Jumlah Jualan", "Bil. Entiti", "Bil. Negeri", "Median R", "Status"]
st.dataframe(display, use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

csv = f.to_csv(index=False).encode("utf-8-sig")
st.download_button("Download data tapis CSV", data=csv, file_name="fama_dashboard_filtered.csv", mime="text/csv")
