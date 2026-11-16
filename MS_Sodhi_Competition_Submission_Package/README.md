# Comparative Conflict Analytics & AI Simulation Portal
### MS Sodhi Medal Competition • Official Datathon Submission

An end-to-end empirical data science, simulation, and interactive analytics portal evaluating conflict severity, civilian vulnerability, forced displacement, and macroeconomic disruption across four major geopolitical theaters:
1. **Russia–Ukraine** (Conventional High-Intensity Mechanized Attrition)
2. **Israel–Hamas** (Asymmetric Urban Siege & Spatial Entrapment)
3. **Afghanistan–Pakistan** (Sub-National Non-State Insurgent Clashes)
4. **US–Iran** (Multi-Theater Asymmetric Standoff across 13 Sovereign Nations)

---

## 📁 Package Contents

```
├── MS_Sodhi_Jury_Presentation.pptx   # 18-Slide Executive Widescreen Deck with full Speaker Notes
├── Final_Analysis_Report.md          # 34 KB Comprehensive Research Report (AQ1–AQ5 & 10 Limitations)
├── Jury_Presentation_Report.md       # Jury Deck Companion, Script, and Q&A Defense Strategy
├── app.py                            # Interactive Streamlit Web Portal with NLP AI Query Engine
├── requirements.txt                  # Python dependencies
├── outputs/
│   ├── charts/                       # 7 Publication-grade high-res analytical figures
│   │   ├── q1_conflict_lethality_civilian_ratio.png
│   │   ├── q2_temporal_fatalities_timeline.png
│   │   ├── q3_displacement_demographics.png
│   │   ├── q4_media_vs_kinetic_macro.png
│   │   ├── q5_conflict_profile_radar.png
│   │   ├── q6_fatality_velocity_simulation.png
│   │   └── q7_geographic_dispersion.png
│   └── screenshots/annotated/        # 8 High-resolution annotated scenario captures
│       ├── scenario_01_russia_ukraine_attrition.png
│       ├── scenario_02_israel_hamas_urban_siege.png
│       ├── scenario_03_afghanistan_pakistan_insurgency.png
│       ├── scenario_04_us_iran_multi_theater_radar.png
│       ├── scenario_05_mass_casualty_major_battles.png
│       ├── scenario_06_ai_analyst_refugees_vs_idps.png
│       ├── scenario_07_ai_analyst_macro_gdp_inflation.png
│       └── scenario_08_forward_simulation_2027.png
└── for participants/data/             # Core micro-event, displacement, demographic & macro data
```

---

## 🚀 How to Run the Interactive Dashboard

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the Portal**:
   ```bash
   streamlit run app.py
   ```
   The dashboard will automatically open in your browser at `http://localhost:8501`.

3. **Key Features**:
   - **Ask AI Data Analyst**: Type any query in plain English (e.g. *"Compare civilian casualties in Gaza vs Ukraine"* or *"Show GDP contraction and inflation"*).
   - **Executive Overview**: High-level KPI cards and multi-dimensional radar comparison.
   - **Lethality & Timeline**: Longitudinal monthly casualty curves and combatant vs. civilian breakdown.
   - **Forced Displacement**: Cross-border UNHCR refugees vs. internal IDPs.
   - **Media & Macro Context**: GDP shocks vs. persistent inflation.
   - **Scenario Simulator**: Forward casualty projections through Dec 2027 under status-quo vs. diplomatic de-escalation.
   - **Data Explorer & Export**: Filtered data table with CSV export.

---

## 🎯 Official Scorecard Alignment (13 Criteria)

| Criteria Group | Focus Areas | Covered In |
|:---|:---|:---|
| **I. Problem Understanding & Prep** | Framing, RFC 4180 parsing, bound clamping, CVR feature engineering | Slides 2–5, Section 1 |
| **II. Analysis & Insights** | AQ1–AQ5, Civilian Vulnerability Ratio, demographic entrapment | Slides 6–11, Section 2 |
| **III. Model Performance** | Dual-regime model, backtesting on withheld 2024–2026 data ($R^2=0.884$) | Slides 12–13, Section 3 |
| **IV. Innovation & Tools** | Streamlit 7-tab portal, Natural Language Query parser, Plotly widgets | Slides 14–15, `app.py` |
| **V. Quality & Defense** | 10 dataset limitations, policy directives, reproducibility, Q&A defense | Slides 16–18, Section 4 |
