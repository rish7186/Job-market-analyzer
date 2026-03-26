import pandas as pd
import streamlit as st
import plotly.express as px
import requests

# -------------------------------
# 🔑 ADD YOUR API KEYS
# -------------------------------
APP_ID = "da319046"
APP_KEY = "083a412f61bf64f1e6eea70c8947bfce"

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="AI Job Market Analyzer", layout="wide")

# -------------------------------
# HEADER
# -------------------------------
st.title("🤖 AI Job Market Analyzer (Live)")
st.write("Real-time job trends, salary insights & skill gap analysis")

# -------------------------------
# FETCH DATA
# -------------------------------
@st.cache_data(ttl=3600)
def fetch_jobs():
    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id={APP_ID}&app_key={APP_KEY}&results_per_page=50"
    response = requests.get(url)
    data = response.json()

    jobs = []
    for job in data.get("results", []):
        jobs.append({
            "Job Title": job.get("title"),
            "Company": job.get("company", {}).get("display_name"),
            "Location": job.get("location", {}).get("display_name"),
            "Salary": job.get("salary_max")
        })

    return pd.DataFrame(jobs)

# -------------------------------
# LOAD DATA
# -------------------------------
df = fetch_jobs()

if df.empty:
    st.error("❌ No data received from API")
    st.stop()

# -------------------------------
# CLEAN DATA
# -------------------------------
df.columns = df.columns.map(str).str.strip()
df["Salary"] = pd.to_numeric(df["Salary"], errors="coerce")

# -------------------------------
# SALARY MESSAGE
# -------------------------------
if df["Salary"].dropna().empty:
    st.warning("⚠️ Salary data is not available in live tracking from API")

# -------------------------------
# 🔎 SEARCH FIRST (IMPORTANT)
# -------------------------------
search = st.text_input("🔍 Search Job Title")

if search:
    filtered_df = df[df["Job Title"].str.contains(search, case=False, na=False)]
else:
    filtered_df = df.copy()

# -------------------------------
# SIDEBAR FILTERS
# -------------------------------
st.sidebar.title("⚙️ Dashboard Controls")

locations = st.sidebar.multiselect(
    "📍 Location",
    df["Location"].dropna().unique(),
    default=df["Location"].dropna().unique()
)

roles = st.sidebar.multiselect(
    "💼 Job Role",
    df["Job Title"].dropna().unique(),
    default=df["Job Title"].dropna().unique()
)

filtered_df = filtered_df[
    (filtered_df["Location"].isin(locations)) &
    (filtered_df["Job Title"].isin(roles))
]

# -------------------------------
# EMPTY DATA HANDLING (NO STOP)
# -------------------------------
if filtered_df.empty:
    st.warning("⚠️ No jobs found. Try different search or filters.")

# -------------------------------
# SKILLS (TEMP)
# -------------------------------
filtered_df["Skills"] = "Python;SQL;Excel"
skills_series = filtered_df["Skills"].str.split(";")
all_skills = skills_series.explode()

# -------------------------------
# SAFE TOP SKILL
# -------------------------------
if not all_skills.empty:
    top_skill = all_skills.value_counts().idxmax()
else:
    top_skill = "N/A"

# -------------------------------
# KPI METRICS
# -------------------------------
col1, col2, col3 = st.columns(3)

avg_salary = filtered_df["Salary"].dropna().mean()
total_jobs = filtered_df.shape[0]

avg_salary_display = f"{avg_salary:.2f} LPA" if pd.notnull(avg_salary) else "Not Available"

col1.metric("💰 Avg Salary", avg_salary_display)
col2.metric("📄 Total Jobs", total_jobs)
col3.metric("🔥 Top Skill", top_skill)

st.markdown("---")

# -------------------------------
# DASHBOARD (SAFE)
# -------------------------------
if not filtered_df.empty:

    col1, col2 = st.columns(2)

    # Skills Chart
    with col1:
        st.subheader("🔥 Top Skills Demand")
        top_skills = all_skills.value_counts().reset_index()
        top_skills.columns = ["Skill", "Count"]
        fig1 = px.bar(top_skills.head(10), x="Skill", y="Count", template="plotly_dark")
        st.plotly_chart(fig1, use_container_width=True)

    # Salary Chart
    with col2:
        st.subheader("💰 Salary Distribution")
        if filtered_df["Salary"].dropna().empty:
            st.warning("No salary data available")
        else:
            fig2 = px.histogram(filtered_df, x="Salary", template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)

    # Roles
    st.subheader("📌 Job Roles Demand")
    role_counts = filtered_df["Job Title"].value_counts().reset_index()
    role_counts.columns = ["Role", "Count"]

    fig3 = px.pie(role_counts.head(10), names="Role", values="Count")
    st.plotly_chart(fig3, use_container_width=True)

    # Companies
    st.subheader("🏢 Top Hiring Companies")
    company_counts = filtered_df["Company"].value_counts().reset_index()
    company_counts.columns = ["Company", "Jobs"]

    fig4 = px.bar(company_counts.head(10), x="Company", y="Jobs", template="plotly_dark")
    st.plotly_chart(fig4, use_container_width=True)

# -------------------------------
# DOWNLOAD
# -------------------------------
csv = filtered_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Download Data",
    data=csv,
    file_name="job_data.csv",
    mime="text/csv"
)

# -------------------------------
# FOOTER
# -------------------------------
st.markdown("---")
st.markdown("Built with ❤️ by Rishabh | Live AI Project 🚀")