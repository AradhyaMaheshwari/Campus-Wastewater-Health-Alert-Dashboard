import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from data_generator import generate_dataset, THRESHOLDS, PH_RED_LOW, PH_RED_HIGH, OUTBREAK_EVENTS, CATEGORY_ORDER, NODES_DF, MARKER_UNITS, day_to_date, build_layout_coords

st.set_page_config(layout="wide", page_title="Campus Wastewater Health Alert Dashboard", page_icon="🧪")


ALERT_COLORS = {"Green": "#2ecc71", "Yellow": "#f1c40f", "Red": "#e74c3c"}
ALERT_ORDER = ["Green", "Yellow", "Red"]

MARKER_GROUPS = {
    "Viral markers (flow-normalized)": {"columns": ["SARS_CoV_2_norm", "Influenza_A_norm", "Norovirus_norm"], "raw_columns": ["SARS_CoV_2", "Influenza_A", "Norovirus"]},
    "Bacterial pathogens": {"columns": ["E_Coli", "Salmonella", "Campylobacter"], "raw_columns": ["E_Coli", "Salmonella", "Campylobacter"]},
    "Physico-chemical": {"columns": ["pH", "Turbidity_NTU"], "raw_columns": ["pH", "Turbidity_NTU"]},
    "Antibiotic residues": {"columns": ["Antibiotic_Residues_ng_L"], "raw_columns": ["Antibiotic_Residues_ng_L"]},
    "Reported clinical cases": {"columns": ["Reported_Clinical_Cases"], "raw_columns": ["Reported_Clinical_Cases"]},
}

NICE_NAMES = {
    "SARS_CoV_2_norm": "SARS-CoV-2 (per 100kL)", "Influenza_A_norm": "Influenza A (per 100kL)",
    "Norovirus_norm": "Norovirus (per 100kL)", "SARS_CoV_2": "SARS-CoV-2 (raw)",
    "Influenza_A": "Influenza A (raw)", "Norovirus": "Norovirus (raw)",
    "E_Coli": "E. coli", "Salmonella": "Salmonella", "Campylobacter": "Campylobacter",
    "pH": "pH", "Turbidity_NTU": "Turbidity (NTU)",
    "Antibiotic_Residues_ng_L": "Antibiotic residues (ng/L)",
    "Reported_Clinical_Cases": "Reported clinical cases",
}

@st.cache_data
def load_data():
    return generate_dataset(seed=42)

@st.cache_data
def load_layout():
    return build_layout_coords()

df = load_data()
layout_coords = load_layout()

st.sidebar.title("🧪 Filters")
campus_options = ["All"] + sorted(df["Campus"].unique())
campus_filter = st.sidebar.selectbox("Campus", campus_options)
scoped = df if campus_filter == "All" else df[df["Campus"] == campus_filter]

category_options = ["All"] + sorted(scoped["Node_Category"].unique())
category_filter = st.sidebar.selectbox("Node category", category_options)
scoped = scoped if category_filter == "All" else scoped[scoped["Node_Category"] == category_filter]

location_options = ["All"] + sorted(scoped["Location_Name"].unique())
location_filter = st.sidebar.selectbox("Location", location_options)
scoped = scoped if location_filter == "All" else scoped[scoped["Location_Name"] == location_filter]

weather_options = ["All"] + sorted(scoped["Weather"].unique())
weather_filter = st.sidebar.selectbox("Weather", weather_options)
scoped = scoped if weather_filter == "All" else scoped[scoped["Weather"] == weather_filter]

min_date, max_date = df["Date"].min(), df["Date"].max()
date_range = st.sidebar.slider("Date range", min_value=pd.to_datetime(min_date).date(), max_value=pd.to_datetime(max_date).date(), value=(pd.to_datetime(min_date).date(), pd.to_datetime(max_date).date(),))
scoped_dt = pd.to_datetime(scoped["Date"])
mask = (scoped_dt.dt.date >= date_range[0]) & (scoped_dt.dt.date <= date_range[1])
filtered = scoped[mask].copy()

st.sidebar.caption(f"{filtered['Location_Name'].nunique()} site(s) · {filtered['Date'].nunique()} day(s) in view")

st.title("Campus Wastewater Health Alert Dashboard")

