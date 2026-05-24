# styles.py

import streamlit as st

def load_css():

    st.markdown("""
    <style>

    .stButton button {
        font-size: 18px !important;
        padding: 0.6rem !important;
    }

    input, .stNumberInput input {
        font-size: 16px !important;
    }

    </style>
    """, unsafe_allow_html=True)
