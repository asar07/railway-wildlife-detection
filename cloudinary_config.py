import cloudinary
import streamlit as st

cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"]
)

APP_USERNAME = st.secrets["auth"]["username"]
APP_PASSWORD = st.secrets["auth"]["password"]
