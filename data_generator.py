import numpy as np
import pandas as pd

CAMPUS_NODES_RAW = [
    "NORTH CAMPUS,Academic,A9",
    "NORTH CAMPUS,Academic,A10",
    "NORTH CAMPUS,Academic,A11",
    "NORTH CAMPUS,Academic,A13",
    "NORTH CAMPUS,Academic,A14",
    "NORTH CAMPUS,Academic,A17",
    "NORTH CAMPUS,Academic,A18",
    "NORTH CAMPUS,Academic,Library",
    "NORTH CAMPUS,Academic,Auditorium",
    "NORTH CAMPUS,Academic,Health Centre",
    "NORTH CAMPUS,Academic,Sports Complex",
    "NORTH CAMPUS,Mess,Pine Mess",
    "NORTH CAMPUS,Mess,Peepal Mess",
    "NORTH CAMPUS,Mess,Yoga Mess",
    "NORTH CAMPUS,Mess,Alder Mess",
    "NORTH CAMPUS,Mess,Oak Mess",
    "NORTH CAMPUS,Boys Hostel,Beas Kund",
    "NORTH CAMPUS,Boys Hostel,Dashir",
    "NORTH CAMPUS,Boys Hostel,Surajtaal",
    "NORTH CAMPUS,Boys Hostel,Suvalsar",
    "NORTH CAMPUS,Girls Hostel,Gaurikund",
    "SOUTH CAMPUS,Academic,A1",
    "SOUTH CAMPUS,Academic,A2",
    "SOUTH CAMPUS,Academic,A3",
    "SOUTH CAMPUS,Academic,A4",
    "SOUTH CAMPUS,Academic,A5",
    "SOUTH CAMPUS,Academic,Library",
    "SOUTH CAMPUS,Mess,Cedar Mess",
    "SOUTH CAMPUS,Mess,Maple Mess",
    "SOUTH CAMPUS,Mess,Gulmohar Mess",
    "SOUTH CAMPUS,Boys Hostel,Mani Mahesh",
    "SOUTH CAMPUS,Boys Hostel,Nako",
    "SOUTH CAMPUS,Boys Hostel,Prashar",
    "SOUTH CAMPUS,Girls Hostel,Chandrataal",
    "SOUTH CAMPUS,Girls Hostel,Renuka",
]

CATEGORY_ORDER = ["Academic", "Mess", "Boys Hostel", "Girls Hostel"]

def _parse_nodes():
    rows = []
    for entry in CAMPUS_NODES_RAW:
        campus, category, location = entry.split(",")
        rows.append({"Campus": campus, "Node_Category": category, "Location_Name": location})
    return pd.DataFrame(rows)

NODES_DF = _parse_nodes()

START_DATE = "2026-08-01"
END_DATE = "2026-10-31"

THRESHOLDS = {
    "SARS_CoV_2_norm":          {"yellow": 50,  "red": 150,  "label": "SARS-CoV-2 (per 100kL flow)"},
    "Influenza_A_norm":         {"yellow": 75,  "red": 200,  "label": "Influenza A (per 100kL flow)"},
    "Norovirus_norm":           {"yellow": 50,  "red": 150,  "label": "Norovirus (per 100kL flow)"},
    "E_Coli":                   {"yellow": 500, "red": 2500, "label": "E. coli (MPN/100mL)"},
    "Salmonella":                {"yellow": 100, "red": 500,  "label": "Salmonella (MPN/100mL)"},
    "Campylobacter":             {"yellow": None, "red": None, "label": "Campylobacter (MPN/100mL)"},
    "Turbidity_NTU":             {"yellow": 20,  "red": 50,   "label": "Turbidity (NTU)"},
    "Antibiotic_Residues_ng_L":  {"yellow": 300, "red": 1000, "label": "Antibiotic residues (ng/L)"},
}

PH_RED_LOW, PH_RED_HIGH = 5.5, 9.0

MARKER_UNITS = {
    "SARS_CoV_2": "copies/mL (raw)", "Influenza_A": "copies/mL (raw)", "Norovirus": "copies/mL (raw)",
    "E_Coli": "MPN/100mL", "Salmonella": "MPN/100mL", "Campylobacter": "MPN/100mL",
    "pH": "pH units", "Turbidity_NTU": "NTU", "Antibiotic_Residues_ng_L": "ng/L",
    "Reported_Clinical_Cases": "cases/day",
}

