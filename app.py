import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="CT Premium Urgent Care Intel", layout="wide")

# ------------------
# Login simples
# ------------------
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "demo123")

if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    st.title("Client Login")
    st.caption("Client-restricted access – Connecticut only")
    pwd = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pwd == APP_PASSWORD:
            st.session_state.authed = True
        else:
            st.error("Wrong password")
    st.markdown("""
    **Notes**
    - Indicative scores  
    - Decision-support only  
    - Aggregated public data (CT)
    """)
    st.stop()

# ------------------
# Dados
# ------------------
df = pd.read_csv("data_mock.csv")

weights = {
    "demographic_fit": 0.22,
    "insurance_alignment": 0.30,
    "health_demand_stability": 0.18,
    "accessibility": 0.20,
    "competition": 0.10,
}

df["competition_inverted"] = 100 - df["competition"]

df["final_score"] = (
    df["demographic_fit"] * weights["demographic_fit"]
    + df["insurance_alignment"] * weights["insurance_alignment"]
    + df["health_demand_stability"] * weights["health_demand_stability"]
    + df["accessibility"] * weights["accessibility"]
    + df["competition_inverted"] * weights["competition"]
).round(0).astype(int)

def recommendation(score):
    if score >= 82:
        return "PROCEED"
    elif score >= 72:
        return "CAUTION"
    else:
        return "AVOID"

df["recommendation"] = df["final_score"].apply(recommendation)

# ------------------
# Sidebar
# ------------------
st.sidebar.title("CT Site Intelligence")
page = st.sidebar.radio("Navigate", ["Home", "Area Detail", "Comparison"])

# ------------------
# HOME
# ------------------
if page == "Home":
    st.title("Connecticut Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Top Areas", len(df))
    c2.metric("Avg Insurance Alignment", int(df["insurance_alignment"].mean()))
    c3.metric("Demand Stability", int(df["health_demand_stability"].mean()))
    c4.metric("Competitive Pressure", int(df["competition"].mean()))

    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        size="final_score",
        color="final_score",
        hover_name="area_name",
        zoom=7.3,
        height=520,
    )
    fig.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Ranked Areas")
    st.dataframe(
        df.sort_values("final_score", ascending=False)[
            ["area_name", "county", "final_score", "recommendation"]
        ],
        use_container_width=True,
    )

# ------------------
# AREA DETAIL
# ------------------
elif page == "Area Detail":
    st.title("Area Detail")
    area = st.selectbox("Select area", df["area_name"])
    row = df[df["area_name"] == area].iloc[0]

    st.subheader(f"{row.area_name} – {row.county} County")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Demographic Fit", row.demographic_fit)
    c2.metric("Insurance Alignment", row.insurance_alignment)
    c3.metric("Health Stability", row.health_demand_stability)
    c4.metric("Accessibility", row.accessibility)
    c5.metric("Competition", row.competition)

    st.divider()
    st.metric("Final Score", row.final_score)
    st.success(f"RECOMMENDATION: {row.recommendation}")

# ------------------
# COMPARISON
# ------------------
else:
    st.title("Comparison")
    picks = st.multiselect(
        "Select areas",
        df["area_name"],
        default=df["area_name"].iloc[:2],
    )

    if len(picks) < 2:
        st.info("Select at least 2 areas")
    else:
        sub = df[df["area_name"].isin(picks)]
        st.dataframe(
            sub[
                ["area_name", "final_score", "insurance_alignment", "accessibility"]
            ].sort_values("final_score", ascending=False),
            use_container_width=True,
        )