latest_date = filtered["Date"].max() if len(filtered) else None
latest_snapshot = filtered[filtered["Date"] == latest_date] if latest_date else filtered

red_count_latest = int((latest_snapshot["Alert_Level"] == "Red").sum())
prev_date = (pd.to_datetime(latest_date) - pd.Timedelta(days=1)).strftime("%Y-%m-%d") if latest_date else None
prev_snapshot = df[df["Date"] == prev_date] if prev_date else pd.DataFrame(columns=df.columns)
red_count_prev = int((prev_snapshot["Alert_Level"] == "Red").sum())
red_diff = red_count_latest - red_count_prev

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Sites monitored", filtered["Location_Name"].nunique())
k2.metric("Latest snapshot date", latest_date or "—")
k3.metric("🔴 Red sites (latest)", red_count_latest, f"{red_diff} from yesterday", delta_color="inverse")
k4.metric("🟡 Yellow sites (latest)", int((latest_snapshot["Alert_Level"] == "Yellow").sum()))
k5.metric("Avg Health Score", int(latest_snapshot["Health_Score"].mean()) if not latest_snapshot.empty else 0)

st.divider()

st.subheader("🤖 Daily AI Analytics & Summary")
if len(latest_snapshot) > 0:
    sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
    
    alert_counts = latest_snapshot["Alert_Level"].value_counts()
    labels = alert_counts.index.tolist()
    values = alert_counts.values.tolist()
    
    pie_fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=[ALERT_COLORS.get(c, "#888888") for c in labels]),
        textinfo="percent",
        textfont=dict(color="white"),
        hoverinfo="label+value"
    ))
    pie_fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        height=220,
        showlegend=False,
        title=dict(text="Alert Distribution", font=dict(size=14, color="gray"), x=0.5, xanchor="center"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    sum_col1.plotly_chart(pie_fig, use_container_width=True)
    
    avg_health = latest_snapshot["Health_Score"].mean()
    gauge_health = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg_health,
        title=dict(text="Avg Health Score", font=dict(size=14, color="gray")),
        number=dict(font=dict(color="white")),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="white"),
            bar=dict(color="rgba(0,0,0,0)"),  # Makes the thick progress bar completely transparent
            bgcolor="rgba(255,255,255,0.05)",
            borderwidth=0,
            steps=[
                dict(range=[0, 40], color="#e74c3c"),  # Red
                dict(range=[40, 70], color="#f1c40f"), # Yellow
                dict(range=[70, 100], color="#2ecc71") # Green
            ],
            threshold=dict(
                line=dict(color="white", width=4),
                thickness=1,
                value=avg_health
            )
        )
    ))
    gauge_health.update_layout(margin=dict(l=20, r=20, t=50, b=10), height=220, paper_bgcolor="rgba(0,0,0,0)")
    sum_col2.plotly_chart(gauge_health, use_container_width=True)
    
    total_sites = len(latest_snapshot)
    risk_pct = (red_count_latest / total_sites * 100) if total_sites > 0 else 0
    gauge_risk = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_pct,
        number=dict(suffix="%", font=dict(color="white")),
        title=dict(text="Critical Sites Load", font=dict(size=14, color="gray")),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="white"),
            bar=dict(color="rgba(0,0,0,0)"),  # Makes the thick progress bar completely transparent
            bgcolor="rgba(255,255,255,0.05)",
            borderwidth=0,
            steps=[
                dict(range=[0, 15], color="#2ecc71"),  # Green (low critical load is good)
                dict(range=[15, 40], color="#f1c40f"), # Yellow
                dict(range=[40, 100], color="#e74c3c") # Red (high critical load is bad)
            ],
            threshold=dict(
                line=dict(color="white", width=4),
                thickness=1,
                value=risk_pct
            )
        )
    ))
    gauge_risk.update_layout(margin=dict(l=20, r=20, t=50, b=10), height=220, paper_bgcolor="rgba(0,0,0,0)")
    sum_col3.plotly_chart(gauge_risk, use_container_width=True)
    
    highest_risk_site = latest_snapshot.loc[latest_snapshot["Health_Score"].idxmin()]
    sum_col4.markdown(f"""
    <div style="background-color: rgba(128, 128, 128, 0.05); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 8px; padding: 20px; height: 210px; display: flex; flex-direction: column; justify-content: center;">
        <div style="font-size: 14px; font-weight: bold; color: gray; text-align: center; margin-bottom: 5px;">Highest Risk Site</div>
        <div style="font-size: 52px; font-weight: bold; color: #e74c3c; text-align: center; line-height: 1;">{highest_risk_site['Health_Score']}</div>
        <div style="font-size: 15px; font-weight: bold; text-align: center; margin-top: 5px;">{highest_risk_site['Location_Name']}</div>
        <div style="font-size: 12px; text-align: center; margin-top: 10px; opacity: 0.8;">{highest_risk_site['Reason']}</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No data available for the current selection.")

st.divider()

tab_map, tab_trends, tab_alerts, tab_forecast, tab_response, tab_ethics, tab_data = st.tabs(
    ["🗺️ Animated Map", "📈 Trend Explorer", "🚨 Alert Log", "🔮 Forecast", "📋 Response Plan",
     "🔒 Privacy & Ethics", "📁 Data & Download"]
)

with tab_map:
    st.subheader("Animated Campus Map")
    available_dates = filtered["Date"].unique().tolist()
    available_dates.sort()
    if len(available_dates) > 0:
        fig = go.Figure()
        frames = []
        for d in available_dates:
            snapshot = df[df["Date"] == d]
            if campus_filter != "All":
                snapshot = snapshot[snapshot["Campus"] == campus_filter]
            if category_filter != "All":
                snapshot = snapshot[snapshot["Node_Category"] == category_filter]
            xs = []
            ys = []
            colors = []
            texts = []
            hovers = []
            for _, row in snapshot.iterrows():
                key = (row["Campus"], row["Node_Category"], row["Location_Name"])
                if key not in layout_coords:
                    continue
                x, y = layout_coords[key]
                xs.append(x)
                ys.append(y)
                colors.append(ALERT_COLORS[row["Alert_Level"]])
                texts.append(row["Location_Name"])
                hovers.append(
                    f"<b>{row['Location_Name']}</b><br>Weather: {row['Weather_Icon']}<br>"
                    f"Alert: {row['Alert_Level']}"
                )
            frames.append(go.Frame(
                data=[go.Scatter(
                    x=xs, y=ys, mode="markers+text", text=texts, textposition="top center",
                    textfont=dict(size=11),
                    marker=dict(size=32, color=colors, line=dict(width=2, color="#333333")),
                    hovertext=hovers, hoverinfo="text"
                )],
                name=d
            ))
        
        fig.add_trace(frames[0].data[0])
        
        annotations = []
        for campus, offset in [("NORTH CAMPUS", 0), ("SOUTH CAMPUS", 8)]:
            annotations.append(dict(x=0, y=offset + 1.5, text=f"<b>{campus}</b>", showarrow=False, font=dict(size=15)))
            for row_i, cat in enumerate(CATEGORY_ORDER):
                annotations.append(dict(x=-17, y=offset - (row_i * 1.5), text=cat, showarrow=False, font=dict(size=11), xanchor="right"))
                
        fig.update_layout(
            height=850, showlegend=False,
            xaxis=dict(visible=True, showgrid=False, zeroline=False, showticklabels=False, showline=True, linewidth=2, linecolor="gray", mirror=True, range=[-19, 19]),
            yaxis=dict(visible=True, showgrid=False, zeroline=False, showticklabels=False, showline=True, linewidth=2, linecolor="gray", mirror=True, range=[-6, 10.5]),
            margin=dict(l=110, r=20, t=20, b=80),
            annotations=annotations,
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                y=-0.1,
                x=0.0,
                xanchor="left",
                yanchor="top",
                font=dict(color="red"),
                bordercolor="red",
                buttons=[dict(
                    label="▶ Play",
                    method="animate",
                    args=[None, dict(frame=dict(duration=300, redraw=True), fromcurrent=True, transition=dict(duration=0))]
                ), dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]
                )]
            )],
            sliders=[dict(
                active=0,
                yanchor="top",
                xanchor="left",
                currentvalue=dict(font=dict(size=16), prefix="Date: ", visible=True, xanchor="right"),
                transition=dict(duration=0),
                pad=dict(b=10, t=50),
                len=0.9,
                x=0.1,
                y=-0.1,
                activebgcolor="red",
                steps=[dict(
                    args=[[d], dict(frame=dict(duration=0, redraw=True), mode="immediate", transition=dict(duration=0))],
                    label=d,
                    method="animate"
                ) for d in available_dates]
            )]
        )
        
        fig.frames = frames
        st.plotly_chart(fig, use_container_width=True)
        
with tab_trends:
    st.subheader("Trend explorer & History")
    default_location = "Beas Kund" if "Beas Kund" in scoped["Location_Name"].unique() else sorted(scoped["Location_Name"].unique())[0]
    all_locations = sorted(scoped["Location_Name"].unique())
    trend_location = st.selectbox("Site", all_locations, index=all_locations.index(default_location) if default_location in all_locations else 0)
    
    all_markers_flat = []
    for v in MARKER_GROUPS.values():
        all_markers_flat.extend(v["columns"])
        
    selected_markers = st.multiselect("Select Markers to Compare", all_markers_flat, default=[MARKER_GROUPS["Viral markers (flow-normalized)"]["columns"][0]])
    
    site_events = [e for e in OUTBREAK_EVENTS if e["location"] == trend_location]
    site_df = df[df["Location_Name"] == trend_location].copy()
    site_df["Date_dt"] = pd.to_datetime(site_df["Date"])
    
    fig1 = go.Figure()
    colors_seq = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33", "#a65628", "#f781bf"]
    for idx, col in enumerate(selected_markers):
        fig1.add_trace(go.Scatter(x=site_df["Date_dt"], y=site_df[col], mode="lines+markers", name=NICE_NAMES.get(col, col), line=dict(color=colors_seq[idx % len(colors_seq)])))
        
    for ev in site_events:
        fig1.add_vrect(x0=day_to_date(ev["start_day"]), x1=day_to_date(ev["end_day"]), fillcolor="red", opacity=0.1, line_width=0)
        
    fig1.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10), title=f"Historical Timeline — {trend_location}", legend=dict(orientation="h", y=1.15), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig1, use_container_width=True)

with tab_alerts:
    st.subheader("Alert log & Anomaly Scores")
    red_alerts = filtered[filtered["Alert_Level"] == "Red"].sort_values("Date", ascending=False)
    yellow_alerts = filtered[filtered["Alert_Level"] == "Yellow"].sort_values("Date", ascending=False)
    show_cols = ["Date", "Campus", "Location_Name", "Alert_Level", "Health_Score", "Reason", "Recommendation", "Confidence_Score"]
    
    c1, c2 = st.columns(2)
    c1.error(f"🔴 Red alerts: {len(red_alerts)}")
    c1.dataframe(red_alerts[show_cols], use_container_width=True, height=320)
    c2.warning(f"🟡 Yellow alerts: {len(yellow_alerts)}")
    c2.dataframe(yellow_alerts[show_cols], use_container_width=True, height=320)

    
with tab_forecast:
    st.subheader("7-Day Forecast")
    forecast_loc = st.selectbox("Select Location for Forecast", all_locations)
    loc_df = df[df["Location_Name"] == forecast_loc].copy()
    loc_df["Date_dt"] = pd.to_datetime(loc_df["Date"])
    last_date = loc_df["Date_dt"].max()
    last_val = loc_df["Norovirus_norm"].iloc[-1]
    trend_diff = loc_df["Norovirus_norm"].iloc[-1] - loc_df["Norovirus_norm"].iloc[-7] if len(loc_df) >= 7 else 0
    
    future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 8)]
    future_vals = [max(0, last_val + (trend_diff/7)*i) for i in range(1, 8)]
    prob_outbreak = min(100, max(0, int((future_vals[-1] / 150) * 100)))
    
    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(x=loc_df["Date_dt"], y=loc_df["Norovirus_norm"], mode="lines", name="Historical Norovirus"))
    fig_forecast.add_trace(go.Scatter(x=future_dates, y=future_vals, mode="lines+markers", line=dict(dash="dash", color="orange"), name="Forecast"))
    fig_forecast.update_layout(height=400, title=f"Forecast for {forecast_loc} (Probability of Outbreak: {prob_outbreak}%)", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_forecast, use_container_width=True)

with tab_response:
    st.subheader("Public-Health Response Matrix")
    
    st.markdown("""
    <style>
    .response-box {
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 6px solid;
        background-color: rgba(128, 128, 128, 0.05);
    }
    .box-green { border-color: #2ecc71; }
    .box-yellow { border-color: #f1c40f; }
    .box-red { border-color: #e74c3c; }
    .response-box h3 {
        margin-top: 0;
        margin-bottom: 15px;
        font-size: 20px;
    }
    .action-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
    }
    .action-col {
        padding: 10px;
        background-color: rgba(0, 0, 0, 0.1);
        border-radius: 6px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="response-box box-green">
        <h3>🟢 Green Alert (Routine Baseline)</h3>
        <p><b>Trigger Condition:</b> All monitored biomarkers remain within historical seasonal baselines and acceptable ranges.</p>
        <div class="action-grid">
            <div class="action-col">
                <b>Immediate Action (0-24h)</b><br>
                • Execute standard routine sampling schedule.<br>
                • Clean and calibrate auto-samplers.
            </div>
            <div class="action-col">
                <b>Communication Protocol</b><br>
                • Log data into the central internal dashboard.<br>
                • No public notification required.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="response-box box-yellow">
        <h3>🟡 Yellow Alert (Elevated Risk / Early Warning)</h3>
        <p><b>Trigger Condition:</b> One or more markers breach the early-warning threshold, indicating potential viral shedding or minor sanitation issues.</p>
        <div class="action-grid">
            <div class="action-col">
                <b>Immediate Action (0-24h)</b><br>
                • Increase sampling frequency to daily at the flagged site.<br>
                • Utilize the 7-day forecast system to predict potential outbreak peaks.<br>
                • Dispatch facility management to inspect local sewage lines for blockages.
            </div>
            <div class="action-col">
                <b>Communication Protocol</b><br>
                • Notify campus health center internally.<br>
                • Alert hostel wardens to monitor for symptomatic students.<br>
                • Maintain public anonymity to avoid panic.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="response-box box-red">
        <h3>🔴 Red Alert (Critical Contamination / Outbreak)</h3>
        <p><b>Trigger Condition:</b> Pathogen loads or chemical markers exceed critical thresholds, or multiple yellow markers cluster geographically.</p>
        <div class="action-grid">
            <div class="action-col">
                <b>Immediate Action (0-24h)</b><br>
                • Mandate immediate re-sampling to eliminate laboratory error.<br>
                • Immediately initiate daily sampling for all neighboring campus buildings to track spatial spread.<br>
                • Deploy point-of-use clinical testing to the affected zone.<br>
                • Initiate targeted building lockdown protocols and deep sanitation (only if corroborated by clinical cases).
            </div>
            <div class="action-col">
                <b>Communication Protocol</b><br>
                • Issue targeted health advisory to the specific building residents.<br>
                • Escalate to municipal public health authorities.<br>
                • Restrict access to affected mess halls or academic blocks.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Escalation Workflow")
    
    col1, col2, col3 = st.columns(3)
    col1.info("**Step 1: Signal Detection**\nWastewater anomaly detected by the AI dashboard.")
    col2.warning("**Step 2: Verification**\nMandatory re-sampling and execution of AI forecast models.")
    col3.error("**Step 3: Intervention**\nTargeted lockdown, clinical testing, and public advisories.")


with tab_ethics:
    st.subheader("Privacy and ethics")
    
    st.markdown("""
    <style>
    .ethics-card {
        background-color: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        display: flex;
        align-items: flex-start;
        gap: 15px;
    }
    .ethics-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: rgba(128, 128, 128, 0.4);
    }
    .ethics-icon {
        font-size: 24px;
        line-height: 1;
    }
    .ethics-content h4 {
        margin: 0 0 8px 0;
        font-size: 16px;
    }
    .ethics-content p {
        margin: 0;
        font-size: 14px;
        line-height: 1.5;
        opacity: 0.9;
    }
    </style>
    """, unsafe_allow_html=True)

    ethics_points = [
        {
            "icon": "🏢", 
            "title": "Data collection & anonymity model", 
            "text": "No individual is tested or named — the smallest unit is a sampling site (hostel/mess/building). A minimum viable catchment size is established below which data is not disaggregated. Structurally small or gender-linked sites are treated with extra caution to prevent re-identification."
        },
        {
            "icon": "✅", 
            "title": "Consent", 
            "text": "WBE is a passive, population-level surveillance method. Community-level notice replaces individual consent: the campus community is told the system exists, what it monitors, and what it does not do, matching standard real-world WBE deployments."
        },
        {
            "icon": "🎯", 
            "title": "Purpose limitation (no function creep)", 
            "text": "The system exists only to detect outbreaks and sanitation failures. Expanding the marker list requires separate ethical review. Secondary uses like disciplinary action, risk scoring, or sharing with non-health bodies are strictly prohibited."
        },
        {
            "icon": "🔐", 
            "title": "Data governance & access control", 
            "text": "Raw site-level data is restricted to the health center, while wider admin sees aggregated dashboards. Data follows a strict retention period and is never linked to other identifiable campus datasets (like health records or ID swipes). Storage is encrypted with role-based access."
        },
        {
            "icon": "📢", 
            "title": "Group harm and stigma", 
            "text": "A Red alert tied to one hostel can cause social stigma. Alerts route to the health center internally first. Any public-facing communication is reviewed and described in general terms rather than immediately naming specific residences."
        },
        {
            "icon": "⚖️", 
            "title": "Handling uncertainty / false positives honestly", 
            "text": "Re-sampling is mandated before escalating a Red alert to wide communication to rule out sensor or lab errors. Signals are communicated as possible early warnings being verified, not as confirmed outbreaks."
        },
        {
            "icon": "🤝", 
            "title": "Equity", 
            "text": "Monitoring frequency and response quality are standard across all hostels. No specific blocks (e.g., international student housing or lower-resourced hostels) are surveilled more intensely or responded to more slowly without explicit justification."
        },
        {
            "icon": "🚦", 
            "title": "Proportionate response", 
            "text": "Response severity is explicitly tied to the alert level. A Yellow alert will not trigger the same disruptive action as a Red one, and no alert alone justifies a lockdown without clinical corroboration."
        },
        {
            "icon": "👁️‍🗨️", 
            "title": "Oversight & accountability", 
            "text": "An oversight group including the health center, a student representative, and a data policy lead periodically reviews system usage. Residents are provided a direct channel to ask questions or raise concerns."
        },
        {
            "icon": "📜", 
            "title": "Legal/regulatory alignment", 
            "text": "The dataset and monitoring framework are designed to align with India's Digital Personal Data Protection Act, 2023, and institutional data-protection policies, ensuring a legally compliant deployment."
        }
    ]

    for point in ethics_points:
        st.markdown(f"""
        <div class="ethics-card">
            <div class="ethics-icon">{point['icon']}</div>
            <div class="ethics-content">
                <h4>{point['title']}</h4>
                <p>{point['text']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)


with tab_data:
    st.subheader("Data Export")
    st.dataframe(filtered.drop(columns=["day_counter"]), use_container_width=True, height=420)
    report_text = f"Campus Wastewater Health Alert Dashboard Report\nGenerated on {latest_date}\n\nTotal Sites Monitored: {filtered['Location_Name'].nunique()}\nRed Alerts Today: {red_count_latest}\n\nHighest Risk Summary:\n{highest_risk_site['Location_Name']} - Score {highest_risk_site['Health_Score']}\nRecommendation: {highest_risk_site['Recommendation']}\nReason: {highest_risk_site['Reason']}"
    
    dl1, dl2, dl3 = st.columns(3)
    dl1.download_button("Download CSV", data=filtered.drop(columns=["day_counter"]).to_csv(index=False).encode("utf-8"), file_name="wastewater_filtered.csv", mime="text/csv")
    dl2.download_button("Download Full CSV", data=df.drop(columns=["day_counter"]).to_csv(index=False).encode("utf-8"), file_name="synthetic_dataset.csv", mime="text/csv")
    dl3.download_button("Download PDF/Report (TXT)", data=report_text.encode("utf-8"), file_name="daily_report.txt", mime="text/plain")