OUTBREAK_EVENTS = [
    {
        "location": "Beas Kund", "campus": "NORTH CAMPUS",
        "type": "Bell-shaped outbreak", "start_day": 50, "end_day": 92,
        "markers": ["Norovirus", "Reported_Clinical_Cases", "Antibiotic_Residues_ng_L"],
        "description": "Bell-shaped norovirus outbreak in a boys' hostel with neighbor spread.",
    },
    {
        "location": "Chandrataal", "campus": "SOUTH CAMPUS",
        "type": "Bell-shaped outbreak", "start_day": 70, "end_day": 92,
        "markers": ["Influenza_A", "Reported_Clinical_Cases"],
        "description": "Bell-shaped influenza outbreak in a girls' hostel with neighbor spread.",
    },
    {
        "location": "Cedar Mess", "campus": "SOUTH CAMPUS",
        "type": "Acute contamination spike", "start_day": 20, "end_day": 22,
        "markers": ["E_Coli", "Salmonella", "Campylobacter", "Turbidity_NTU"],
        "description": "A 3-day acute sewage/contamination spike.",
    },
    {
        "location": "A1", "campus": "SOUTH CAMPUS",
        "type": "Single-day chemical incident", "start_day": 80, "end_day": 80,
        "markers": ["pH", "Turbidity_NTU"],
        "description": "A one-day chemical spill.",
    },
]

def day_to_date(day_counter):
    return (pd.Timestamp(START_DATE) + pd.Timedelta(days=day_counter - 1)).strftime("%Y-%m-%d")

