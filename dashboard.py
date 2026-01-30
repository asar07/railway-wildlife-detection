import streamlit as st
from cloudinary.search import Search
from datetime import datetime
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Railway Wildlife Dashboard",
    layout="wide"
)

try:
    import cloudinary
    cloudinary.config(
        cloud_name=st.secrets["cloudinary"]["cloud_name"],
        api_key=st.secrets["cloudinary"]["api_key"],
        api_secret=st.secrets["cloudinary"]["api_secret"]
    )
    APP_USERNAME = st.secrets["auth"]["username"]
    APP_PASSWORD = st.secrets["auth"]["password"]
except Exception as e:
    st.error("Configuration error. Please contact administrator.")
    st.stop()

def login_view():
    st.markdown("<h2 style='text-align:center'>Railway Wildlife Monitoring System</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center'>Secure Login</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
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
    st.write(f"Logged in as: {APP_USERNAME}")
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

ALLOWED_CLASSES = {
    "elephant": "Elephant",
    "cow": "Cow",
    "deer": "Deer",
    "car": "Car"
}

FOLDER = "railway_wildlife"
MAX_RESULTS = 300

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
    margin: 4px 0;
}
img {
    border-radius: 10px;
    width: 100%;
    height: auto;
}
</style>
""", unsafe_allow_html=True)

st.title("Railway Wildlife Monitoring Dashboard")
st.caption("Cloud-based detection history")

@st.cache_data(ttl=30)
def load_images():
    try:
        return (
            Search()
            .expression(f"folder:{FOLDER}")
            .sort_by("created_at", "desc")
            .max_results(MAX_RESULTS)
            .execute()
            .get("resources", [])
        )
    except Exception as e:
        st.error(f"Error loading images: {str(e)}")
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

if not records:
    st.warning("No detections found")
    st.stop()

st.subheader("Detection Statistics")

df = pd.DataFrame(records)
animal_counts = df['animal'].value_counts().reset_index()
animal_counts.columns = ['Animal', 'Count']

fig = px.bar(
    animal_counts,
    x='Animal',
    y='Count',
    text='Count',
    title="Wildlife Detections by Species",
    color='Animal',
    color_discrete_sequence=px.colors.qualitative.Bold
)

fig.update_traces(textposition='outside')
fig.update_layout(
    showlegend=False,
    height=400,
    xaxis_title="Animal Type",
    yaxis_title="Number of Detections"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Filters")

f1, f2 = st.columns(2)

with f1:
    animals = sorted(set(r["animal"] for r in records))
    selected_animals = st.multiselect(
        "Filter by animal",
        animals,
        default=animals
    )

with f2:
    all_dates = sorted(set(r["date"] for r in records))
    selected_dates = st.multiselect(
        "Filter by date",
        all_dates
    )

filtered = []

for r in records:
    animal_ok = r["animal"] in selected_animals
    
    if not selected_dates:
        date_ok = True
    elif len(selected_dates) == 1:
        date_ok = r["date"] == selected_dates[0]
    else:
        date_ok = min(selected_dates) <= r["date"] <= max(selected_dates)
    
    if animal_ok and date_ok:
        filtered.append(r)

st.divider()
st.subheader(f"Detection History ({len(filtered)})")

cols = st.columns(3)

for i, r in enumerate(filtered):
    with cols[i % 3]:
        st.image(
            r["url"],
            use_container_width=True
        )
        st.markdown(f"""
        <div class="card">
            <div class="meta"><b>Animal:</b> {r['animal']}</div>
            <div class="meta"><b>Date:</b> {r['time'].strftime('%Y-%m-%d')}</div>
            <div class="meta"><b>Time:</b> {r['time'].strftime('%H:%M:%S')}</div>
        </div>
        """, unsafe_allow_html=True)
