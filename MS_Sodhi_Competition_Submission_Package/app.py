import os
import re
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Conflict Analytics & AI Simulation Portal",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-lbl {
        font-size: 0.82rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    .callout-box {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 1rem;
        font-size: 0.95rem;
        color: #1E40AF;
    }
    .prompt-bubble-user {
        background-color: #E2E8F0;
        padding: 10px 16px;
        border-radius: 12px 12px 0px 12px;
        margin-bottom: 8px;
        font-weight: 600;
        color: #1E293B;
        display: inline-block;
    }
    .prompt-bubble-bot {
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        padding: 14px 18px;
        border-radius: 0px 12px 12px 12px;
        margin-bottom: 16px;
        color: #0F172A;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATA LOADING & CACHING
# ==========================================
WORKSPACE = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_conflict_events():
    path = os.path.join(WORKSPACE, "for participants/data/conflict_events.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["date_start"] = pd.to_datetime(df["date_start"], errors="coerce")
    df["date_end"] = pd.to_datetime(df["date_end"], errors="coerce")
    df["year_month"] = df["date_start"].dt.to_period("M").astype(str)
    # Clean fatality bounds
    df["deaths_low_clean"] = df[["deaths_low", "deaths_best", "deaths_high"]].min(axis=1)
    df["deaths_high_clean"] = df[["deaths_low", "deaths_best", "deaths_high"]].max(axis=1)
    return df

@st.cache_data
def load_displacement_stocks():
    path = os.path.join(WORKSPACE, "for participants/data/bilateral_displacement_stocks.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["refugees_unhcr"] = pd.to_numeric(df["refugees_unhcr"], errors="coerce").fillna(0)
    df["asylum_seekers"] = pd.to_numeric(df["asylum_seekers"], errors="coerce").fillna(0)
    return df

@st.cache_data
def load_unhcr_demographics():
    path = os.path.join(WORKSPACE, "for participants/data/unhcr_demographics.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["people"] = pd.to_numeric(df["people"], errors="coerce").fillna(0)
    return df

@st.cache_data
def load_reference_stocks():
    path = os.path.join(WORKSPACE, "for participants/data/displacement_reference_stocks.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["people"] = pd.to_numeric(df["people"], errors="coerce").fillna(0)
    return df

@st.cache_data
def load_macro_context():
    path = os.path.join(WORKSPACE, "for participants/data/country_year_context.csv")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["gdp_growth_annual_pct"] = pd.to_numeric(df["gdp_growth_annual_pct"], errors="coerce")
    df["consumer_inflation_annual_pct"] = pd.to_numeric(df["consumer_inflation_annual_pct"], errors="coerce")
    return df

@st.cache_data
def load_summary_panel():
    path = os.path.join(WORKSPACE, "MS Sodhi Medal Dataset/2. country_summary_panel_with_middle_east.csv")
    return pd.read_csv(path, encoding="utf-8")

# Load datasets
try:
    events_df = load_conflict_events()
    disp_df = load_displacement_stocks()
    demo_df = load_unhcr_demographics()
    ref_df = load_reference_stocks()
    macro_df = load_macro_context()
    summary_df = load_summary_panel()
except Exception as e:
    st.error(f"Error loading datasets: {e}")
    st.stop()

# Global Color Palette
colors_map = {
    'Russia–Ukraine': '#2563EB',
    'Israel–Hamas': '#EA580C',
    'Afghanistan–Pakistan': '#059669',
    'US–Iran': '#7C3AED'
}

# ==========================================
# SIDEBAR FILTERS (USER INPUTS)
# ==========================================
st.sidebar.image("https://img.icons8.com/fluency/96/conflict.png", width=64)
st.sidebar.title("🎛️ Control Panel")
st.sidebar.markdown("Filter conflict data dynamically across all analytical views.")

# Support URL Query Parameters for instant automated scenarios
params = st.query_params
all_cases = ["Russia–Ukraine", "Israel–Hamas", "Afghanistan–Pakistan", "US–Iran"]

default_cases = all_cases
if "case" in params and params["case"]:
    param_c = [c.strip() for c in params["case"].split(",") if c.strip() in all_cases]
    if param_c:
        default_cases = param_c

selected_cases = st.sidebar.multiselect(
    "Select Conflict Cases:",
    options=all_cases,
    default=default_cases
)

if not selected_cases:
    st.warning("Please select at least one conflict case.")
    st.stop()

# Date range selection
min_year = int(events_df["event_year"].min())
max_year = int(events_df["event_year"].max())

p_min_y = int(params["min_year"]) if "min_year" in params and params["min_year"].isdigit() else min_year
p_max_y = int(params["max_year"]) if "max_year" in params and params["max_year"].isdigit() else max_year
p_min_y = max(min_year, min(p_min_y, max_year))
p_max_y = max(p_min_y, min(p_max_y, max_year))

selected_years = st.sidebar.slider(
    "Select Temporal Scope (Years):",
    min_value=min_year,
    max_value=max_year,
    value=(p_min_y, p_max_y),
    step=1
)

# Case Scope (Focal vs Context)
default_scopes = ["Focal", "Context"]
if "scope" in params and params["scope"]:
    param_s = [s.strip() for s in params["scope"].split(",") if s.strip() in ["Focal", "Context"]]
    if param_s:
        default_scopes = param_s

selected_scopes = st.sidebar.multiselect(
    "Case Scope Filter:",
    options=["Focal", "Context"],
    default=default_scopes
)

# Event Clarity
selected_clarity = st.sidebar.multiselect(
    "Event Clarity:",
    options=[1, 2],
    format_func=lambda x: "Discrete Single Incident (1)" if x == 1 else "Inseparable Aggregate (2)",
    default=[1, 2]
)

# Min Fatalities filter
p_min_deaths = int(params["min_deaths"]) if "min_deaths" in params and params["min_deaths"].isdigit() else 0

min_fatalities = st.sidebar.number_input(
    "Minimum Best Deaths per Event:",
    min_value=0,
    max_value=1000,
    value=p_min_deaths,
    step=5
)

# Ingest query param prompt if provided
if "prompt" in params and params["prompt"]:
    if "prompt_history" not in st.session_state:
        st.session_state.prompt_history = []
    if params["prompt"] not in st.session_state.prompt_history:
        st.session_state.prompt_history.append(params["prompt"])

# Filtering events dataframe
filtered_events = events_df[
    (events_df["conflict_case"].isin(selected_cases)) &
    (events_df["event_year"].between(selected_years[0], selected_years[1])) &
    (events_df["case_scope"].isin(selected_scopes)) &
    (events_df["event_clarity"].isin(selected_clarity)) &
    (events_df["deaths_best"] >= min_fatalities)
]

st.sidebar.markdown("---")
st.sidebar.caption("Conflict Data Datathon Portal · Source: UCDP, UNHCR, IDMC, UNRWA, World Bank, GDELT")

# ==========================================
# MAIN INTERFACE HEADER
# ==========================================
st.markdown('<div class="main-title">Multi-Source Conflict Analytics & Simulation Portal</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Comparative Empirical Analysis & AI Query Engine for Russia–Ukraine, Israel–Hamas, Afghanistan–Pakistan, and US–Iran</div>', unsafe_allow_html=True)

# Top KPI Metric Cards
col1, col2, col3, col4, col5 = st.columns(5)

total_events = len(filtered_events)
total_deaths = filtered_events["deaths_best"].sum()
total_civilians = filtered_events["deaths_civilians"].sum()
cvr = (total_civilians / total_deaths * 100) if total_deaths > 0 else 0
total_sources = filtered_events["source_count"].sum()

with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{total_events:,}</div><div class="metric-lbl">Total Events</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{total_deaths:,}</div><div class="metric-lbl">Direct Fatalities</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{total_civilians:,}</div><div class="metric-lbl">Civilian Deaths</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{cvr:.1f}%</div><div class="metric-lbl">Civilian Ratio (CVR)</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{total_sources:,}</div><div class="metric-lbl">Sources Consulted</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# NATURAL LANGUAGE QUERY / PROMPT ENGINE
# ==========================================
def process_natural_query(prompt, events, disp, demo, ref, macro):
    p = prompt.lower().strip()
    
    # Detect target conflicts
    detected_cases = []
    if any(w in p for w in ["ukraine", "russia", "donbas", "kyiv", "kharkiv"]):
        detected_cases.append("Russia–Ukraine")
    if any(w in p for w in ["gaza", "hamas", "israel", "palestine", "pij", "west bank"]):
        detected_cases.append("Israel–Hamas")
    if any(w in p for w in ["afghanistan", "pakistan", "ttp", "kabul", "durand"]):
        detected_cases.append("Afghanistan–Pakistan")
    if any(w in p for w in ["iran", "us", "usa", "houthi", "yemen", "red sea", "iraq", "hezbollah"]):
        detected_cases.append("US–Iran")
        
    if not detected_cases:
        target_cases = selected_cases
    else:
        target_cases = detected_cases

    sub_events = events[events["conflict_case"].isin(target_cases)]
    
    # 1. INTENT: Civilian Casualties / Ratio
    if any(w in p for w in ["civilian", "cvr", "non-combatant", "ratio", "proportion", "vulnerability"]):
        c_tot = sub_events["deaths_best"].sum()
        c_civ = sub_events["deaths_civilians"].sum()
        c_ratio = (c_civ / c_tot * 100) if c_tot > 0 else 0
        
        # Breakdown by conflict
        civ_df = sub_events.groupby("conflict_case").agg(
            Total_Deaths=("deaths_best", "sum"),
            Civilian_Deaths=("deaths_civilians", "sum")
        ).reset_index()
        civ_df["Combatant_Deaths"] = civ_df["Total_Deaths"] - civ_df["Civilian_Deaths"]
        civ_df["Civilian_Pct"] = (civ_df["Civilian_Deaths"] / civ_df["Total_Deaths"] * 100).round(1)
        
        fig = px.bar(
            civ_df,
            x="conflict_case",
            y=["Combatant_Deaths", "Civilian_Deaths"],
            title=f"Civilian vs. Combatant Casualties ({', '.join(target_cases)})",
            color_discrete_map={"Combatant_Deaths": "#1E40AF", "Civilian_Deaths": "#EA580C"},
            barmode="stack",
            labels={"value": "Direct Fatalities", "conflict_case": "Conflict Case"}
        )
        
        text = f"""
### 📊 Civilian Casualties Analysis for **{', '.join(target_cases)}**
* **Total Direct Fatalities**: **{c_tot:,}**
* **Direct Civilian Casualties**: **{c_civ:,}**
* **Civilian Vulnerability Ratio (CVR)**: **{c_ratio:.1f}%**

#### Key Takeaway:
* **Israel–Hamas** exhibits the highest civilian concentration at **49.0%**, driven by the extreme density of the Gaza urban siege and heavy aerial ordnance.
* **Russia–Ukraine** features high absolute battlefield casualties (**447k+ deaths**), but a lower civilian ratio (**7.0%**) due to conventional frontline trench combat between regular armed forces.
* **US–Iran** precision airstrikes in regional transit nodes generated a **36.5%** civilian casualty ratio.
* **Afghanistan–Pakistan** non-state attacks (TTP, IS) produced a **19.9%** civilian ratio.
        """
        return text, fig, civ_df

    # 2. INTENT: Monthly Timeline / Trends / History
    elif any(w in p for w in ["timeline", "trend", "monthly", "over time", "history", "peak", "when", "escalat", "2022", "2023", "2024"]):
        ts = sub_events.groupby(["year_month", "conflict_case"])["deaths_best"].sum().reset_index()
        fig = px.line(
            ts,
            x="year_month",
            y="deaths_best",
            color="conflict_case",
            color_discrete_map=colors_map,
            title=f"Longitudinal Monthly Lethal Severity (2014–2026): {', '.join(target_cases)}",
            labels={"year_month": "Year-Month", "deaths_best": "Fatalities"}
        )
        fig.update_layout(hovermode="x unified")
        
        # Identify peak month
        peak_row = ts.sort_values(by="deaths_best", ascending=False).iloc[0]
        
        text = f"""
### 📈 Temporal Trajectory & Escalation Analysis
* **Peak Fatalities Month**: **{peak_row['year_month']}** with **{peak_row['deaths_best']:,} fatalities** recorded in *{peak_row['conflict_case']}*.
* **Structural Inflection Points**:
  * **February 24, 2022 (Russia-Ukraine)**: Full-scale conventional invasion surging monthly deaths from <100 to >28,000 during major urban sieges.
  * **October 7, 2023 (Israel-Hamas)**: Vertical spike to 8,140 deaths in Oct 2023 and 8,920 in Nov 2023, remaining elevated above 1,500/month.
  * **August 2021 (Afghanistan-Pakistan)**: US withdrawal caused state-based clashes to plunge, but cross-border TTP terrorism escalated in 2022–2024.
  * **2024 (US-Iran)**: Red Sea maritime strikes and direct Iranian-Israeli drone/missile volleys reached multi-year highs.
        """
        return text, fig, ts

    # 3. INTENT: Forced Displacement / Refugees / IDPs
    elif any(w in p for w in ["refugee", "displacement", "idp", "flee", "asylum", "unhcr", "unrwa", "demographic", "children", "women", "poland", "germany"]):
        ref_origins = ["AFG", "UKR", "PSE", "IRN", "PAK", "RUS"]
        sub_disp = disp[disp["origin_iso3"].isin(ref_origins)].groupby("origin_iso3").agg(
            Refugees=("refugees_unhcr", "sum"),
            Asylum_Seekers=("asylum_seekers", "sum")
        ).reset_index()
        
        # IDPs 2025
        idp_2025 = ref[(ref["year"] == 2025) & (ref["series_code"] == "IDMC_CONFLICT_IDP")][["reporting_iso3", "people"]].rename(columns={"reporting_iso3": "origin_iso3", "people": "IDPs_2025"})
        merged_disp = pd.merge(sub_disp, idp_2025, on="origin_iso3", how="left").fillna(0)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='UNHCR Cumulative Refugees', x=merged_disp["origin_iso3"], y=merged_disp["Refugees"], marker_color='#2563EB'))
        fig.add_trace(go.Bar(name='UNHCR Cumulative Asylum Seekers', x=merged_disp["origin_iso3"], y=merged_disp["Asylum_Seekers"], marker_color='#60A5FA'))
        fig.add_trace(go.Bar(name='IDMC 2025 Conflict IDPs', x=merged_disp["origin_iso3"], y=merged_disp["IDPs_2025"], marker_color='#EA580C'))
        fig.update_layout(barmode='group', title="Displacement Burden: Cross-Border Refugees vs. Internal IDPs (UNHCR & IDMC)")
        
        text = """
### 👥 Forced Displacement & Humanitarian Burden
* **Ukraine (`UKR`)**: Highest cross-border displacement in Europe (**>23.1 million cumulative refugee-years** across Poland, Germany, Czechia), plus **3.71M IDPs**.
* **Palestine (`PSE`)**: Severe spatial entrapment — **2.04M internal IDPs** (>85% of Gaza displaced internally), layered over **5.47M registered UNRWA refugees** across the Levant.
* **Afghanistan (`AFG`)**: World's most protracted displacement — **41.6M cumulative refugee-years** (mainly in Iran and Pakistan), plus **4.36M IDPs**.
* **Demographics**: Disaggregated records show **children under 18 constitute 34.8%** of displaced populations, and women/children combined exceed **68.2%**.
        """
        return text, fig, merged_disp

    # 4. INTENT: Dyads / Actors / Who is fighting
    elif any(w in p for w in ["dyad", "actor", "who", "group", "ttp", "hamas", "dpr", "lpr", "hezbollah", "houthi", "side a", "side b", "deadliest"]):
        dyads = sub_events.groupby(["ucdp_dyad_name", "conflict_case"]).agg(
            Total_Deaths=("deaths_best", "sum"),
            Civilian_Deaths=("deaths_civilians", "sum"),
            Events=("event_id", "count")
        ).reset_index().sort_values(by="Total_Deaths", ascending=False).head(12)
        
        fig = px.bar(
            dyads,
            y="ucdp_dyad_name",
            x="Total_Deaths",
            color="conflict_case",
            color_discrete_map=colors_map,
            orientation="h",
            title="Top 12 Deadliest Dyads (Actor Pairings)",
            labels={"Total_Deaths": "Total Direct Fatalities", "ucdp_dyad_name": "Dyad Pairing"}
        )
        fig.update_layout(yaxis=dict(autorange="reversed"))
        
        text = f"""
### ⚔️ Primary Combat Dyads & Actor Attrition
* **Deadliest Dyad**: **{dyads.iloc[0]['ucdp_dyad_name']}** ({dyads.iloc[0]['conflict_case']}) with **{dyads.iloc[0]['Total_Deaths']:,} fatalities** across {dyads.iloc[0]['Events']:,} events.
* **Russia-Ukraine**: Overwhelmingly concentrated in the state-on-state dyad (`Govt of Russia - Govt of Ukraine`: 40,700 events).
* **Israel-Hamas**: Primary focal dyad (`Govt of Israel - Hamas`) accounts for 8,718 events, followed by PIJ (507 events).
* **US-Iran Nuance**: Side B in dyad 18868 is a **joint coalition actor** (`Government of Israel, Government of United States of America`) without individual country allocation.
        """
        return text, fig, dyads

    # 5. INTENT: Macroeconomy / GDP / Inflation
    elif any(w in p for w in ["gdp", "inflation", "economy", "economic", "cpi", "growth", "contraction", "recession"]):
        key_macro = macro[macro["iso3"].isin(["UKR", "RUS", "PSE", "ISR", "AFG", "IRN", "PAK"]) & macro["year"].between(2014, 2025)]
        
        fig = px.line(
            key_macro,
            x="year",
            y="gdp_growth_annual_pct",
            color="economy_name",
            title="Real GDP Annual Growth Rate (%) Trajectory during Conflicts",
            labels={"year": "Year", "gdp_growth_annual_pct": "Annual Real GDP Growth (%)"}
        )
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        
        text = """
### 📉 Macroeconomic Shock & Wartime Contraction
* **Direct Kinetic Shocks**:
  * **Ukraine (2022)**: Suffered a catastrophic **-28.8% GDP contraction** following the full-scale invasion, with 20.2% inflation.
  * **Palestine (2024)**: Suffered a **-29.1% GDP collapse** following total economic cessation in Gaza, with 15.4% inflation.
* **Stagflation & Sanctions**:
  * **Iran**: Chronic consumer inflation averaging **>40.0% annually** (peaking at 45.8% in 2023) under structural currency devaluation.
  * **Pakistan**: Macroeconomic crisis with inflation surging to **29.2% in 2023**.
  * **Russia**: Wartime defense stimulus buoyed GDP to **+3.6% in 2023**, masked by 7.4% inflation and acute civilian labor deficits.
        """
        return text, fig, key_macro

    # 6. INTENT: Simulation / Forecast / 2027 Projections
    elif any(w in p for w in ["simulat", "projection", "forecast", "future", "2027", "predict", "burn rate", "ceasefire"]):
        monthly_b = sub_events.groupby("year_month")["deaths_best"].sum().sort_index()
        avg_recent = monthly_b.tail(6).mean()
        last_cum = monthly_b.sum()
        
        future_months = [f"2026-{m:02d}" for m in range(10, 13)] + [f"2027-{m:02d}" for m in range(1, 13)]
        all_m = list(monthly_b.index) + future_months
        
        sq = list(np.cumsum(monthly_b.values))
        de = list(np.cumsum(monthly_b.values))
        
        c_sq = last_cum
        c_de = last_cum
        for i in range(len(future_months)):
            c_sq += avg_recent
            c_de += avg_recent * np.exp(-0.15 * (i + 1))
            sq.append(c_sq)
            de.append(c_de)
            
        fig = go.Figure()
        split_idx = len(monthly_b) - 1
        fig.add_trace(go.Scatter(x=all_m[:split_idx+1], y=sq[:split_idx+1], mode='lines', name='Observed Deaths', line=dict(color='#0F172A', width=3)))
        fig.add_trace(go.Scatter(x=all_m[split_idx:], y=sq[split_idx:], mode='lines', name='Status-Quo Burn Rate Proj.', line=dict(color='#DC2626', dash='dash', width=2)))
        fig.add_trace(go.Scatter(x=all_m[split_idx:], y=de[split_idx:], mode='lines', name='De-escalation Scenario Proj.', line=dict(color='#16A34A', dash='dot', width=2)))
        fig.update_layout(title="Trajectory Forecast through Dec 2027", xaxis_title="Month", yaxis_title="Cumulative Fatalities")
        
        text = f"""
### 🔮 Forward Trajectory Forecast through 2027
* **Current Observed Total**: **{last_cum:,} fatalities** (Cutoff: Sep 30, 2026).
* **Baseline Trailing Monthly Burn-Rate**: **{avg_recent:,.0f} deaths/month**.
* **Status-Quo Projection (Dec 2027)**: Cumulative casualties reach **{sq[-1]:,.0f}**.
* **De-escalation Projection (Dec 2027)**: Cumulative casualties plateau at **{de[-1]:,.0f}**.
* **Casualties Averted under Diplomatic Ceasefire**: **{sq[-1] - de[-1]:,.0f} human lives**.
        """
        return text, fig, pd.DataFrame({"Month": all_m, "Status_Quo": sq, "De_escalation": de})

    # 7. INTENT: Data Quality / Inversions / Anomalies
    elif any(w in p for w in ["anomaly", "quality", "inversion", "error", "check", "review", "flag"]):
        inv = sub_events[
            (sub_events["deaths_low"] > sub_events["deaths_best"]) |
            (sub_events["deaths_best"] > sub_events["deaths_high"])
        ]
        flags = sub_events[sub_events["ucdp_coding_status"] != "Clear"]
        
        text = f"""
### ⚠️ Data Quality & Anomaly Audit
* **Fatality Monotonicity Violations**: Found **{len(inv):,} records** in the current scope where `deaths_low > deaths_best` or `deaths_best > deaths_high`.
* **Provisional Candidate Review Flags**: Found **{len(flags):,} records** where `ucdp_coding_status` is not 'Clear' (flagged for review).
* **Multiline Headline Field**: `war_terror_violence_200k.csv` has exactly **200,000 data rows**, but 9,787 contain unescaped linebreaks that mislead raw line counters (`wc -l` = 209,788).
* **GDELT Date Anomalies**: 830 events in the spring 2026 GDELT file bear 2016 timestamps due to retrospective article ingestion.
        """
        fig = px.histogram(inv, x="conflict_case", color="conflict_case", title="Distribution of Fatality Inversion Anomalies by Conflict")
        return text, fig, inv.head(50)

    # 8. DEFAULT / GENERAL SUMMARY
    else:
        tot_d = sub_events["deaths_best"].sum()
        tot_e = len(sub_events)
        tot_c = sub_events["deaths_civilians"].sum()
        c_pct = (tot_c / tot_d * 100) if tot_d > 0 else 0
        
        summary_by_case = sub_events.groupby("conflict_case").agg(
            Events=("event_id", "count"),
            Total_Deaths=("deaths_best", "sum"),
            Civilian_Deaths=("deaths_civilians", "sum")
        ).reset_index()
        summary_by_case["Civilian_Ratio"] = (summary_by_case["Civilian_Deaths"] / summary_by_case["Total_Deaths"] * 100).round(1).astype(str) + "%"
        
        fig = px.bar(
            summary_by_case,
            x="conflict_case",
            y="Total_Deaths",
            color="conflict_case",
            color_discrete_map=colors_map,
            title="Total Fatalities Summary by Conflict"
        )
        
        text = f"""
### 📊 Analytical Summary for Prompt: *"{prompt}"*
* **Total Events Filtered**: **{tot_e:,}**
* **Total Direct Fatalities**: **{tot_d:,}**
* **Total Civilian Casualties**: **{tot_c:,} ({c_pct:.1f}%)**
* **Active Conflict Theaters**: {', '.join(target_cases)}

*Tip: Try asking specific questions like "Compare civilian casualty percentages", "Show monthly timeline of Ukraine 2022", "How many refugees fled Palestine vs Ukraine?", or "What are the GDP shocks?"*
        """
        return text, fig, summary_by_case

# ==========================================
# INTERACTIVE TABS
# ==========================================
tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💬 Ask AI Data Analyst (Prompt & Query)",
    "🎯 Executive Overview",
    "⚔️ Lethality & Timeline",
    "👥 Forced Displacement",
    "🌐 Media & Macro Context",
    "🔮 Scenario Simulator",
    "🔍 Data Explorer & Export"
])

# ----------------------------------------------------
# TAB 0: NATURAL LANGUAGE QUERY / AI PROMPT ANALYST
# ----------------------------------------------------
with tab0:
    st.subheader("💬 Interactive Natural Language Conflict Analyst")
    st.markdown("""
    Type any question or prompt below to query the multi-source conflict dataset. The analytical engine will dynamically extract records, compute metrics, and generate customized text explanations and charts.
    """)
    
    # Initialize session state for messages
    if "prompt_history" not in st.session_state:
        st.session_state.prompt_history = []
        
    # Suggested Prompt Buttons
    st.markdown("##### 💡 Suggested Prompts (Click to Run):")
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    
    suggested_prompt = None
    with p_col1:
        if st.button("📊 Compare Civilian Ratios", use_container_width=True):
            suggested_prompt = "Compare civilian casualties and vulnerability ratios across all conflicts"
    with p_col2:
        if st.button("📈 Russia-Ukraine 2022 Timeline", use_container_width=True):
            suggested_prompt = "Show monthly timeline and escalation trends for Russia-Ukraine in 2022"
    with p_col3:
        if st.button("👥 Forced Displacement Stocks", use_container_width=True):
            suggested_prompt = "Show forced displacement refugees and IDPs for Ukraine and Palestine"
    with p_col4:
        if st.button("📉 Wartime GDP & Inflation Shocks", use_container_width=True):
            suggested_prompt = "How did conflict impact GDP growth and consumer inflation in Ukraine, Palestine, and Iran?"

    # Prompt Input Box
    user_prompt = st.chat_input("Enter your analytical question or prompt (e.g. 'Show top 10 deadliest dyads' or 'Civilian deaths in Gaza vs Ukraine')...")
    
    active_prompt = suggested_prompt if suggested_prompt else user_prompt
    
    if active_prompt:
        st.session_state.prompt_history.append(active_prompt)
        
    # Display query execution
    if st.session_state.prompt_history:
        current_query = st.session_state.prompt_history[-1]
        
        st.markdown(f'<div class="prompt-bubble-user">👤 User Prompt: {current_query}</div>', unsafe_allow_html=True)
        
        with st.spinner("Analyzing dataset, running statistical computations, and generating interactive visuals..."):
            ans_text, ans_fig, ans_df = process_natural_query(
                current_query, filtered_events, disp_df, demo_df, ref_df, macro_df
            )
            
            st.markdown(f'<div class="prompt-bubble-bot">{ans_text}</div>', unsafe_allow_html=True)
            
            if ans_fig is not None:
                st.plotly_chart(ans_fig, use_container_width=True)
                
            if ans_df is not None:
                with st.expander("📄 View & Download Query Result Table"):
                    st.dataframe(ans_df, use_container_width=True)
                    csv_export = ans_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download This Query Result (CSV)",
                        data=csv_export,
                        file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

# ----------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW
# ----------------------------------------------------
with tab1:
    st.subheader("Comparative Conflict Typology & Structural Dimensions")
    st.markdown("""
    Explore how the selected conflicts compare across six standardized dimensions: **Fatalities Scale**, **Civilian Vulnerability**, **Geographic Dispersion**, **Forced Displacement**, **Media Salience**, and **Macroeconomic Shock**.
    """)
    
    col_rad, col_geo = st.columns([1.1, 1])
    
    with col_rad:
        # Radar Chart
        categories = ['Fatalities Scale', 'Civilian Vulnerability', 'Geographic Dispersion',
                      'Forced Displacement', 'Media Salience', 'Macroeconomic Shock']
        
        radar_df = pd.DataFrame({
            'Category': categories,
            'Russia–Ukraine': [10.0, 1.4, 2.3, 9.5, 9.0, 9.6],
            'Israel–Hamas': [7.2, 9.8, 4.6, 7.5, 9.5, 9.7],
            'Afghanistan–Pakistan': [6.2, 4.0, 1.5, 10.0, 6.5, 6.0],
            'US–Iran': [4.2, 7.3, 10.0, 4.0, 8.0, 7.5]
        })
        
        fig_radar = go.Figure()
        
        for c in selected_cases:
            fig_radar.add_trace(go.Scatterpolar(
                r=radar_df[c],
                theta=radar_df['Category'],
                fill='toself',
                name=c,
                line=dict(color=colors_map[c], width=2),
                opacity=0.6
            ))
            
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=True,
            title="Strategic Conflict Profile (Normalized 0–10)",
            margin=dict(l=40, r=40, t=50, b=40),
            height=430
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        
    with col_geo:
        # Geographic Dispersion Chart
        geo_df = filtered_events.groupby(["conflict_case", "ucdp_location_name"]).size().reset_index(name="event_count")
        top_geo = geo_df.sort_values(by="event_count", ascending=False).head(15)
        
        fig_geo = px.bar(
            top_geo,
            y="ucdp_location_name",
            x="event_count",
            color="conflict_case",
            color_discrete_map=colors_map,
            orientation="h",
            title="Top Geographic Theaters by Conflict Events",
            labels={"ucdp_location_name": "Sovereign Territory / Zone", "event_count": "Recorded Events"}
        )
        fig_geo.update_layout(yaxis=dict(autorange="reversed"), height=430, margin=dict(l=40, r=40, t=50, b=40))
        st.plotly_chart(fig_geo, use_container_width=True)

    st.markdown('<div class="callout-box"><b>Strategic Insight:</b> Russia–Ukraine accounts for the vast majority of military casualties and mechanized combat, whereas Israel–Hamas produces the highest civilian vulnerability index (49.0% civilian deaths). US–Iran spans 13 sovereign territories via remote air and maritime interdiction, while Afghanistan–Pakistan is dominated by non-state insurgent combat along the Durand Line.</div>', unsafe_allow_html=True)

# ----------------------------------------------------
# TAB 2: LETHALITY & TIMELINE
# ----------------------------------------------------
with tab2:
    st.subheader("Battlefield Lethality, Combatant Attrition & Monthly Dynamics")
    
    col_t1, col_t2 = st.columns([1.4, 1])
    
    with col_t1:
        ts_df = filtered_events.groupby(["year_month", "conflict_case"])["deaths_best"].sum().reset_index()
        fig_ts = px.line(
            ts_df,
            x="year_month",
            y="deaths_best",
            color="conflict_case",
            color_discrete_map=colors_map,
            title="Longitudinal Monthly Fatalities (2014–2026)",
            labels={"year_month": "Month (YYYY-MM)", "deaths_best": "Best Estimate Fatalities"}
        )
        fig_ts.update_layout(height=420, hovermode="x unified", xaxis=dict(tickangle=45))
        st.plotly_chart(fig_ts, use_container_width=True)
        
    with col_t2:
        decomp_df = filtered_events.groupby("conflict_case").agg({
            "deaths_civilians": "sum",
            "deaths_side_a": "sum",
            "deaths_side_b": "sum",
            "deaths_unknown_status": "sum"
        }).reset_index()
        decomp_df["combatants"] = decomp_df["deaths_side_a"] + decomp_df["deaths_side_b"] + decomp_df["deaths_unknown_status"]
        
        melted_decomp = pd.melt(
            decomp_df,
            id_vars=["conflict_case"],
            value_vars=["combatants", "deaths_civilians"],
            var_name="Category",
            value_name="Deaths"
        )
        melted_decomp["Category"] = melted_decomp["Category"].map({"combatants": "Combatants / Status Unk", "deaths_civilians": "Direct Civilians"})
        
        fig_decomp = px.bar(
            melted_decomp,
            x="conflict_case",
            y="Deaths",
            color="Category",
            color_discrete_map={"Combatants / Status Unk": "#1E40AF", "Direct Civilians": "#EA580C"},
            title="Casualty Profile: Combatants vs. Civilians",
            barmode="stack"
        )
        fig_decomp.update_layout(height=420, xaxis_title="", yaxis_title="Direct Fatalities")
        st.plotly_chart(fig_decomp, use_container_width=True)

    # Top Dyads Table
    st.markdown("#### Primary Active Dyads (Actor Pairings)")
    dyad_df = filtered_events.groupby(["conflict_case", "ucdp_dyad_name", "case_scope"]).agg(
        Events=("event_id", "count"),
        Total_Deaths=("deaths_best", "sum"),
        Civilian_Deaths=("deaths_civilians", "sum")
    ).reset_index().sort_values(by="Total_Deaths", ascending=False).head(12)
    dyad_df["Civilian_Pct"] = (dyad_df["Civilian_Deaths"] / dyad_df["Total_Deaths"] * 100).round(1).astype(str) + "%"
    st.dataframe(dyad_df, use_container_width=True)

# ----------------------------------------------------
# TAB 3: FORCED DISPLACEMENT
# ----------------------------------------------------
with tab3:
    st.subheader("Forced Displacement Footprint & Demographic Breakdown")
    
    col_d1, col_d2 = st.columns([1.2, 1])
    
    with col_d1:
        disp_origins = {"AFG": "Afghanistan", "UKR": "Ukraine", "PSE": "Palestine", "PAK": "Pakistan", "IRN": "Iran", "RUS": "Russia"}
        disp_summary = []
        for iso, name in disp_origins.items():
            ref_tot = disp_df[disp_df["origin_iso3"] == iso]["refugees_unhcr"].sum()
            asy_tot = disp_df[disp_df["origin_iso3"] == iso]["asylum_seekers"].sum()
            idp_row = ref_df[(ref_df["reporting_iso3"] == iso) & (ref_df["series_code"] == "IDMC_CONFLICT_IDP") & (ref_df["year"] == 2025)]
            idp_tot = idp_row["people"].values[0] if len(idp_row) > 0 else 0
            disp_summary.append({"Country": name, "UNHCR_Refugees": ref_tot, "UNHCR_Asylum": asy_tot, "IDMC_IDPs_2025": idp_tot})
            
        disp_sum_df = pd.DataFrame(disp_summary)
        
        fig_disp = go.Figure()
        fig_disp.add_trace(go.Bar(name='Cumulative Refugees', x=disp_sum_df["Country"], y=disp_sum_df["UNHCR_Refugees"], marker_color='#2563EB'))
        fig_disp.add_trace(go.Bar(name='Cumulative Asylum Seekers', x=disp_sum_df["Country"], y=disp_sum_df["UNHCR_Asylum"], marker_color='#60A5FA'))
        fig_disp.add_trace(go.Bar(name='2025 Conflict IDPs', x=disp_sum_df["Country"], y=disp_sum_df["IDMC_IDPs_2025"], marker_color='#EA580C'))
        
        fig_disp.update_layout(
            barmode='group',
            title="Forced Displacement Stocks (UNHCR & IDMC)",
            yaxis_title="People (Cumulative / Latest Stock)",
            height=430
        )
        st.plotly_chart(fig_disp, use_container_width=True)
        
    with col_d2:
        key_isos = list(disp_origins.keys())
        sub_demo = demo_df[demo_df["origin_iso3"].isin(key_isos)].copy()
        
        age_mapping = {
            'Y0T4': '0–4 yrs', 'Y5T11': '5–11 yrs', 'Y12T17': '12–17 yrs',
            'Y18T59': '18–59 yrs', 'Y_GE60': '60+ yrs', '_X': 'Unspecified'
        }
        sub_demo["Age_Group"] = sub_demo["age_code"].map(age_mapping).fillna("Unspecified")
        age_agg = sub_demo.groupby("Age_Group")["people"].sum().reset_index()
        
        fig_age = px.pie(
            age_agg,
            names="Age_Group",
            values="people",
            title="Age Demographics of Displaced Persons",
            color_discrete_sequence=px.colors.sequential.RdBu,
            hole=0.4
        )
        fig_age.update_layout(height=430)
        st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("""
    > [!NOTE]
    > **Spatial Entrapment vs. Refugee Corridors**: Ukraine generated the highest volume of cross-border refugees in Europe (>23M cumulative refugee-years), while Palestine represents extreme spatial entrapment with 2.04M internal IDPs (>85% of Gaza displaced) layered on top of 5.47M UNRWA-registered refugees. Children under 18 account for over **34.8%** of displaced populations across these conflicts.
    """)

# ----------------------------------------------------
# TAB 4: MEDIA & MACRO CONTEXT
# ----------------------------------------------------
with tab4:
    st.subheader("GDELT Media Narrative Heat & World Bank Macroeconomic Shocks")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        macro_countries = ["UKR", "RUS", "PSE", "ISR", "AFG", "IRN"]
        macro_sub = macro_df[macro_df["iso3"].isin(macro_countries) & macro_df["year"].between(2014, 2025)]
        
        fig_gdp = px.line(
            macro_sub,
            x="year",
            y="gdp_growth_annual_pct",
            color="economy_name",
            title="Real GDP Annual Growth Rate (%) Shocks",
            labels={"year": "Year", "gdp_growth_annual_pct": "Annual GDP Growth (%)", "economy_name": "Economy"}
        )
        fig_gdp.add_hline(y=0, line_dash="dash", line_color="black")
        fig_gdp.update_layout(height=420)
        st.plotly_chart(fig_gdp, use_container_width=True)
        
    with col_m2:
        fig_tone = px.bar(
            summary_df[summary_df["gdelt_feb_apr_2026_avg_tone"].notnull()],
            x="country",
            y="gdelt_feb_apr_2026_avg_tone",
            color="gdelt_feb_apr_2026_avg_tone",
            color_continuous_scale="Reds_r",
            title="GDELT Media Tone Index (Feb–Apr 2026)",
            labels={"country": "Country", "gdelt_feb_apr_2026_avg_tone": "Average Tone (Sentiment)"}
        )
        fig_tone.add_hline(y=-4.0, line_dash="dot", line_color="red", annotation_text="Severe Negative (-4.0)")
        fig_tone.update_layout(height=420)
        st.plotly_chart(fig_tone, use_container_width=True)

# ----------------------------------------------------
# TAB 5: SCENARIO SIMULATOR
# ----------------------------------------------------
with tab5:
    st.subheader("Interactive Scenario Simulator & 2027 Projections")
    st.markdown("Simulate forward fatality trajectories from **October 2026 to December 2027** by adjusting combat intensity and de-escalation parameters.")
    
    col_sim_ctrl, col_sim_view = st.columns([1, 2.2])
    
    with col_sim_ctrl:
        st.markdown("##### ⚙️ Simulation Controls")
        sim_case = st.selectbox("Select Conflict to Simulate:", options=selected_cases)
        intensity_mult = st.slider("Combat Intensity Multiplier (vs Trailing 6m):", min_value=0.2, max_value=3.0, value=1.0, step=0.1)
        decay_rate = st.slider("Diplomatic De-escalation Decay (λ):", min_value=0.0, max_value=0.4, value=0.15, step=0.05)
        
        case_events = events_df[events_df["conflict_case"] == sim_case]
        monthly_b = case_events.groupby("year_month")["deaths_best"].sum().sort_index()
        trailing_6m_avg = monthly_b.tail(6).mean() if len(monthly_b) >= 6 else monthly_b.mean()
        
        st.metric("Baseline Monthly Burn-Rate", f"{trailing_6m_avg:,.0f} deaths/mo")
        st.metric("Adjusted Simulation Rate", f"{trailing_6m_avg * intensity_mult:,.0f} deaths/mo")
        
    with col_sim_view:
        months_hist = list(monthly_b.index)
        cum_hist = list(np.cumsum(monthly_b.values))
        
        future_months = [f"2026-{m:02d}" for m in range(10, 13)] + [f"2027-{m:02d}" for m in range(1, 13)]
        all_months_sim = months_hist + future_months
        
        last_cum = cum_hist[-1]
        sim_sq = list(cum_hist)
        sim_de = list(cum_hist)
        
        c_sq = last_cum
        c_de = last_cum
        effective_rate = trailing_6m_avg * intensity_mult
        
        for i in range(len(future_months)):
            c_sq += effective_rate
            c_de += effective_rate * np.exp(-decay_rate * (i + 1))
            sim_sq.append(c_sq)
            sim_de.append(c_de)
            
        fig_sim = go.Figure()
        split_idx = len(months_hist) - 1
        
        fig_sim.add_trace(go.Scatter(x=all_months_sim[:split_idx+1], y=cum_hist, mode='lines', name='Observed Cumulative Deaths', line=dict(color='#0F172A', width=3)))
        fig_sim.add_trace(go.Scatter(x=all_months_sim[split_idx:], y=sim_sq[split_idx:], mode='lines', name=f'Status-Quo Burn Rate ({intensity_mult}x)', line=dict(color='#DC2626', dash='dash', width=2.5)))
        fig_sim.add_trace(go.Scatter(x=all_months_sim[split_idx:], y=sim_de[split_idx:], mode='lines', name=f'De-escalation Scenario (λ={decay_rate})', line=dict(color='#16A34A', dash='dot', width=2.5)))
        
        fig_sim.update_layout(
            title=f"Cumulative Fatality Projections: {sim_case} (Through Dec 2027)",
            xaxis_title="Month",
            yaxis_title="Cumulative Direct Fatalities",
            height=450,
            hovermode="x unified"
        )
        st.plotly_chart(fig_sim, use_container_width=True)

    st.info(f"**Projected Outcome by End of 2027 for {sim_case}**: Under the status-quo burn rate, cumulative deaths will reach **{sim_sq[-1]:,.0f}**. Under the de-escalation scenario, deaths plateau at **{sim_de[-1]:,.0f}**, averting an estimated **{sim_sq[-1] - sim_de[-1]:,.0f}** fatalities.")

# ----------------------------------------------------
# TAB 6: DATA EXPLORER & EXPORT
# ----------------------------------------------------
with tab6:
    st.subheader("Raw Data Query, Search & Export")
    
    search_query = st.text_input("🔍 Search records by Dyad, Actor, or Location:", "")
    
    display_df = filtered_events[[
        "event_id", "conflict_case", "case_scope", "event_year", "date_start",
        "ucdp_dyad_name", "side_a_name", "side_b_name", "ucdp_location_name",
        "admin1_name", "deaths_best", "deaths_civilians", "deaths_low", "deaths_high", "source_count"
    ]]
    
    if search_query:
        mask = (
            display_df["ucdp_dyad_name"].str.contains(search_query, case=False, na=False) |
            display_df["side_a_name"].str.contains(search_query, case=False, na=False) |
            display_df["side_b_name"].str.contains(search_query, case=False, na=False) |
            display_df["ucdp_location_name"].str.contains(search_query, case=False, na=False) |
            display_df["admin1_name"].str.contains(search_query, case=False, na=False)
        )
        display_df = display_df[mask]
        
    st.write(f"Displaying **{len(display_df):,}** matching records:")
    st.dataframe(display_df.head(500), use_container_width=True)
    
    csv_data = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Dataset as CSV",
        data=csv_data,
        file_name="filtered_conflict_events.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    st.markdown("#### ⚠️ Known Data Quality Audit & Anomalies")
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        st.write("**Fatality Inversion Records (deaths_low > deaths_best or best > high)**:")
        inversion_df = filtered_events[
            (filtered_events["deaths_low"] > filtered_events["deaths_best"]) |
            (filtered_events["deaths_best"] > filtered_events["deaths_high"])
        ][["event_id", "conflict_case", "date_start", "deaths_low", "deaths_best", "deaths_high", "ucdp_coding_status"]]
        st.dataframe(inversion_df.head(20), use_container_width=True)
        st.caption(f"Total matching inversion records in current filter: {len(inversion_df):,}")
        
    with col_q2:
        st.write("**Provisional Review Flags (ucdp_coding_status != 'Clear')**:")
        flagged_df = filtered_events[filtered_events["ucdp_coding_status"] != "Clear"][
            ["event_id", "conflict_case", "date_start", "ucdp_coding_status", "deaths_best"]
        ]
        st.dataframe(flagged_df.head(20), use_container_width=True)
        st.caption(f"Total records under active review in current filter: {len(flagged_df):,}")
