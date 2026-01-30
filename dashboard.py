import streamlit as st
import cloudinary
import cloudinary.api
from datetime import datetime

from datetime import datetime
import pandas as pd
import plotly.express as px


# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="Railway Wildlife Dashboard",
    layout="wide"
)


# -------------------------------
# CLOUDINARY CONFIG
# -------------------------------
try:
    cloudinary.config(
        cloud_name=st.secrets["cloudinary"]["cloud_name"],
        api_key=st.secrets["cloudinary"]["api_key"],
        api_secret=st.secrets["cloudinary"]["api_secret"],
        secure=True
    )

    APP_USERNAME = st.secrets["auth"]["username"]
    APP_PASSWORD = st.secrets["auth"]["password"]

except Exception:
    st.error("Configuration error. Check Streamlit secrets.")
    st.stop()


# -------------------------------
# AUTH
# -------------------------------
def login_view():
    st.markdown("<h2 style='text-align:center'>Railway Wildlife Monitoring System</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center'>Secure Login</h4>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            if username == APP_USERNAME and password == APP_PASSWORD:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Invalid credentials")


if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    login_view()
    st.stop()


with st.sidebar:
    st.success(f"Logged in as {APP_USERNAME}")
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()


# -------------------------------
# CONSTANTS
# -------------------------------
ALLOWED_CLASSES = {
    "elephant": "Elephant",
    "cow": "Cow",
    "deer": "Deer",
    "car": "Car"
}

FOLDER = "railway_wildlife"
MAX_RESULTS = 300


# -------------------------------
# STYLE
# -------------------------------
st.markdown("""
<style>
.card {
    background: #0f172a;
    padding: 12px;
    border-radius: 14px;
    margin-bottom: 10px;
}
.meta {
    font-size: 14px;
    color: #cbd5f5;
}
img {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


# -------------------------------
# LOAD DATA
# -------------------------------
@st.cache_data(ttl=30)
def load_images():
    try:
        result = (
            Search()
            .expression(f"folder:{FOLDER}")
            .sort_by("created_at", "desc")
            .max_results(MAX_RESULTS)
            .execute()
        )
        return result.get("resources", [])
    except Exception as e:
        st.error(f"Cloudinary error: {e}")
        return []


images = load_images()

records = []

for img in images:
    name = img["public_id"].split("/")[-1]
    raw = name.split("_")[0].lower()

    if raw not in ALLOWED_CLASSES:
        continue

    time_obj = datetime.fromisoformat(img["created_at"].replace("Z", ""))

    records.append({
        "animal": ALLOWED_CLASSES[raw],
        "time": time_obj,
        "date": time_obj.date(),
        "url": img["secure_url"]
    })


# -------------------------------
# UI
# -------------------------------
st.title("Railway Wildlife Monitoring Dashboard")
st.caption("Cloud-based detection history")

if not records:
    st.warning("No detections found")
    st.stop()

df = pd.DataFrame(records)

st.subheader("Detection Statistics")

animal_counts = df["animal"].value_counts().reset_index()
animal_counts.columns = ["Animal", "Count"]

fig = px.bar(
    animal_counts,
    x="Animal",
    y="Count",
    text="Count",
    color="Animal"
)

fig.update_traces(textposition="outside")
fig.update_layout(showlegend=False)

st.plotly_chart(fig, use_container_width=True)


# -------------------------------
# FILTERS
# -------------------------------
st.divider()
st.subheader("Filters")

c1, c2 = st.columns(2)

with c1:
    selected_animals = st.multiselect(
        "Filter by animal",
        sorted(df["animal"].unique()),
        default=sorted(df["animal"].unique())
    )

with c2:
    selected_dates = st.multiselect(
        "Filter by date",
        sorted(df["date"].unique())
    )


filtered_df = df[df["animal"].isin(selected_animals)]

if selected_dates:
    filtered_df = filtered_df[
        (filtered_df["date"] >= min(selected_dates)) &
        (filtered_df["date"] <= max(selected_dates))
    ]


# -------------------------------
# DISPLAY CARDS
# -------------------------------
st.divider()
st.subheader(f"Detection History ({len(filtered_df)})")

cols = st.columns(3)

for i, row in filtered_df.iterrows():
    with cols[i % 3]:
        st.image(row["url"], use_container_width=True)
        st.markdown(f"""
        <div class="card">
            <div class="meta"><b>Animal:</b> {row['animal']}</div>
            <div class="meta"><b>Date:</b> {row['time'].strftime('%Y-%m-%d')}</div>
            <div class="meta"><b>Time:</b> {row['time'].strftime('%H:%M:%S')}</div>
        </div>
        """, unsafe_allow_html=True)