def generate_dataset(seed=42):
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    df = NODES_DF.merge(pd.DataFrame({"Date": dates}), how="cross")
    df = df.sort_values(["Date", "Campus", "Node_Category", "Location_Name"]).reset_index(drop=True)

    unique_dates = sorted(df["Date"].unique())
    date_to_day = {d: i + 1 for i, d in enumerate(unique_dates)}
    df["day_counter"] = df["Date"].map(date_to_day)

    n = len(df)
    rng = np.random.default_rng(seed)

    weather_choices = ["Sunny", "Cloudy", "Rain"]
    weather_icons = {"Sunny": "☀️", "Cloudy": "☁️", "Rain": "🌧️"}
    daily_weather = rng.choice(weather_choices, size=len(unique_dates), p=[0.6, 0.3, 0.1])
    date_to_weather = {d: w for d, w in zip(unique_dates, daily_weather)}
    df["Weather"] = df["Date"].map(date_to_weather)
    df["Weather_Icon"] = df["Weather"].map(weather_icons)

    is_weekend = df["Date"].dt.dayofweek >= 5
    is_academic = df["Node_Category"] == "Academic"
    occupancy = np.select([is_weekend & is_academic, is_weekend & ~is_academic], [0.2, 1.3], default=1.0)
    
    season = 1 + 0.08 * np.sin(2 * np.pi * df["day_counter"] / 30)
    base_mult = occupancy * season

    df["Flow_Rate_kL"] = np.maximum(10.0, 100.0 * base_mult + rng.normal(0, 15, n))
    df["SARS_CoV_2"] = np.maximum(2.0, 15.0 * base_mult + rng.normal(0, 3, n))
    df["Influenza_A"] = np.maximum(2.0, 20.0 * base_mult + rng.normal(0, 4, n))
    df["Norovirus"] = np.maximum(2.0, 10.0 * base_mult + rng.normal(0, 2, n))
    df["E_Coli"] = np.maximum(10.0, 200.0 * base_mult + rng.normal(1.5, 0.4, n) * 10.0)
    df["Salmonella"] = np.maximum(0.0, 15.0 * base_mult + rng.normal(0, 5, n))
    df["Campylobacter"] = np.maximum(0.0, 10.0 * base_mult + rng.normal(0, 3, n))
    df["pH"] = np.clip(7.2 + rng.normal(0, 0.25, n), 0.0, 14.0)
    df["Turbidity_NTU"] = np.maximum(1.0, 5.0 * base_mult + rng.normal(0, 2, n))
    df["Antibiotic_Residues_ng_L"] = np.maximum(0.0, 50.0 * base_mult + rng.normal(0, 10, n))
    df["Reported_Clinical_Cases"] = 0.0

    rain_mask = df["Weather"] == "Rain"
    df.loc[rain_mask, "Flow_Rate_kL"] *= 1.5
    df.loc[rain_mask, "Turbidity_NTU"] *= 1.8
    df.loc[rain_mask, "SARS_CoV_2"] *= 0.85
    df.loc[rain_mask, "Influenza_A"] *= 0.85
    df.loc[rain_mask, "Norovirus"] *= 0.85

    def apply_bell_curve(loc_mask, start, end, peak, peak_val, std, col):
        c = loc_mask & (df["day_counter"] >= start) & (df["day_counter"] <= end)
        df.loc[c, col] += np.exp(-0.5 * ((df.loc[c, "day_counter"] - peak) / std) ** 2) * peak_val

    m_beas = df["Location_Name"] == "Beas Kund"
    apply_bell_curve(m_beas, 50, 92, 70, 900.0, 10.0, "Norovirus")
    apply_bell_curve(m_beas, 53, 92, 73, 20.0, 10.0, "Reported_Clinical_Cases")
    apply_bell_curve(m_beas, 55, 92, 75, 700.0, 10.0, "Antibiotic_Residues_ng_L")

    for neighbor in ["Dashir", "Suvalsar", "Surajtaal"]:
        m_neigh = df["Location_Name"] == neighbor
        apply_bell_curve(m_neigh, 50, 92, 70, 900.0 * 0.3, 10.0, "Norovirus")

    m_chandra = df["Location_Name"] == "Chandrataal"
    apply_bell_curve(m_chandra, 70, 92, 80, 500.0, 8.0, "Influenza_A")
    apply_bell_curve(m_chandra, 75, 92, 85, 12.0, 8.0, "Reported_Clinical_Cases")

    m_renuka = df["Location_Name"] == "Renuka"
    apply_bell_curve(m_renuka, 70, 92, 80, 500.0 * 0.3, 8.0, "Influenza_A")

    m_cedar = df["Location_Name"] == "Cedar Mess"
    df.loc[m_cedar & (df["day_counter"] == 20), ["E_Coli", "Salmonella", "Turbidity_NTU"]] += [1800.0, 400.0, 25.0]
    df.loc[m_cedar & (df["day_counter"] == 21), ["E_Coli", "Salmonella", "Campylobacter", "Turbidity_NTU"]] += [3500.0, 850.0, 300.0, 60.0]
    df.loc[m_cedar & (df["day_counter"] == 22), ["E_Coli", "Salmonella", "Turbidity_NTU"]] += [1200.0, 200.0, 15.0]

    m_a1 = df["Location_Name"] == "A1"
    df.loc[m_a1 & (df["day_counter"] == 80), "pH"] = 4.8
    df.loc[m_a1 & (df["day_counter"] == 80), "Turbidity_NTU"] = 45.0

    df["Salmonella"] += df["E_Coli"] * 0.05
    df["Campylobacter"] += df["Salmonella"] * 0.05
    df["Reported_Clinical_Cases"] += df["Norovirus"] * 0.01
    df["Antibiotic_Residues_ng_L"] += df["Reported_Clinical_Cases"] * 5.0

    marker_cols = ["Flow_Rate_kL", "SARS_CoV_2", "Influenza_A", "Norovirus", "E_Coli", "Salmonella", "Campylobacter", "pH", "Turbidity_NTU", "Antibiotic_Residues_ng_L"]
    noise_matrix = rng.uniform(0.97, 1.03, size=(n, len(marker_cols)))
    df[marker_cols] = df[marker_cols].values * noise_matrix

    missing_mask = rng.random(size=(n, len(marker_cols))) < 0.015
    df_vals = df[marker_cols].values
    df_vals[missing_mask] = np.nan
    df[marker_cols] = df_vals

    df["Reported_Clinical_Cases"] = df["Reported_Clinical_Cases"].fillna(0).round().astype(int)

    df["SARS_CoV_2_norm"] = df["SARS_CoV_2"] * 100.0 / df["Flow_Rate_kL"]
    df["Influenza_A_norm"] = df["Influenza_A"] * 100.0 / df["Flow_Rate_kL"]
    df["Norovirus_norm"] = df["Norovirus"] * 100.0 / df["Flow_Rate_kL"]

    red = (
        (df["SARS_CoV_2_norm"] > THRESHOLDS["SARS_CoV_2_norm"]["red"]) |
        (df["Influenza_A_norm"] > THRESHOLDS["Influenza_A_norm"]["red"]) |
        (df["Norovirus_norm"] > THRESHOLDS["Norovirus_norm"]["red"]) |
        (df["E_Coli"] > THRESHOLDS["E_Coli"]["red"]) |
        (df["Salmonella"] > THRESHOLDS["Salmonella"]["red"]) |
        (df["pH"] < PH_RED_LOW) | (df["pH"] > PH_RED_HIGH) |
        (df["Turbidity_NTU"] > THRESHOLDS["Turbidity_NTU"]["red"]) |
        (df["Antibiotic_Residues_ng_L"] > THRESHOLDS["Antibiotic_Residues_ng_L"]["red"])
    )
    yellow = (
        (df["SARS_CoV_2_norm"] > THRESHOLDS["SARS_CoV_2_norm"]["yellow"]) |
        (df["Influenza_A_norm"] > THRESHOLDS["Influenza_A_norm"]["yellow"]) |
        (df["Norovirus_norm"] > THRESHOLDS["Norovirus_norm"]["yellow"]) |
        (df["E_Coli"] > THRESHOLDS["E_Coli"]["yellow"]) |
        (df["Salmonella"] > THRESHOLDS["Salmonella"]["yellow"]) |
        (df["Turbidity_NTU"] > THRESHOLDS["Turbidity_NTU"]["yellow"]) |
        (df["Antibiotic_Residues_ng_L"] > THRESHOLDS["Antibiotic_Residues_ng_L"]["yellow"])
    )
    df["Alert_Level"] = np.select([red, yellow], ["Red", "Yellow"], default="Green")

    def calc_health_score(row):
        score = 100
        if row["Alert_Level"] == "Red":
            score -= 40
        elif row["Alert_Level"] == "Yellow":
            score -= 15
        if row["Turbidity_NTU"] > 15:
            score -= 5
        return max(0, min(100, int(score)))

    df["Health_Score"] = df.apply(calc_health_score, axis=1)

    def generate_reason(row):
        reasons = []
        if row["SARS_CoV_2_norm"] > THRESHOLDS["SARS_CoV_2_norm"]["yellow"]: reasons.append("SARS-CoV-2")
        if row["Influenza_A_norm"] > THRESHOLDS["Influenza_A_norm"]["yellow"]: reasons.append("Influenza A")
        if row["Norovirus_norm"] > THRESHOLDS["Norovirus_norm"]["yellow"]: reasons.append("Norovirus")
        if row["E_Coli"] > THRESHOLDS["E_Coli"]["yellow"]: reasons.append("E. coli")
        if row["Salmonella"] > THRESHOLDS["Salmonella"]["yellow"]: reasons.append("Salmonella")
        if row["Turbidity_NTU"] > THRESHOLDS["Turbidity_NTU"]["yellow"]: reasons.append("Turbidity")
        if row["Antibiotic_Residues_ng_L"] > THRESHOLDS["Antibiotic_Residues_ng_L"]["yellow"]: reasons.append("Antibiotics")
        if row["pH"] < PH_RED_LOW or row["pH"] > PH_RED_HIGH: reasons.append("pH Anomaly")
        if row["Reported_Clinical_Cases"] > 5: reasons.append("Clinical Cases")
        return " + ".join(reasons) if reasons else "Normal Baseline"

    df["Reason"] = df.apply(generate_reason, axis=1)

    def generate_recommendation(row):
        if row["Alert_Level"] == "Red":
            return "Notify Health Centre, Increase sampling, Inspect sewage line"
        elif row["Alert_Level"] == "Yellow":
            return "Increase sampling frequency, Watch closely"
        return "Routine monitoring"

    df["Recommendation"] = df.apply(generate_recommendation, axis=1)

    df = df.sort_values(["Location_Name", "Date"])
    df["Prev_Score"] = df.groupby("Location_Name")["Health_Score"].shift(1)
    df["Risk_Trend"] = np.where(df["Health_Score"] > df["Prev_Score"] + 5, "↑ Rising Health",
                       np.where(df["Health_Score"] < df["Prev_Score"] - 5, "↓ Falling Health", "→ Stable"))
    df = df.drop(columns=["Prev_Score"])

    df["Confidence_Score"] = df[marker_cols].notna().mean(axis=1) * 100
    df["Confidence_Score"] = df["Confidence_Score"].astype(int).astype(str) + "%"

    round_cols = ["Flow_Rate_kL", "SARS_CoV_2", "Influenza_A", "Norovirus", "E_Coli",
                  "Salmonella", "Campylobacter", "pH", "Turbidity_NTU",
                  "Antibiotic_Residues_ng_L", "SARS_CoV_2_norm", "Influenza_A_norm", "Norovirus_norm"]
    for col in round_cols:
        df[col] = df[col].astype(float).round(2)
        
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    
    cols = ["Date", "day_counter", "Campus", "Node_Category", "Location_Name", "Weather", "Weather_Icon",
            "Flow_Rate_kL", "SARS_CoV_2", "Influenza_A", "Norovirus", "SARS_CoV_2_norm", "Influenza_A_norm", 
            "Norovirus_norm", "E_Coli", "Salmonella", "Campylobacter", "pH", "Turbidity_NTU", 
            "Antibiotic_Residues_ng_L", "Reported_Clinical_Cases", "Alert_Level", "Health_Score", 
            "Reason", "Recommendation", "Risk_Trend", "Confidence_Score"]
    return df[cols]

def build_layout_coords():
    coords = {}
    campus_row_offset = {"NORTH CAMPUS": 0, "SOUTH CAMPUS": 8}
    for campus, offset in campus_row_offset.items():
        for row_i, category in enumerate(CATEGORY_ORDER):
            subset = NODES_DF[(NODES_DF.Campus == campus) & (NODES_DF.Node_Category == category)]
            names = list(subset["Location_Name"])
            k = len(names)
            for i, name in enumerate(names):
                x = (i - (k - 1) / 2.0) * 3
                y = offset - (row_i * 1.5)
                coords[(campus, category, name)] = (x, y)
    return coords

if __name__ == "__main__":
    data = generate_dataset()